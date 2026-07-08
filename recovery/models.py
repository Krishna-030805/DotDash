"""Data models for the DotDash Recovery Module.

Defines the core domain objects for a custom-recovery-question flow:

- ``QuestionType``    -- Enum of supported question kinds.
- ``SessionStatus``   -- Enum tracking a recovery session's lifecycle.
- ``RecoveryQuestion``-- An individual security question with its prompt and type.
- ``RecoveryProfile`` -- A user's stored set of questions + hashed answers.
- ``RecoverySession`` -- Tracks a single recovery attempt in progress.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional

# ── Constants ───────────────────────────────────────────────────────────────
MIN_QUESTIONS: int = 4
"""Minimum number of questions a recovery profile must contain."""

MAX_QUESTIONS: int = 8
"""Maximum number of questions a recovery profile may contain."""

MAX_RECOVERY_ATTEMPTS: int = 3
"""Maximum verification attempts per recovery session before lockout."""

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
"""Compiled pattern for validating SHA-256 hex digest strings."""


# ── Enums ───────────────────────────────────────────────────────────────────
class QuestionType(Enum):
    """Supported question kinds.

    ``TEXT``             -- Free-form textual answer.
    ``NUMERIC``          -- Numeric-only answer (e.g. a year, a PIN).
    ``MULTIPLE_CHOICE``  -- One of a predefined set of options.
    """

    TEXT = auto()
    NUMERIC = auto()
    MULTIPLE_CHOICE = auto()


class SessionStatus(Enum):
    """Lifecycle states of a :class:`RecoverySession`.

    ``ACTIVE``   -- Session created, awaiting answer submission.
    ``VERIFIED`` -- All answers verified successfully.
    ``FAILED``   -- Verification failed (wrong answers or too many attempts).
    ``EXPIRED``  -- Session timed out before completion.
    """

    ACTIVE = auto()
    VERIFIED = auto()
    FAILED = auto()
    EXPIRED = auto()


# ── Data Classes ────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class RecoveryQuestion:
    """An individual security question presented during recovery.

    Attributes
    ----------
    question_id : str
        Unique identifier for this question.
    prompt : str
        The question text shown to the user (e.g. "What is your pet's name?").
    question_type : QuestionType
        The kind of answer expected.
    options : tuple[str, ...] | None
        Predefined choices when ``question_type`` is ``MULTIPLE_CHOICE``;
        ``None`` for other types.
    """

    question_id: str
    prompt: str
    question_type: QuestionType = QuestionType.TEXT
    options: Optional[tuple] = None  # tuple[str, ...] for MC, else None

    def __post_init__(self) -> None:
        if not self.question_id or not self.question_id.strip():
            raise ValueError("question_id must be a non-empty string.")
        if not self.prompt or not self.prompt.strip():
            raise ValueError("prompt must be a non-empty string.")
        if self.question_type is QuestionType.MULTIPLE_CHOICE:
            if not self.options or len(self.options) < 2:
                raise ValueError(
                    "MULTIPLE_CHOICE questions require at least 2 options."
                )
        elif self.options is not None:
            raise ValueError(
                "options must be None for non-MULTIPLE_CHOICE questions."
            )


@dataclass(frozen=True)
class RecoveryProfile:
    """A user's stored recovery profile -- questions paired with hashed answers.

    The profile is created once during recovery-setup and is used later to
    verify a recovery attempt.

    Attributes
    ----------
    user_id : str
        Identifier of the owning user.
    questions : tuple[RecoveryQuestion, ...]
        Ordered sequence of questions (4–8 items).
    answer_hashes : tuple[str, ...]
        SHA-256 hex digests of each normalised answer, positionally matched
        to ``questions``.
    created_at : datetime
        When the profile was created.
    updated_at : datetime | None
        When the profile was last modified (``None`` if never updated).
    """

    user_id: str
    questions: tuple  # tuple[RecoveryQuestion, ...]
    answer_hashes: tuple  # tuple[str, ...]
    created_at: datetime
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id must be a non-empty string.")

        q_count = len(self.questions)
        if not (MIN_QUESTIONS <= q_count <= MAX_QUESTIONS):
            raise ValueError(
                f"A recovery profile must have between {MIN_QUESTIONS} and "
                f"{MAX_QUESTIONS} questions, got {q_count}."
            )

        if len(self.answer_hashes) != q_count:
            raise ValueError(
                f"answer_hashes length ({len(self.answer_hashes)}) must match "
                f"questions length ({q_count})."
            )

        # Validate every hash looks like a 64-char hex digest.
        for idx, h in enumerate(self.answer_hashes):
            if not _SHA256_PATTERN.match(h):
                raise ValueError(
                    f"answer_hashes[{idx}] is not a valid SHA-256 hex digest."
                )


@dataclass
class RecoverySession:
    """Tracks the state of a single recovery attempt.

    Unlike ``RecoveryProfile`` this is *mutable* -- fields such as
    ``status`` and ``attempt_count`` are updated as the user progresses
    through the flow.

    Attributes
    ----------
    session_id : str
        Unique identifier for this recovery session.
    user_id : str
        The user attempting recovery.
    selected_question_ids : tuple[str, ...]
        IDs of the questions randomly selected for this session.
    status : SessionStatus
        Current lifecycle state.
    attempt_count : int
        Number of verification attempts made in this session.
    created_at : datetime
        When the session was started.
    completed_at : datetime | None
        When the session was finalised (success, failure, or expiry).
    """

    session_id: str
    user_id: str
    selected_question_ids: tuple  # tuple[str, ...]
    status: SessionStatus = SessionStatus.ACTIVE
    attempt_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of an answer verification attempt.

    Returned by the verification engine after comparing user-submitted
    answers against the stored profile hashes.

    Attributes
    ----------
    identity_verified : bool
        ``True`` if every submitted answer matched the stored hash.
    session_status : SessionStatus
        The session's status after verification (``VERIFIED``, ``FAILED``,
        or ``ACTIVE`` if retries remain).
    attempt_count : int
        Total number of verification attempts (including this one).
    message : str
        Human-readable outcome description.  Never reveals *which*
        answer was wrong or what the correct answer is.
    """

    identity_verified: bool
    session_status: SessionStatus
    attempt_count: int
    message: str

