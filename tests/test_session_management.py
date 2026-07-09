"""Unit tests for the Recovery Session Management layer.

Tests cover:
 1. 6-question profile → 3 selected
 2. No duplicate questions in selection
 3. Session stored correctly
 4. Session retrieved correctly
 5. Session deletion (cancel)
 6. Selection varies between sessions
 7. start_recovery raises ProfileNotFoundError for missing user
 8. cancel_session raises SessionNotFoundError for bad ID
 9. Returned questions contain only prompts, never hashes
"""

from recovery import (
    RecoveryQuestion,
    RecoveryManager,
    SessionStatus,
    create_recovery_manager,
)
from recovery.exceptions import ProfileNotFoundError, SessionNotFoundError


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_questions(n: int):
    """Create *n* unique TEXT questions."""
    return [
        RecoveryQuestion(
            question_id=f"q{i}",
            prompt=f"What is answer number {i}?",
        )
        for i in range(1, n + 1)
    ]


def _make_answers(n: int):
    """Create *n* unique plain-text answers."""
    return [f"answer {i}" for i in range(1, n + 1)]


def _setup_profile(mgr: RecoveryManager, user_id: str, n_questions: int = 6):
    """Create and persist a profile with *n_questions* questions."""
    qs = _make_questions(n_questions)
    ans = _make_answers(n_questions)
    return mgr.create_profile(user_id, qs, ans)


# ── Tests ───────────────────────────────────────────────────────────────────

def test_6_questions_selects_3():
    mgr = create_recovery_manager()
    _setup_profile(mgr, "user6")

    session, selected = mgr.start_recovery("user6")
    assert len(selected) == 3, f"Expected 3 selected, got {len(selected)}"
    assert len(session.selected_question_ids) == 3
    print("[PASS] 6-question profile -> 3 selected")


def test_no_duplicate_questions_in_selection():
    mgr = create_recovery_manager()
    _setup_profile(mgr, "user_dup")

    # Run multiple times to check for duplicates.
    for _ in range(20):
        session, selected = mgr.start_recovery("user_dup")
        ids = [q.question_id for q in selected]
        assert len(ids) == len(set(ids)), f"Duplicates found: {ids}"

    print("[PASS] No duplicate questions across 20 selection runs")


def test_session_stored_correctly():
    mgr = create_recovery_manager()
    _setup_profile(mgr, "user_store")

    session, _ = mgr.start_recovery("user_store")

    assert session.session_id, "session_id must be non-empty"
    assert session.user_id == "user_store"
    assert session.status == SessionStatus.ACTIVE
    assert session.attempt_count == 0
    assert session.created_at is not None
    assert session.completed_at is None
    assert len(session.selected_question_ids) == 3
    print("[PASS] Session fields stored correctly")


def test_session_retrieved_correctly():
    mgr = create_recovery_manager()
    _setup_profile(mgr, "user_get")

    session, _ = mgr.start_recovery("user_get")
    retrieved = mgr.get_session(session.session_id)

    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.user_id == session.user_id
    assert retrieved.selected_question_ids == session.selected_question_ids
    assert retrieved.status == SessionStatus.ACTIVE
    print("[PASS] Session retrieved correctly via get_session")


def test_get_session_returns_none_for_missing():
    mgr = create_recovery_manager()
    assert mgr.get_session("nonexistent_id") is None
    print("[PASS] get_session returns None for unknown ID")


def test_cancel_session():
    mgr = create_recovery_manager()
    _setup_profile(mgr, "user_cancel")

    session, _ = mgr.start_recovery("user_cancel")
    sid = session.session_id

    # Cancel the session.
    mgr.cancel_session(sid)

    # Should be gone.
    assert mgr.get_session(sid) is None
    print("[PASS] cancel_session — session deleted")


def test_cancel_nonexistent_session():
    mgr = create_recovery_manager()
    try:
        mgr.cancel_session("ghost_session")
        assert False, "Should have raised SessionNotFoundError"
    except SessionNotFoundError as e:
        print(f"[PASS] cancel non-existent session: {e}")


def test_start_recovery_no_profile():
    mgr = create_recovery_manager()
    try:
        mgr.start_recovery("ghost_user")
        assert False, "Should have raised ProfileNotFoundError"
    except ProfileNotFoundError as e:
        print(f"[PASS] start_recovery with no profile: {e}")


def test_selection_varies_between_sessions():
    """Run start_recovery many times and verify that selections vary."""
    mgr = create_recovery_manager()
    _setup_profile(mgr, "user_vary")

    selections = set()
    for _ in range(30):
        _, selected = mgr.start_recovery("user_vary")
        ids = tuple(sorted(q.question_id for q in selected))
        selections.add(ids)

    # With 6 questions choosing 3, there are C(6,3)=20 combinations.
    # After 30 runs, we should see at least 2 distinct selections.
    assert len(selections) > 1, (
        f"Expected varied selections but only got: {selections}"
    )
    print(f"[PASS] Selection varies — {len(selections)} unique combos in 30 runs")


def test_returned_questions_have_prompts_no_hashes():
    """Ensure the returned selected questions contain prompts but the
    return value itself never exposes answer hashes."""
    mgr = create_recovery_manager()
    _setup_profile(mgr, "user_safe")

    session, selected = mgr.start_recovery("user_safe")

    # Selected questions should have prompts.
    for q in selected:
        assert q.prompt, "Selected question must have a prompt"
        assert q.question_id, "Selected question must have an ID"

    # The session object should NOT carry hashes.
    assert not hasattr(session, "answer_hashes"), (
        "Session must not expose answer_hashes"
    )
    print("[PASS] Returned questions have prompts, no hashes leaked")


if __name__ == "__main__":
    test_6_questions_selects_3()
    test_no_duplicate_questions_in_selection()
    test_session_stored_correctly()
    test_session_retrieved_correctly()
    test_get_session_returns_none_for_missing()
    test_cancel_session()
    test_cancel_nonexistent_session()
    test_start_recovery_no_profile()
    test_selection_varies_between_sessions()
    test_returned_questions_have_prompts_no_hashes()
    print("\n=== ALL SESSION MANAGEMENT TESTS PASSED ===")
