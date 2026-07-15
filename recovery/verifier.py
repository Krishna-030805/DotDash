"""Answer verification engine for the DotDash Recovery Module.

Compares user-submitted answers against the stored recovery profile using
SHA-256 hashing and constant-time comparison.

Security guarantees:
- Plaintext answers are never compared directly.
- Constant-time hash comparison via ``hmac.compare_digest``.
- Never reveals which specific answer failed.
- Never exposes stored hashes.
"""

from __future__ import annotations

from typing import Dict, Sequence

from .models import (
    RecoveryProfile,
    RecoverySession,
    SessionStatus,
    VerificationResult,
)
from .utils.hashing import verify_answer_hash
from .exceptions import InvalidAnswerError


def _build_question_hash_map(
    profile: RecoveryProfile,
) -> Dict[str, str]:
    """Build a mapping of ``question_id -> answer_hash`` from *profile*.

    Parameters
    ----------
    profile : RecoveryProfile
        The user's stored recovery profile.

    Returns
    -------
    dict[str, str]
        Mapping from each question's ID to its corresponding SHA-256
        answer hash.
    """
    return {
        question.question_id: answer_hash
        for question, answer_hash in zip(
            profile.questions, profile.answer_hashes
        )
    }


def _validate_answer_count(
    selected_question_ids: Sequence[str],
    user_answers: Dict[str, str],
) -> None:
    """Raise if answer count doesn't match the selected question count.

    Parameters
    ----------
    selected_question_ids : Sequence[str]
        The question IDs selected for this session.
    user_answers : dict[str, str]
        Mapping of ``question_id -> raw_answer`` submitted by the user.

    Raises
    ------
    InvalidAnswerError
        If the number of answers doesn't match the number of selected
        questions.
    """
    expected = len(selected_question_ids)
    received = len(user_answers)
    if received != expected:
        raise InvalidAnswerError(
            f"Expected {expected} answers, got {received}."
        )


def verify_session_answers(
    session: RecoverySession,
    profile: RecoveryProfile,
    user_answers: Dict[str, str],
    max_attempts: int,
) -> VerificationResult:
    """Verify *user_answers* against *profile* for the given *session*.

    This is a **pure function** -- it computes the result but does NOT
    mutate the session or persist anything.  The caller (RecoveryManager)
    is responsible for updating and saving the session.

    Parameters
    ----------
    session : RecoverySession
        The active recovery session (must have status ``ACTIVE``).
    profile : RecoveryProfile
        The user's stored recovery profile.
    user_answers : dict[str, str]
        Mapping of ``question_id -> raw_answer`` for each selected
        question.
    max_attempts : int
        Maximum number of verification attempts before the session
        is locked out.

    Returns
    -------
    VerificationResult
        The outcome of the verification attempt.

    Raises
    ------
    InvalidAnswerError
        If the answer count doesn't match the selected question count.
    """
    # 1. Validate answer count.
    _validate_answer_count(session.selected_question_ids, user_answers)

    # 2. Build question_id -> stored_hash lookup.
    hash_map = _build_question_hash_map(profile)

    # 3. Compare each submitted answer against its stored hash.
    #    We always check ALL answers to prevent timing side-channels
    #    from revealing which specific answer failed.
    all_correct = True
    for question_id in session.selected_question_ids:
        stored_hash = hash_map.get(question_id)
        raw_answer = user_answers.get(question_id, "")

        if stored_hash is None:
            # Question ID not in profile -- treat as mismatch.
            all_correct = False
            continue

        if not raw_answer or not raw_answer.strip():
            all_correct = False
            continue

        if not verify_answer_hash(raw_answer, stored_hash):
            all_correct = False
            # Do NOT break early -- constant-time behaviour.

    # 4. Determine outcome.
    new_attempt_count = session.attempt_count + 1

    if all_correct:
        return VerificationResult(
            identity_verified=True,
            session_status=SessionStatus.VERIFIED,
            attempt_count=new_attempt_count,
            message="Identity verified successfully.",
        )

    # Failed attempt -- check if retries remain.
    if new_attempt_count >= max_attempts:
        return VerificationResult(
            identity_verified=False,
            session_status=SessionStatus.FAILED,
            attempt_count=new_attempt_count,
            message="Maximum recovery attempts exceeded.",
        )

    # Retries still available -- session stays ACTIVE.
    return VerificationResult(
        identity_verified=False,
        session_status=SessionStatus.ACTIVE,
        attempt_count=new_attempt_count,
        message="One or more answers are incorrect. Please try again.",
    )

