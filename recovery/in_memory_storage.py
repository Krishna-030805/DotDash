"""In-memory storage back-end for the DotDash Recovery Module.

Implements :class:`AbstractStorage` using plain dictionaries.  Suitable for
testing and development -- data does not survive process restarts.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import RecoveryProfile, RecoverySession
from .storage import AbstractStorage


class InMemoryStorage(AbstractStorage):
    """Dictionary-backed storage implementation.

    Profiles are keyed by ``user_id``.
    Sessions are keyed by ``session_id``.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, RecoveryProfile] = {}
        self._sessions: Dict[str, RecoverySession] = {}

    # ── Profile persistence ─────────────────────────────────────────────
    def save_profile(self, profile: RecoveryProfile) -> None:
        """Store *profile*, overwriting any existing entry for the user."""
        self._profiles[profile.user_id] = profile

    def get_profile(self, user_id: str) -> Optional[RecoveryProfile]:
        """Return the stored profile or ``None``."""
        return self._profiles.get(user_id)

    def delete_profile(self, user_id: str) -> None:
        """Remove the profile for *user_id* (no-op if absent)."""
        self._profiles.pop(user_id, None)

    # ── Session persistence ─────────────────────────────────────────────
    def save_session(self, session: RecoverySession) -> None:
        """Store *session*, overwriting any existing entry."""
        self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[RecoverySession]:
        """Return the stored session or ``None``."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        """Remove the session (no-op if absent)."""
        self._sessions.pop(session_id, None)

    def list_sessions_for_user(self, user_id: str) -> List[RecoverySession]:
        """Return all sessions belonging to *user_id*."""
        return [
            session
            for session in self._sessions.values()
            if session.user_id == user_id
        ]
