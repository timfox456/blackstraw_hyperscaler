import logging
import re
import json
import uuid
from typing import List

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, DataPart, UnsupportedOperationError, Message, Role, Part
from a2a.utils.errors import ServerError

try:
    from a2a.utils import new_agent_parts_message
except ImportError:
    def new_agent_parts_message(parts, context_id, task_id):
        return Message(
            message_id=str(uuid.uuid4()),
            role=Role.agent,
            parts=parts,
        )

from google.adk.runners import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# get_agent import moved inside CircanaPilotExecutor._init_agent to avoid unnecessary dependencies in sub-agents

logger = logging.getLogger(__name__)

A2UI_MIME_TYPE = "application/json+a2ui"
A2UI_OPEN_TAG = "<a2ui-json>"
A2UI_CLOSE_TAG = "</a2ui-json>"

_A2UI_BLOCK_RE = re.compile(
    f"{re.escape(A2UI_OPEN_TAG)}(.*?){re.escape(A2UI_CLOSE_TAG)}", re.DOTALL
)

def _sanitize_json(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```json"):
        s = s[len("```json"):]
    elif s.startswith("```"):
        s = s[len("```"):]
    if s.endswith("```"):
        s = s[:-len("```")]

    # Match literalString value block and sanitize its contents
    pattern = re.compile(
        r'("literalString"\s*:\s*")(.*?)("\s*(?:\n|\r\n|\\n)?\s*\}\s*(?:\n|\r\n|\\n)?\s*\})',
        re.DOTALL
    )
    def replacer(match):
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)
        # Escape raw newlines
        content = content.replace('\n', '\\n').replace('\r', '\\r')
        # Escape unescaped double quotes
        content = re.sub(r'(?<!\\)"', r'\"', content)
        return prefix + content + suffix

    s = pattern.sub(replacer, s)
    s = re.sub(r'\\\s*\n', '\n', s)
    return s.strip()

def _create_a2ui_part(data: dict) -> Part:
    return Part(root=DataPart(data=data, metadata={"mimeType": A2UI_MIME_TYPE}))

def parse_response_to_parts(content: str) -> List[Part]:
    matches = list(_A2UI_BLOCK_RE.finditer(content))
    if not matches:
        start_idx = -1
        for marker in ['[{"surfaceId"', '[ {"surfaceId"', '{"surfaceId"']:
            idx = content.find(marker)
            if idx != -1:
                start_idx = idx
                break
        
        if start_idx != -1:
            end_idx = max(content.rfind(']'), content.rfind('}'))
            if end_idx > start_idx:
                json_str = content[start_idx:end_idx+1].strip()
                try:
                    json_str = _sanitize_json(json_str)
                    payload = json.loads(json_str)
                    parts: List[Part] = []
                    text_before = content[:start_idx].strip()
                    if text_before:
                        parts.append(Part(root=TextPart(text=text_before)))
                    if isinstance(payload, list):
                        for item in payload:
                            parts.append(_create_a2ui_part(item))
                    else:
                        parts.append(_create_a2ui_part(payload))
                    text_after = content[end_idx+1:].strip()
                    if text_after:
                        parts.append(Part(root=TextPart(text=text_after)))
                    return parts
                except Exception as parse_ex:
                    logger.warning(f"Fallback balanced JSON extraction failed: {parse_ex}")
        
        clean = content.strip()
        return [Part(root=TextPart(text=clean))] if clean else []
    parts: List[Part] = []
    last_end = 0
    for match in matches:
        start, end = match.span()
        text_before = content[last_end:start].strip()
        if text_before:
            parts.append(Part(root=TextPart(text=text_before)))
        try:
            json_str = _sanitize_json(match.group(1))
            payload = json.loads(json_str)
            if isinstance(payload, list):
                for item in payload:
                    parts.append(_create_a2ui_part(item))
            else:
                parts.append(_create_a2ui_part(payload))
        except Exception as e:
            logger.error(f"Failed to parse A2UI JSON block: {e}")
        last_end = end
    trailing = content[last_end:].strip()
    if trailing:
        parts.append(Part(root=TextPart(text=trailing)))
    return parts

