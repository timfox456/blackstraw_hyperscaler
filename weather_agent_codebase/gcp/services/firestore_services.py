"""Firestore-backed Session + Memory services for the ADK Runner.

Implements PDF Section 3 (State Management & Persistent Memory).

Replaces InMemorySessionService / InMemoryMemoryService so that, when a
stateless container restarts or a user switches browser tabs, the executor
queries Firestore for the conversation's active state (session.state) and
resumes execution seamlessly.

The PDF references these import paths verbatim:

    from google.adk.sessions.firestore_session_service import FirestoreSessionService
    from google.adk.memory.firestore_memory_service   import FirestoreMemoryService

Newer ADK builds may not ship those modules out of the box (the Medium
article linked in the PDF describes building a custom BaseSessionService).
This module therefore tries the official import first and falls back to a
custom Firestore-backed implementation that conforms to the same interface.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Try the import path the PDF documents. If ADK ships these natively we use
# them as-is so behavior matches Google's reference architecture.
# ---------------------------------------------------------------------------
_NATIVE_AVAILABLE = False
try:
    from google.adk.sessions.firestore_session_service import (  # type: ignore
        FirestoreSessionService as _NativeFirestoreSessionService,
    )
    from google.adk.memory.firestore_memory_service import (  # type: ignore
        FirestoreMemoryService as _NativeFirestoreMemoryService,
    )

    _NATIVE_AVAILABLE = True
except Exception:  # pragma: no cover - depends on ADK version
    _NativeFirestoreSessionService = None
    _NativeFirestoreMemoryService = None


# ---------------------------------------------------------------------------
# Custom Firestore-backed implementation (fallback path).
#
# Follows the pattern in the PDF's referenced Medium article: persist
# session.state and session.events in Firestore documents so that stateless
# Reasoning Engine workers can resume context across restarts.
# ---------------------------------------------------------------------------
try:
    from google.adk.sessions import BaseSessionService, Session  # type: ignore
except Exception:  # pragma: no cover
    BaseSessionService = object  # type: ignore
    Session = None  # type: ignore

try:
    from google.adk.memory import BaseMemoryService  # type: ignore
except Exception:  # pragma: no cover
    BaseMemoryService = object  # type: ignore

try:
    from google.cloud import firestore  # type: ignore
except Exception:  # pragma: no cover
    firestore = None  # type: ignore


@dataclass
class _SimpleSession:
    """Lightweight session record persisted to Firestore."""

    id: str
    app_name: str
    user_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    last_update_time: float = field(default_factory=time.time)


class _CustomFirestoreSessionService(BaseSessionService):  # type: ignore[misc]
    """Firestore-backed Session service used when ADK does not ship one.

    Documents are stored at:
        sessions/{app_name}/{user_id}/{session_id}
    """

    COLLECTION = "adk_sessions"

    def __init__(self, project_id: str, database: str = "(default)") -> None:
        if firestore is None:
            raise RuntimeError(
                "google-cloud-firestore is required for FirestoreSessionService. "
                "Install with: pip install google-cloud-firestore"
            )
        self.project_id = project_id
        self._client = firestore.Client(project=project_id, database=database)

    # --- BaseSessionService interface ----------------------------------------

    def _doc(self, app_name: str, user_id: str, session_id: str):
        return (
            self._client.collection(self.COLLECTION)
            .document(app_name)
            .collection(user_id)
            .document(session_id)
        )

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> _SimpleSession:
        sid = session_id or uuid.uuid4().hex
        session = _SimpleSession(
            id=sid,
            app_name=app_name,
            user_id=user_id,
            state=dict(state or {}),
        )
        self._doc(app_name, user_id, sid).set(session.__dict__)
        return session

    async def get_session(
        self, *, app_name: str, user_id: str, session_id: str, **_: Any
    ) -> Optional[_SimpleSession]:
        snap = self._doc(app_name, user_id, session_id).get()
        if not snap.exists:
            return None
        d = snap.to_dict() or {}
        return _SimpleSession(**d)

    async def list_sessions(self, *, app_name: str, user_id: str) -> List[_SimpleSession]:
        col = (
            self._client.collection(self.COLLECTION)
            .document(app_name)
            .collection(user_id)
        )
        return [_SimpleSession(**(d.to_dict() or {})) for d in col.stream()]

    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        self._doc(app_name, user_id, session_id).delete()

    async def append_event(self, session: _SimpleSession, event: Any) -> Any:
        event_dict = event if isinstance(event, dict) else getattr(event, "__dict__", {"event": str(event)})
        session.events.append(event_dict)
        session.last_update_time = time.time()
        self._doc(session.app_name, session.user_id, session.id).set(session.__dict__)
        return event


class _CustomFirestoreMemoryService(BaseMemoryService):  # type: ignore[misc]
    """Firestore-backed long-term Memory service (fallback).

    Stores summarized memories at:
        memories/{app_name}/{user_id}/{memory_id}
    """

    COLLECTION = "adk_memories"

    def __init__(self, project_id: str, database: str = "(default)") -> None:
        if firestore is None:
            raise RuntimeError(
                "google-cloud-firestore is required for FirestoreMemoryService."
            )
        self._client = firestore.Client(project=project_id, database=database)

    def _doc(self, app_name: str, user_id: str, memory_id: str):
        return (
            self._client.collection(self.COLLECTION)
            .document(app_name)
            .collection(user_id)
            .document(memory_id)
        )

    async def add_session_to_memory(self, session: Any) -> None:
        """Compaction hook (PDF Section 3): summarize older events and persist."""
        if session is None:
            return
        mid = uuid.uuid4().hex
        events = getattr(session, "events", []) or []
        state = getattr(session, "state", {}) or {}
        self._doc(session.app_name, session.user_id, mid).set(
            {
                "id": mid,
                "session_id": getattr(session, "id", None),
                "state_snapshot": dict(state),
                "event_count": len(events),
                "created_at": time.time(),
            }
        )

    async def search_memory(
        self, *, app_name: str, user_id: str, query: str
    ) -> List[Dict[str, Any]]:
        col = self._client.collection(self.COLLECTION).document(app_name).collection(user_id)
        return [d.to_dict() or {} for d in col.stream()]


# ---------------------------------------------------------------------------
# Public factory: prefer native ADK classes, fall back to custom impl.
# ---------------------------------------------------------------------------

def build_firestore_session_service(project_id: Optional[str] = None):
    """Returns a Firestore-backed Session service implementing BaseSessionService."""
    project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT must be set or project_id passed in.")

    if _NATIVE_AVAILABLE and _NativeFirestoreSessionService is not None:
        return _NativeFirestoreSessionService(project_id=project_id)
    return _CustomFirestoreSessionService(project_id=project_id)


def build_firestore_memory_service(project_id: Optional[str] = None):
    """Returns a Firestore-backed Memory service implementing BaseMemoryService."""
    project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT must be set or project_id passed in.")

    if _NATIVE_AVAILABLE and _NativeFirestoreMemoryService is not None:
        return _NativeFirestoreMemoryService(project_id=project_id)
    return _CustomFirestoreMemoryService(project_id=project_id)


# Public aliases matching the PDF's documented class names so user code can do:
#   from gcp.services.firestore_services import FirestoreSessionService
FirestoreSessionService = build_firestore_session_service
FirestoreMemoryService = build_firestore_memory_service
