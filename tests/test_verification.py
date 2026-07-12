"""Unit tests for the Answer Verification Engine.

Tests cover:
 1. Correct answers -> VERIFIED
 2. First failed attempt -> ACTIVE (retry available)
 3. Second failed attempt -> ACTIVE (retry available)
 4. Third (final) failed attempt -> FAILED (lockout)
 5. Successful verification after one failed attempt
 6. Case-insensitive verification (normalisation)
 7. Extra whitespace normalisation
 8. Mixed case + whitespace
 9. Attempt counter increments
10. Session status updates to VERIFIED on success
11. Session status updates to FAILED after max attempts
12. Session completed_at set on VERIFIED
13. Session completed_at set on FAILED (final attempt)
14. Session completed_at NOT set on non-final failure
15. Answer count mismatch raises InvalidAnswerError
16. Session not found raises SessionNotFoundError
17. Verify after VERIFIED session raises InactiveSessionError
18. Verify after FAILED session raises InactiveSessionError
19. VerificationResult never exposes hashes
20. Message never reveals which answer failed
21. One wrong answer fails the entire verification
22. 6-question profile verification (3 selected)
23. Unicode NFKC normalisation (full-width characters)
24. Unicode NFKC normalisation (compatibility equivalence)
"""

from recovery import (
    RecoveryQuestion,
    RecoveryManager,
    SessionStatus,
    VerificationResult,
    MAX_RECOVERY_ATTEMPTS,
    create_recovery_manager,
)
from recovery.exceptions import (
    SessionNotFoundError,
    InactiveSessionError,
    InvalidAnswerError,
)


# -- Helpers -----------------------------------------------------------------

def _make_questions(n):
    """Create *n* unique TEXT questions."""
    return [
        RecoveryQuestion(
            question_id=f"q{i}",
            prompt=f"What is answer number {i}?",
        )
        for i in range(1, n + 1)
    ]


def _make_answers(n):
    """Create *n* unique plain-text answers."""
    return [f"answer {i}" for i in range(1, n + 1)]


def _setup_and_start(mgr, user_id, n_questions=6):
    """Create a profile and start a recovery session.

    Returns (session, selected_questions, profile).
    """
    qs = _make_questions(n_questions)
    ans = _make_answers(n_questions)
    profile = mgr.create_profile(user_id, qs, ans)
    session, selected = mgr.start_recovery(user_id)
    return session, selected, profile


def _build_correct_answers(selected_questions):
    """Build the correct answer dict for *selected_questions*.

    Our test answers follow the pattern 'answer {i}' where i is extracted
    from question_id 'q{i}'.
    """
    answers = {}
    for q in selected_questions:
        idx = q.question_id[1:]  # strip the 'q'
        answers[q.question_id] = f"answer {idx}"
    return answers


def _build_wrong_answers(selected_questions):
    """Build an all-wrong answer dict for *selected_questions*."""
    return {q.question_id: "totally wrong" for q in selected_questions}


# -- Core verification tests -------------------------------------------------

def test_correct_answers_verified():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_ok")

    answers = _build_correct_answers(selected)
    result = mgr.verify_answers(session.session_id, answers)

    assert result.identity_verified is True
    assert result.session_status == SessionStatus.VERIFIED
    assert result.attempt_count == 1
    print("[PASS] Correct answers -> VERIFIED")


def test_first_failed_attempt_stays_active():
    """First wrong attempt: session stays ACTIVE, retries available."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_f1")

    wrong = _build_wrong_answers(selected)
    result = mgr.verify_answers(session.session_id, wrong)

    assert result.identity_verified is False
    assert result.session_status == SessionStatus.ACTIVE
    assert result.attempt_count == 1
    assert "try again" in result.message.lower()

    # Session should still be ACTIVE in storage.
    updated = mgr.get_session(session.session_id)
    assert updated.status == SessionStatus.ACTIVE
    assert updated.attempt_count == 1
    print("[PASS] First failed attempt -> ACTIVE (retry available)")


def test_second_failed_attempt_stays_active():
    """Second wrong attempt: session still ACTIVE."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_f2")

    wrong = _build_wrong_answers(selected)

    # Attempt 1.
    mgr.verify_answers(session.session_id, wrong)
    # Attempt 2.
    result = mgr.verify_answers(session.session_id, wrong)

    assert result.identity_verified is False
    assert result.session_status == SessionStatus.ACTIVE
    assert result.attempt_count == 2
    assert "try again" in result.message.lower()

    updated = mgr.get_session(session.session_id)
    assert updated.status == SessionStatus.ACTIVE
    assert updated.attempt_count == 2
    print("[PASS] Second failed attempt -> ACTIVE (retry available)")


