import logging
import uuid
import json
from typing import List

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, Message, Role, Part, UnsupportedOperationError
from a2a.utils.errors import ServerError

from google.adk.runners import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from circana_pilot_agent.executor import parse_response_to_parts, new_agent_parts_message

logger = logging.getLogger(__name__)

class BaseSubAgentExecutor(AgentExecutor):
    def __init__(self, agent_instance, app_name: str):
        self.agent_instance = agent_instance
        self.app_name = app_name
        self.agent = None
        self.runner = None

    def _init_agent(self):
        if self.agent is None:
            self.agent = self.agent_instance
            self.runner = Runner(
                app_name=self.app_name,
                agent=self.agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )
            logger.info(f"Initialized runner for {self.app_name}")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        self._init_agent()

        from a2a.contrib.tasks.vertex_task_converter import to_stored_part
        runner_parts = []

        if context.message and context.message.parts:
            for part in context.message.parts:
                try:
                    runner_parts.append(to_stored_part(part))
                except Exception as e:
                    logger.warning(f"Failed to convert part: {e}")

        if not runner_parts:
            query = context.get_user_input()
            runner_parts.append(types.Part(text=query))

        logger.info(f"{self.app_name} executor executing query with {len(runner_parts)} parts")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()
        await updater.start_work()

        try:
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name,
                user_id='user',
                session_id=context.context_id,
            )
            if session is None:
                session = await self.runner.session_service.create_session(
                    app_name=self.runner.app_name,
                    user_id='user',
                    state={},
                    session_id=context.context_id,
                )

            content = types.Content(role='user', parts=runner_parts)

            print(f"[{self.app_name}] Starting run_async with session {session.id}", flush=True)
            event_count = 0
            has_final = False
            async for event in self.runner.run_async(
                session_id=session.id,
                user_id='user',
                new_message=content
            ):
                event_count += 1
                print(f"[{self.app_name}] Yielded event #{event_count}: type={type(event)}, content={event}", flush=True)
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    has_final = True
                    print(f"[{self.app_name}] Found final response event!", flush=True)
                    answer_text = ""
                    if event.content and event.content.parts:
                        answer_text = "\n".join(
                            [part.text for part in event.content.parts if part.text]
                        )

                    if answer_text:
                        print(f"[{self.app_name}] Final answer text: {answer_text}", flush=True)
                        final_parts = parse_response_to_parts(answer_text)
                        
                        from circana_pilot_agent.tools import _MOCK_STATE
                        active_parts = _MOCK_STATE.get("active_data_parts", [])
                        if active_parts:
                            from circana_pilot_agent.executor import _create_a2ui_part
                            for ap in active_parts:
                                final_parts.append(_create_a2ui_part(ap))
                            _MOCK_STATE["active_data_parts"] = []

                        await updater.update_status(
                            TaskState.completed,
                            new_agent_parts_message(
                                final_parts,
                                context.context_id,
                                context.task_id,
                            ),
                            final=True,
                        )
                    else:
                        print(f"[{self.app_name}] WARNING: Final event yielded empty content!", flush=True)
                        await updater.update_status(
                            TaskState.completed,
                            new_agent_parts_message(
                                [Part(root=TextPart(text="No response generated."))],
                                context.context_id,
                                context.task_id,
                            ),
                            final=True,
                        )
                    break

            print(f"[{self.app_name}] run_async finished. Total events: {event_count}, has_final: {has_final}", flush=True)
            if not has_final:
                print(f"[{self.app_name}] ERROR: Critical: run_async completed without yielding is_final_response!", flush=True)
                await updater.update_status(
                    TaskState.failed,
                    message=Message(
                        message_id=str(uuid.uuid4()),
                        role=Role.agent,
                        parts=[TextPart(text="Error: Sub-agent execution exited without final response.")]
                    )
                )
        except Exception as e:
            import traceback
            err_msg = f"Executor Exception in {self.app_name}: {str(e)}\nTraceback:\n{traceback.format_exc()}"
            print(f"[{self.app_name}] ERROR: {err_msg}", flush=True)
            await updater.update_status(
                TaskState.completed,
                message=Message(
                    message_id=str(uuid.uuid4()),
                    role=Role.agent,
                    parts=[TextPart(text=err_msg)]
                ),
                final=True
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())


# PricingAssortmentExecutor
from circana_pilot_agent.sub_agents.pricing_assortment_orchestrator import pricing_assortment_orchestrator
class PricingAssortmentExecutor(BaseSubAgentExecutor):
    def __init__(self):
        super().__init__(pricing_assortment_orchestrator, "PricingAssortmentAgent")


# LiquidActivateExecutor
from circana_pilot_agent.sub_agents.liquid_activate_orchestrator import liquid_activate_orchestrator
class LiquidActivateExecutor(BaseSubAgentExecutor):
    def __init__(self):
        super().__init__(liquid_activate_orchestrator, "LiquidActivateAgent")


# LoyaltyCampaignExecutor
from circana_pilot_agent.sub_agents.loyalty_campaign_orchestrator import loyalty_campaign_orchestrator
class LoyaltyCampaignExecutor(BaseSubAgentExecutor):
    def __init__(self):
        super().__init__(loyalty_campaign_orchestrator, "LoyaltyCampaignAgent")

# AudienceProfileExecutor
from circana_pilot_agent.sub_agents.profile_agent import profile_agent
class AudienceProfileExecutor(BaseSubAgentExecutor):
    def __init__(self):
        super().__init__(profile_agent, "AudienceProfileAgent")
