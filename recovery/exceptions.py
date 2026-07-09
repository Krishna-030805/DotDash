"""Custom exception types for the DotDash Recovery Module.

All exceptions inherit from :class:`RecoveryError` so callers can catch the
base class for broad error handling.
"""


class RecoveryError(Exception):
    """Base class for all recovery-related errors."""


class InvalidQuestionCountError(RecoveryError):
    """Raised when a profile does not have exactly REQUIRED_QUESTIONS questions."""


class SessionNotFoundError(RecoveryError):
    """Raised when a session_id cannot be resolved to a stored session."""


class InactiveSessionError(RecoveryError):
    """Raised when an operation requires an ACTIVE session but the session
    has a different status (VERIFIED, FAILED, or EXPIRED)."""


class ProfileNotFoundError(RecoveryError):
    """Raised when a user_id has no associated recovery profile."""


class InvalidAnswerError(RecoveryError):
    """Raised when a submitted answer fails validation (empty, wrong type,
    or answer count mismatch)."""


class DuplicateQuestionError(RecoveryError):
    """Raised when a profile contains duplicate questions after normalisation."""


class EmptyQuestionError(RecoveryError):
    """Raised when a question prompt is empty or whitespace-only."""

