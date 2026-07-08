"""Abstract storage interface for the DotDash Recovery Module.

Defines the contract that any persistence back-end must implement.
Concrete implementations (in-memory, file-based, database) will live in
dedicated modules and inherit from :class:`AbstractStorage`.

No business logic is implemented here -- only method signatures.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import RecoveryProfile, RecoverySession


class AbstractStorage(ABC):
    """Contract that every storage back-end must fulfil.

    Methods are grouped into two categories:

    **Profile persistence** -- CRUD operations on :class:`RecoveryProfile`.
    **Session persistence** -- CRUD operations on :class:`RecoverySession`.
    """

    # ── Profile persistence ─────────────────────────────────────────────
    @abstractmethod
    def save_profile(self, profile: RecoveryProfile) -> None:
        """Persist or update *profile*.

        If a profile already exists for ``profile.user_id``, it is
        overwritten.
        """
        ...

    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[RecoveryProfile]:
        """Retrieve the stored profile for *user_id*, or ``None``."""
        ...

    @abstractmethod
    def delete_profile(self, user_id: str) -> None:
        """Remove the stored profile for *user_id* (no-op if absent)."""
        ...

    # ── Session persistence ─────────────────────────────────────────────
    @abstractmethod
    def save_session(self, session: RecoverySession) -> None:
        """Persist or update *session*."""
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[RecoverySession]:
        """Retrieve the stored session by *session_id*, or ``None``."""
        ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """Remove the stored session (no-op if absent)."""
        ...

    @abstractmethod
    def list_sessions_for_user(self, user_id: str) -> List[RecoverySession]:
        """Return all sessions belonging to *user_id*."""
        ...