def test_final_failed_attempt_locks_out():
    """Third wrong attempt (MAX_RECOVERY_ATTEMPTS): session -> FAILED."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_f3")

    wrong = _build_wrong_answers(selected)

    # Exhaust all attempts.
    for i in range(MAX_RECOVERY_ATTEMPTS - 1):
        result = mgr.verify_answers(session.session_id, wrong)
        assert result.session_status == SessionStatus.ACTIVE, (
            f"Attempt {i + 1} should keep session ACTIVE"
        )

    # Final attempt.
    result = mgr.verify_answers(session.session_id, wrong)

    assert result.identity_verified is False
    assert result.session_status == SessionStatus.FAILED
    assert result.attempt_count == MAX_RECOVERY_ATTEMPTS
    assert "maximum" in result.message.lower()

    updated = mgr.get_session(session.session_id)
    assert updated.status == SessionStatus.FAILED
    print("[PASS] Final failed attempt -> FAILED (lockout)")


def test_success_after_one_failed_attempt():
    """Correct answers on attempt 2 after failing attempt 1."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_retry")

    wrong = _build_wrong_answers(selected)
    correct = _build_correct_answers(selected)

    # Attempt 1: wrong.
    r1 = mgr.verify_answers(session.session_id, wrong)
    assert r1.identity_verified is False
    assert r1.session_status == SessionStatus.ACTIVE
    assert r1.attempt_count == 1

    # Attempt 2: correct.
    r2 = mgr.verify_answers(session.session_id, correct)
    assert r2.identity_verified is True
    assert r2.session_status == SessionStatus.VERIFIED
    assert r2.attempt_count == 2

    updated = mgr.get_session(session.session_id)
    assert updated.status == SessionStatus.VERIFIED
    assert updated.completed_at is not None
    print("[PASS] Success after one failed attempt")


# -- Normalisation tests -----------------------------------------------------

def test_case_insensitive_verification():
    """'ANSWER 1' should match 'answer 1' after normalisation."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_case")

    answers = {}
    for q in selected:
        idx = q.question_id[1:]
        answers[q.question_id] = f"ANSWER {idx}"

    result = mgr.verify_answers(session.session_id, answers)

    assert result.identity_verified is True
    assert result.session_status == SessionStatus.VERIFIED
    print("[PASS] Case-insensitive verification works")


def test_extra_whitespace_normalisation():
    """'  answer   1  ' should match 'answer 1' after normalisation."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_ws")

    answers = {}
    for q in selected:
        idx = q.question_id[1:]
        answers[q.question_id] = f"  answer   {idx}  "

    result = mgr.verify_answers(session.session_id, answers)

    assert result.identity_verified is True
    assert result.session_status == SessionStatus.VERIFIED
    print("[PASS] Extra whitespace normalisation works")


