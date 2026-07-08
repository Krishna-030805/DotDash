"""Profile validation logic for the DotDash Recovery Module.

Each function validates one aspect of a recovery profile's input data.
All validators raise domain-specific exceptions from :mod:`recovery.exceptions`
on failure and return ``None`` on success.

Usage
-----
Call :func:`validate_profile_input` for a single entry-point that runs every
check in sequence.
"""

from __future__ import annotations

from typing import Sequence

from .models import MIN_QUESTIONS, MAX_QUESTIONS, RecoveryQuestion
from .exceptions import (
    DuplicateQuestionError,
    EmptyQuestionError,
    InvalidAnswerError,
    InvalidQuestionCountError,
)


# ── Individual validators ───────────────────────────────────────────────────

def validate_question_count(questions: Sequence[RecoveryQuestion]) -> None:
    """Raise :class:`InvalidQuestionCountError` if the count is out of range.

    Parameters
    ----------
    questions : Sequence[RecoveryQuestion]
        The list of questions to validate.

    Raises
    ------
    InvalidQuestionCountError
        If ``len(questions)`` is less than ``MIN_QUESTIONS`` or greater than
        ``MAX_QUESTIONS``.
    """
    count = len(questions)
    if count < MIN_QUESTIONS:
        raise InvalidQuestionCountError(
            f"At least {MIN_QUESTIONS} questions are required, got {count}."
        )
    if count > MAX_QUESTIONS:
        raise InvalidQuestionCountError(
            f"At most {MAX_QUESTIONS} questions are allowed, got {count}."
        )


def validate_no_empty_questions(questions: Sequence[RecoveryQuestion]) -> None:
    """Raise :class:`EmptyQuestionError` if any question prompt is empty.

    Parameters
    ----------
    questions : Sequence[RecoveryQuestion]
        The list of questions to validate.

    Raises
    ------
    EmptyQuestionError
        If any ``question.prompt`` is empty or whitespace-only after trimming.
    """
    for question in questions:
        if not question.prompt or not question.prompt.strip():
            raise EmptyQuestionError(
                f"Question '{question.question_id}' has an empty prompt."
            )


def validate_no_duplicate_questions(
    questions: Sequence[RecoveryQuestion],
) -> None:
    """Raise :class:`DuplicateQuestionError` if duplicates exist.

    Questions are compared by their *trimmed, lowercased* prompt text so
    that ``"Pet name?"`` and ``"  pet name?  "`` are treated as identical.

    Parameters
    ----------
    questions : Sequence[RecoveryQuestion]
        The list of questions to validate.

    Raises
    ------
    DuplicateQuestionError
        If two or more questions share the same normalised prompt.
    """
    seen: set[str] = set()
    for question in questions:
        normalised_prompt = question.prompt.strip().lower()
        if normalised_prompt in seen:
            raise DuplicateQuestionError(
                f"Duplicate question detected: '{question.prompt.strip()}'."
            )
        seen.add(normalised_prompt)


def validate_no_empty_answers(raw_answers: Sequence[str]) -> None:
    """Raise :class:`InvalidAnswerError` if any answer is empty.

    Parameters
    ----------
    raw_answers : Sequence[str]
        The plain-text answers to validate.

    Raises
    ------
    InvalidAnswerError
        If any answer is empty or whitespace-only after trimming.
    """
    for idx, answer in enumerate(raw_answers):
        if not isinstance(answer, str) or not answer.strip():
            raise InvalidAnswerError(
                f"Answer at index {idx} must be a non-empty string."
            )


def validate_answers_match_questions(
    questions: Sequence[RecoveryQuestion],
    raw_answers: Sequence[str],
) -> None:
    """Raise :class:`InvalidAnswerError` if counts don't match.

    Parameters
    ----------
    questions : Sequence[RecoveryQuestion]
        The list of questions.
    raw_answers : Sequence[str]
        The list of raw answers.

    Raises
    ------
    InvalidAnswerError
        If ``len(raw_answers) != len(questions)``.
    """
    if len(raw_answers) != len(questions):
        raise InvalidAnswerError(
            f"Expected {len(questions)} answers, got {len(raw_answers)}."
        )


# ── Composite validator ─────────────────────────────────────────────────────

def validate_profile_input(
    questions: Sequence[RecoveryQuestion],
    raw_answers: Sequence[str],
) -> None:
    """Run all profile-input validations in sequence.

    This is the single entry-point that the manager should call before
    building a :class:`RecoveryProfile`.

    Parameters
    ----------
    questions : Sequence[RecoveryQuestion]
        The list of questions.
    raw_answers : Sequence[str]
        The plain-text answers.

    Raises
    ------
    InvalidQuestionCountError
        Too few or too many questions.
    EmptyQuestionError
        A question prompt is blank.
    DuplicateQuestionError
        Two questions share the same normalised prompt.
    InvalidAnswerError
        An answer is blank or the answer count doesn't match.
    """
    validate_question_count(questions)
    validate_no_empty_questions(questions)
    validate_no_duplicate_questions(questions)
    validate_answers_match_questions(questions, raw_answers)
    validate_no_empty_answers(raw_answers)
