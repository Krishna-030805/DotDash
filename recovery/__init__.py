"""DotDash Recovery Module -- custom-question-based account recovery.

Public API
----------
Constants:
    REQUIRED_QUESTIONS, MAX_RECOVERY_ATTEMPTS

Enums:
    QuestionType, SessionStatus

Models:
    RecoveryQuestion, RecoveryProfile, RecoverySession, VerificationResult

Utilities:
    normalize_answer, hash_answer

Validation:
    validate_profile_input

Question Selection:
    select_questions

Storage:
    AbstractStorage, InMemoryStorage

Manager:
    RecoveryManager, create_recovery_manager
"""

from .models import (
    REQUIRED_QUESTIONS,
    MAX_RECOVERY_ATTEMPTS,
    QuestionType,
    SessionStatus,
    RecoveryQuestion,
    RecoveryProfile,
    RecoverySession,
    VerificationResult,
)
from .manager import RecoveryManager
from .interface import create_recovery_manager
from .utils import normalize_answer, hash_answer
from .storage import AbstractStorage
from .in_memory_storage import InMemoryStorage
from .validators import validate_profile_input
from .question_selector import select_questions

__all__ = [
    # Constants
    "REQUIRED_QUESTIONS",
    "MAX_RECOVERY_ATTEMPTS",
    # Enums
    "QuestionType",
    "SessionStatus",
    # Data models
    "RecoveryQuestion",
    "RecoveryProfile",
    "RecoverySession",
    "VerificationResult",
    # Utilities
    "normalize_answer",
    "hash_answer",
    # Validation
    "validate_profile_input",
    # Question selection
    "select_questions",
    # Storage
    "AbstractStorage",
    "InMemoryStorage",
    # Manager
    "RecoveryManager",
    "create_recovery_manager",
]