def test_mixed_case_and_whitespace():
    """'  AnSwEr   1  ' should match 'answer 1'."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_mix")

    answers = {}
    for q in selected:
        idx = q.question_id[1:]
        answers[q.question_id] = f"  AnSwEr   {idx}  "

    result = mgr.verify_answers(session.session_id, answers)

    assert result.identity_verified is True
    print("[PASS] Mixed case + whitespace normalisation works")


def test_unicode_fullwidth_normalisation():
    """Full-width digits/letters should match ASCII after NFKC."""
    mgr = create_recovery_manager()

    # Create profile with ASCII answer "answer 1".
    qs = _make_questions(6)
    mgr.create_profile("user_fw", qs, _make_answers(6))

    session, selected = mgr.start_recovery("user_fw")

    # Build answers using full-width characters where possible.
    # Full-width 'a' = U+FF41, 'n' = U+FF4E, etc.
    # For simplicity, use full-width digits for the number part.
    answers = {}
    for q in selected:
        idx = q.question_id[1:]
        # Replace the digit with its full-width equivalent.
        # Full-width digits start at U+FF10 ('0' = U+FF10, '1' = U+FF11, ...)
        fw_digit = chr(0xFF10 + int(idx))
        answers[q.question_id] = f"answer {fw_digit}"

    result = mgr.verify_answers(session.session_id, answers)

    assert result.identity_verified is True, (
        "Full-width digits should match ASCII after NFKC normalisation"
    )
    print("[PASS] Unicode NFKC normalisation (full-width characters)")


def test_unicode_compatibility_normalisation():
    """NFKC compatibility equivalents should match."""
    from recovery.utils.normalization import normalize_answer

    # The 'fi' ligature (U+FB01) should decompose to 'fi' under NFKC.
    assert normalize_answer("\ufb01rst") == "first"

    # Full-width 'A' (U+FF21) -> 'a' after NFKC + lowercase.
    assert normalize_answer("\uff21nswer") == "answer"

    # Superscript '2' (U+00B2) -> '2' under NFKC.
    assert normalize_answer("\u00b2nd") == "2nd"

    print("[PASS] Unicode NFKC normalisation (compatibility equivalence)")


# -- Counter and status tests ------------------------------------------------

def test_attempt_counter_increments():
    """Verify that attempt_count increases with each verification."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_cnt")

    wrong = _build_wrong_answers(selected)

    # Attempt 1.
    r1 = mgr.verify_answers(session.session_id, wrong)
    assert r1.attempt_count == 1

    # Attempt 2.
    r2 = mgr.verify_answers(session.session_id, wrong)
    assert r2.attempt_count == 2

    updated = mgr.get_session(session.session_id)
    assert updated.attempt_count == 2
    print("[PASS] Attempt counter increments correctly")


def test_session_status_verified():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_sv")

    answers = _build_correct_answers(selected)
    mgr.verify_answers(session.session_id, answers)

    updated = mgr.get_session(session.session_id)
    assert updated.status == SessionStatus.VERIFIED
    print("[PASS] Session status updated to VERIFIED")


def test_session_status_failed_after_max_attempts():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_sf")

    wrong = _build_wrong_answers(selected)
    for _ in range(MAX_RECOVERY_ATTEMPTS):
        mgr.verify_answers(session.session_id, wrong)

    updated = mgr.get_session(session.session_id)
    assert updated.status == SessionStatus.FAILED
    print("[PASS] Session status updated to FAILED after max attempts")


def test_completed_at_set_on_verified():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_cv")
    assert session.completed_at is None

    answers = _build_correct_answers(selected)
    mgr.verify_answers(session.session_id, answers)

    updated = mgr.get_session(session.session_id)
    assert updated.completed_at is not None
    print("[PASS] completed_at is set on VERIFIED")


def test_completed_at_set_on_failed():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_cf")

    wrong = _build_wrong_answers(selected)
    for _ in range(MAX_RECOVERY_ATTEMPTS):
        mgr.verify_answers(session.session_id, wrong)

    updated = mgr.get_session(session.session_id)
    assert updated.completed_at is not None
    print("[PASS] completed_at is set on FAILED (final attempt)")


def test_completed_at_not_set_on_non_final_failure():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_cnf")

    wrong = _build_wrong_answers(selected)
    mgr.verify_answers(session.session_id, wrong)

    updated = mgr.get_session(session.session_id)
    assert updated.completed_at is None
    print("[PASS] completed_at NOT set on non-final failure")


# -- Error handling tests ----------------------------------------------------

def test_answer_count_mismatch():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_acm")

    answers = {selected[0].question_id: "answer 1"}  # only 1 answer

    try:
        mgr.verify_answers(session.session_id, answers)
        assert False, "Should have raised InvalidAnswerError"
    except InvalidAnswerError as e:
        assert "Expected" in str(e)
        print(f"[PASS] Answer count mismatch: {e}")


