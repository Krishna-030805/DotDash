"""Public API entry point for the DotDash Recovery Module.

Provides a factory function to create a :class:`RecoveryManager`
instance with an optional custom storage back-end.
"""

from __future__ import annotations

from typing import Optional

from .models import MAX_RECOVERY_ATTEMPTS
from .manager import RecoveryManager
from .storage import AbstractStorage
from .in_memory_storage import InMemoryStorage


def create_recovery_manager(
    storage: Optional[AbstractStorage] = None,
    max_attempts: int = MAX_RECOVERY_ATTEMPTS,
    session_ttl_minutes: int = 15,
) -> RecoveryManager:
    """Factory that returns a configured :class:`RecoveryManager`.

    Parameters
    ----------
    storage : AbstractStorage, optional
        Custom storage back-end.  When ``None`` an :class:`InMemoryStorage`
        instance is used (suitable for testing and development).
    max_attempts : int
        Maximum verification attempts per session.
    session_ttl_minutes : int
        Minutes before an idle session expires.
    """
    if storage is None:
        storage = InMemoryStorage()

    return RecoveryManager(
        storage=storage,
        max_attempts=max_attempts,
        session_ttl_minutes=session_ttl_minutes,
    )

