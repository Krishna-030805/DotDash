"""Core recovery manager for the DotDash Recovery Module.

Orchestrates the custom-recovery-question flow:
- Profile creation (setup questions + hashed answers)
- Profile retrieval and deletion
- Session lifecycle (start -> select -> track)
- Answer verification
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

from .models import (
    MAX_RECOVERY_ATTEMPTS,
    RecoveryProfile,
    RecoveryQuestion,
    RecoverySession,
    SessionStatus,
    VerificationResult,
)
from .storage import AbstractStorage
from .utils.hashing import hash_answer
from .validators import validate_profile_input
from .question_selector import select_questions
from .verifier import verify_session_answers
from .exceptions import (
    ProfileNotFoundError,
    SessionNotFoundError,
    InactiveSessionError,
)


class RecoveryManager:
    """High-level orchestrator for the question-based recovery flow.

    Parameters
    ----------
    storage : AbstractStorage
        Persistence back-end.
    max_attempts : int
        Maximum verification attempts per session before lockout.
    session_ttl_minutes : int
        Minutes before an idle session expires.
    """

    def __init__(
        self,
        storage: AbstractStorage,
        max_attempts: int = MAX_RECOVERY_ATTEMPTS,
        session_ttl_minutes: int = 15,
    ) -> None:
        self._storage = storage
        self._max_attempts = max_attempts
        self._session_ttl_minutes = session_ttl_minutes

    # -- Profile management (implemented) --------------------------------

    def create_profile(
        self,
        user_id: str,
        questions: Sequence[RecoveryQuestion],
        raw_answers: Sequence[str],
    ) -> RecoveryProfile:
        """Create and persist a new recovery profile for *user_id*.

        Validates all inputs, hashes every answer via the existing hashing
        utility, builds a :class:`RecoveryProfile`, and saves it through
        the storage abstraction.

        Parameters
        ----------
        user_id : str
            The user to associate the profile with.
        questions : Sequence[RecoveryQuestion]
            Ordered questions (4-8 items).
        raw_answers : Sequence[str]
            Plain-text answers (will be normalised and hashed).

        Returns
        -------
        RecoveryProfile
            The newly created and persisted profile.

        Raises
        ------
        InvalidQuestionCountError
            If the number of questions is outside the 4-8 range.
        EmptyQuestionError
            If any question prompt is blank.
        DuplicateQuestionError
            If two questions share the same normalised prompt.
        InvalidAnswerError
            If any answer is blank or the answer count doesn't match.
        """
        # 1. Validate all inputs.
        validate_profile_input(questions, raw_answers)

        # 2. Hash every raw answer using the existing utility.
        answer_hashes = tuple(hash_answer(answer) for answer in raw_answers)

        # 3. Build the immutable profile dataclass.
        profile = RecoveryProfile(
            user_id=user_id,
            questions=tuple(questions),
            answer_hashes=answer_hashes,
            created_at=datetime.utcnow(),
        )

        # 4. Persist via the storage abstraction.
        self._storage.save_profile(profile)

        return profile

    def get_profile(self, user_id: str) -> Optional[RecoveryProfile]:
        """Retrieve the recovery profile for *user_id*.

        Returns
        -------
        RecoveryProfile or None
            The stored profile, or ``None`` if no profile exists.
        """
        return self._storage.get_profile(user_id)

    def delete_profile(self, user_id: str) -> None:
        """Delete the recovery profile for *user_id*.

        Raises
        ------
        ProfileNotFoundError
            If no profile exists for the user.
        """
        existing = self._storage.get_profile(user_id)
        if existing is None:
            raise ProfileNotFoundError(
                f"No recovery profile found for user '{user_id}'."
            )
        self._storage.delete_profile(user_id)

    # -- Session lifecycle (implemented) ---------------------------------

    def start_recovery(
        self, user_id: str,
    ) -> Tuple[RecoverySession, List[RecoveryQuestion]]:
        """Begin a new recovery session for *user_id*.

        Loads the stored profile, randomly selects a subset of questions,
        creates a :class:`RecoverySession` with status ``ACTIVE``, persists
        the session, and returns both the session and the selected question
        prompts.

        Parameters
        ----------
        user_id : str
            The user attempting recovery.

        Returns
        -------
        tuple[RecoverySession, list[RecoveryQuestion]]
            A 2-tuple of:
            - The newly created session.
            - The selected questions (**prompts only** -- no hashes are
              exposed).

        Raises
        ------
        ProfileNotFoundError
            If no profile exists for the user.
        """
        # 1. Load the stored profile.
        profile = self._storage.get_profile(user_id)
        if profile is None:
            raise ProfileNotFoundError(
                f"No recovery profile found for user '{user_id}'."
            )

        # 2. Randomly select questions.
        selected = select_questions(profile.questions)

        # 3. Extract selected question IDs.
        selected_ids = tuple(q.question_id for q in selected)

        # 4. Build the session.
        session = RecoverySession(
            session_id=uuid.uuid4().hex,
            user_id=user_id,
            selected_question_ids=selected_ids,
            status=SessionStatus.ACTIVE,
            attempt_count=0,
            created_at=datetime.utcnow(),
        )

        # 5. Persist the session.
        self._storage.save_session(session)

        return session, selected

    def get_session(self, session_id: str) -> Optional[RecoverySession]:
        """Retrieve a session by its ID, or ``None``.

        Parameters
        ----------
        session_id : str
            The unique session identifier.

        Returns
        -------
        RecoverySession or None
            The stored session, or ``None`` if not found.
        """
        return self._storage.get_session(session_id)

    def cancel_session(self, session_id: str) -> None:
        """Cancel (delete) an active recovery session.

        Parameters
        ----------
        session_id : str
            The unique session identifier.

        Raises
        ------
        SessionNotFoundError
            If no session exists with the given ID.
        """
        existing = self._storage.get_session(session_id)
        if existing is None:
            raise SessionNotFoundError(
                f"No recovery session found with ID '{session_id}'."
            )
        self._storage.delete_session(session_id)

    # -- Verification (implemented) --------------------------------------

    def verify_answers(
        self,
        session_id: str,
        user_answers: Dict[str, str],
    ) -> VerificationResult:
        """Verify submitted answers against the stored profile.

        Loads the session and profile, delegates to the verification
        engine, then updates and persists the session state.

        Parameters
        ----------
        session_id : str
            The active session identifier.
        user_answers : dict[str, str]
            Mapping of ``question_id`` to raw answer text.

        Returns
        -------
        VerificationResult
            The outcome of the verification attempt.

        Raises
        ------
        SessionNotFoundError
            If no session exists with the given ID.
        InactiveSessionError
            If the session is not in ``ACTIVE`` status.
        ProfileNotFoundError
            If the user's recovery profile is missing.
        InvalidAnswerError
            If the answer count doesn't match the selected questions.
        """
        # 1. Load the session.
        session = self._storage.get_session(session_id)
        if session is None:
            raise SessionNotFoundError(
                f"No recovery session found with ID '{session_id}'."
            )

        # 2. Ensure the session is ACTIVE.
        if session.status != SessionStatus.ACTIVE:
            raise InactiveSessionError(
                f"Session '{session_id}' is not active "
                f"(current status: {session.status.name})."
            )

        # 3. Load the user's profile.
        profile = self._storage.get_profile(session.user_id)
        if profile is None:
            raise ProfileNotFoundError(
                f"No recovery profile found for user '{session.user_id}'."
            )

        # 4. Delegate to the pure verification engine.
        result = verify_session_answers(
            session, profile, user_answers, self._max_attempts,
        )

        # 5. Update session state.
        session.status = result.session_status
        session.attempt_count = result.attempt_count
        if result.session_status in (
            SessionStatus.VERIFIED,
            SessionStatus.FAILED,
        ):
            session.completed_at = datetime.utcnow()

        # 6. Persist updated session.
        self._storage.save_session(session)

        return result