def test_session_not_found():
    mgr = create_recovery_manager()
    try:
        mgr.verify_answers("ghost_session", {"q1": "a"})
        assert False, "Should have raised"
    except SessionNotFoundError as e:
        print(f"[PASS] Session not found: {e}")


def test_inactive_session_after_verified():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_iav")

    answers = _build_correct_answers(selected)
    mgr.verify_answers(session.session_id, answers)

    try:
        mgr.verify_answers(session.session_id, answers)
        assert False, "Should have raised"
    except InactiveSessionError as e:
        assert "VERIFIED" in str(e)
        print(f"[PASS] Inactive after VERIFIED: {e}")


def test_inactive_session_after_failed():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_iaf")

    wrong = _build_wrong_answers(selected)

    # Exhaust all attempts.
    for _ in range(MAX_RECOVERY_ATTEMPTS):
        mgr.verify_answers(session.session_id, wrong)

    # Now session is FAILED -- any further attempt should raise.
    try:
        correct = _build_correct_answers(selected)
        mgr.verify_answers(session.session_id, correct)
        assert False, "Should have raised"
    except InactiveSessionError as e:
        assert "FAILED" in str(e)
        print(f"[PASS] Inactive after FAILED: {e}")


# -- Security tests ----------------------------------------------------------

def test_result_never_exposes_hashes():
    mgr = create_recovery_manager()
    session, selected, profile = _setup_and_start(mgr, "user_sec")

    answers = _build_correct_answers(selected)
    result = mgr.verify_answers(session.session_id, answers)

    result_str = str(result)
    for h in profile.answer_hashes:
        assert h not in result_str, "Hash leaked in VerificationResult!"

    print("[PASS] VerificationResult never exposes hashes")


def test_message_never_reveals_which_answer_failed():
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_msg")

    wrong = _build_wrong_answers(selected)
    result = mgr.verify_answers(session.session_id, wrong)

    msg = result.message.lower()
    for q in selected:
        assert q.question_id.lower() not in msg, (
            f"Message reveals question ID: {q.question_id}"
        )
    print("[PASS] Message never reveals which answer failed")


def test_one_wrong_answer_fails_all():
    """Even if only one answer is wrong, verification should fail."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_1w")

    answers = _build_correct_answers(selected)
    first_qid = selected[0].question_id
    answers[first_qid] = "definitely wrong"

    result = mgr.verify_answers(session.session_id, answers)
    assert result.identity_verified is False
    # First failure -> ACTIVE (retries remain).
    assert result.session_status == SessionStatus.ACTIVE
    print("[PASS] One wrong answer fails the entire verification")


# -- Profile-size tests ------------------------------------------------------

def test_6_question_profile_verification():
    """Verify with a 6-question profile (3 selected)."""
    mgr = create_recovery_manager()
    session, selected, _ = _setup_and_start(mgr, "user_6q")

    assert len(selected) == 3
    answers = _build_correct_answers(selected)
    result = mgr.verify_answers(session.session_id, answers)

    assert result.identity_verified is True
    assert result.session_status == SessionStatus.VERIFIED
    print("[PASS] 6-question profile verification (3 selected)")


if __name__ == "__main__":
    test_correct_answers_verified()
    test_first_failed_attempt_stays_active()
    test_second_failed_attempt_stays_active()
    test_final_failed_attempt_locks_out()
    test_success_after_one_failed_attempt()
    test_case_insensitive_verification()
    test_extra_whitespace_normalisation()
    test_mixed_case_and_whitespace()
    test_unicode_fullwidth_normalisation()
    test_unicode_compatibility_normalisation()
    test_attempt_counter_increments()
    test_session_status_verified()
    test_session_status_failed_after_max_attempts()
    test_completed_at_set_on_verified()
    test_completed_at_set_on_failed()
    test_completed_at_not_set_on_non_final_failure()
    test_answer_count_mismatch()
    test_session_not_found()
    test_inactive_session_after_verified()
    test_inactive_session_after_failed()
    test_result_never_exposes_hashes()
    test_message_never_reveals_which_answer_failed()
    test_one_wrong_answer_fails_all()
    test_6_question_profile_verification()
    print("\n=== ALL VERIFICATION TESTS PASSED ===")