class CircanaPilotExecutor(AgentExecutor):
    def __init__(self):
        self.agent = None
        self.runner = None

    def _init_agent(self):
        if self.agent is None:
            try:
                from .agent import get_agent
            except ImportError:
                from agent import get_agent
            self.agent = get_agent()
            self.runner = Runner(
                app_name="CircanaPilotSupervisor",
                agent=self.agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )
            logger.info("CircanaPilotExecutor initialized runner")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        self._init_agent()

        from a2a.contrib.tasks.vertex_task_converter import to_stored_part
        
        runner_parts = []
        user_input_text = ""

        # Check if the incoming request contains an interactive action payload
        if context.message and context.message.parts:
            for part in context.message.parts:
                # Handle direct actions from WebFrameSrcdoc callbacks
                if isinstance(part.root, DataPart):
                    try:
                        action_data = part.root.data
                        if isinstance(action_data, str):
                            action_data = json.loads(action_data)
                        
                        action_id = action_data.get("actionId")
                        payload = action_data.get("payload", {})
                        
                        if action_id == "product_selected":
                            product = payload.get("product")
                            user_input_text = f'Selected product: "{product}"'
                            logger.info(f"Translated product_selected action to query: {user_input_text}")
                        elif action_id == "btn_activate":
                            partners = ", ".join(payload.get("partners", []))
                            user_input_text = f'Action received: activate the segment on channels: {partners}. Proceed to export.'
                            logger.info(f"Translated btn_activate action to query: {user_input_text}")
                        elif action_id == "btn_launch_campaign":
                            product = payload.get("product")
                            discount = payload.get("discount_pct", "10")
                            multiplier = payload.get("points_mult", "2")
                            user_input_text = f'Action received: launch personalized loyalty rewards campaign for cohort: "{product}" with discount: {discount}% and points multiplier: {multiplier}x.'
                        elif action_id in ("confirm_size", "size_audience"):
                            aud_id = payload.get("audience_id", "AUD-TROPICANA-PURE-PREMIUM-52OZ-999")
                            recap = payload.get("recap", "")
                            user_input_text = f"Yes, size the audience {aud_id} for activation. {recap}".strip()
                            logger.info(f"Translated confirm_size action to query: {user_input_text}")
                        elif action_id in ("request_profile", "profile_audience"):
                            user_input_text = "Compile demographic breakdown and audience profile for this segment."
                            logger.info(f"Translated request_profile action to query: {user_input_text}")
                        elif action_id == "do_activate":
                            user_input_text = "Activate the audience"
                            logger.info(f"Translated do_activate action to query: {user_input_text}")
                        else:
                            user_input_text = f"Execute action: {action_id}"
                            logger.info(f"Fallback translated action {action_id} to query: {user_input_text}")
                    except Exception as action_err:
                        logger.error(f"Error parsing interactive action payload: {action_err}")

                try:
                    stored = to_stored_part(part)
                    if getattr(stored, 'inline_data', None) and stored.inline_data.mime_type == "application/x-a2a-datapart":
                        continue
                    runner_parts.append(stored)
                except Exception as e:
                    logger.warning(f"Failed to convert part: {e}")

        if not user_input_text:
            user_input_text = context.get_user_input()

        if not runner_parts:
            runner_parts = [types.Part(text=user_input_text or "Execute action")]

        # If we translated an action, clear and set the primary text part
        if user_input_text:
            runner_parts = [types.Part(text=user_input_text)]

        logger.info(f"CircanaPilotExecutor executing with user prompt: {user_input_text}")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()
        await updater.start_work()

        # Model Armor inline prompt safety scan
        if user_input_text:
            try:
                try:
                    from .tools import sanitize_content_with_model_armor
                except ImportError:
                    from tools import sanitize_content_with_model_armor
                user_input_text = sanitize_content_with_model_armor(user_input_text)
                runner_parts = [types.Part(text=user_input_text)]
            except ValueError as guard_err:
                logger.warning(f"CircanaPilotExecutor blocked by safety guardrail: {guard_err}")
                await updater.update_status(
                    TaskState.completed,
                    new_agent_parts_message(
                        [Part(root=TextPart(text=f"⚠️ {str(guard_err)}"))],
                        context.context_id,
                        context.task_id
                    ),
                    final=True
                )
                return

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

            async for event in self.runner.run_async(
                session_id=session.id,
                user_id='user',
                new_message=content
            ):
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    logger.info(f"[DEBUG] Final Event: {event}")
                    answer_text = ""
                    if event.content and event.content.parts:
                        answer_text = "\n".join(
                            [part.text for part in event.content.parts if part.text]
                        )

                    try:
                        from .tools import _MOCK_STATE
                    except ImportError:
                        from tools import _MOCK_STATE
                    
                    active_parts = _MOCK_STATE.get("active_data_parts", [])

                    if answer_text or active_parts:
                        final_parts = []
                        if answer_text:
                            try:
                                try:
                                    from .tools import sanitize_content_with_model_armor
                                except ImportError:
                                    from tools import sanitize_content_with_model_armor
                                answer_text = sanitize_content_with_model_armor(answer_text)
                            except Exception as pii_err:
                                logger.error(f"Error sanitizing output: {pii_err}")
                            final_parts = parse_response_to_parts(answer_text)
                        
                        if active_parts:
                            logger.info(f"[CircanaPilotExecutor] Appending {len(active_parts)} cached A2UI data parts directly to final response.")
                            for data_val in active_parts:
                                final_parts.append(_create_a2ui_part(data_val))
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
        except Exception as e:
            logger.error(f"Error in CircanaPilotExecutor: {e}", exc_info=True)
            await updater.update_status(
                TaskState.failed,
                message=Message(
                    message_id=str(uuid.uuid4()),
                    role=Role.agent,
                    parts=[TextPart(text=f"An error occurred: {str(e)}")]
                )
            )
            raise
        finally:
            pass

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())
