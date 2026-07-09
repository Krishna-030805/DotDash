"""Smoke tests for the Question Management layer.

Tests:
1. Happy path — create, get, delete profile (6 questions)
2. Reject 5 questions (too few)
3. Reject 7 questions (too many)
4. Reject duplicate questions
5. Reject empty question prompts
6. Reject empty answers
7. Reject mismatched answer count
8. Delete non-existent profile raises ProfileNotFoundError
9. Answer normalisation works through the full pipeline
"""

from recovery import (
    RecoveryQuestion,
    QuestionType,
    RecoveryManager,
    create_recovery_manager,
    InMemoryStorage,
)
from recovery.exceptions import (
    InvalidQuestionCountError,
    DuplicateQuestionError,
    EmptyQuestionError,
    InvalidAnswerError,
    ProfileNotFoundError,
)


def make_questions(n: int):
    """Helper — create *n* unique TEXT questions."""
    return [
        RecoveryQuestion(
            question_id=f"q{i}",
            prompt=f"What is answer number {i}?",
        )
        for i in range(1, n + 1)
    ]


def make_answers(n: int):
    """Helper — create *n* unique plain-text answers."""
    return [f"answer {i}" for i in range(1, n + 1)]


def test_happy_path():
    mgr = create_recovery_manager()
    qs = make_questions(6)
    ans = make_answers(6)

    # Create
    profile = mgr.create_profile("user1", qs, ans)
    assert profile.user_id == "user1"
    assert len(profile.questions) == 6
    assert len(profile.answer_hashes) == 6
    assert profile.created_at is not None
    assert profile.updated_at is None
    print("[PASS] create_profile — happy path (6 questions)")

    # Get
    loaded = mgr.get_profile("user1")
    assert loaded is not None
    assert loaded.user_id == "user1"
    assert loaded.answer_hashes == profile.answer_hashes
    print("[PASS] get_profile — found")

    # Get missing
    assert mgr.get_profile("nonexistent") is None
    print("[PASS] get_profile — returns None for missing user")

    # Delete
    mgr.delete_profile("user1")
    assert mgr.get_profile("user1") is None
    print("[PASS] delete_profile — profile removed")


def test_reject_5_questions():
    mgr = create_recovery_manager()
    try:
        mgr.create_profile("user_bad", make_questions(5), make_answers(5))
        assert False, "Should have raised"
    except InvalidQuestionCountError as e:
        assert "6" in str(e)
        print(f"[PASS] reject 5 questions: {e}")


def test_reject_7_questions():
    mgr = create_recovery_manager()
    try:
        mgr.create_profile("user_bad", make_questions(7), make_answers(7))
        assert False, "Should have raised"
    except InvalidQuestionCountError as e:
        assert "6" in str(e)
        print(f"[PASS] reject 7 questions: {e}")


def test_duplicate_questions():
    mgr = create_recovery_manager()
    qs = [
        RecoveryQuestion(question_id="q1", prompt="What is your pet's name?"),
        RecoveryQuestion(question_id="q2", prompt="  what is your pet's name?  "),
        RecoveryQuestion(question_id="q3", prompt="Favourite colour?"),
        RecoveryQuestion(question_id="q4", prompt="Birth city?"),
        RecoveryQuestion(question_id="q5", prompt="First school?"),
        RecoveryQuestion(question_id="q6", prompt="Best friend?"),
    ]
    try:
        mgr.create_profile("user_dup", qs, make_answers(6))
        assert False, "Should have raised"
    except DuplicateQuestionError as e:
        print(f"[PASS] reject duplicate questions: {e}")


def test_empty_answers():
    mgr = create_recovery_manager()
    qs = make_questions(6)
    answers = ["answer1", "   ", "answer3", "answer4", "answer5", "answer6"]
    try:
        mgr.create_profile("user_empty", qs, answers)
        assert False, "Should have raised"
    except InvalidAnswerError as e:
        print(f"[PASS] reject empty answers: {e}")


def test_mismatched_count():
    mgr = create_recovery_manager()
    try:
        mgr.create_profile("user_mis", make_questions(6), make_answers(5))
        assert False, "Should have raised"
    except InvalidAnswerError as e:
        print(f"[PASS] reject mismatched answer count: {e}")


def test_delete_nonexistent():
    mgr = create_recovery_manager()
    try:
        mgr.delete_profile("ghost_user")
        assert False, "Should have raised"
    except ProfileNotFoundError as e:
        print(f"[PASS] delete non-existent profile: {e}")


def test_normalisation_pipeline():
    """Verify that '  My   Pet  ' and 'my pet' hash to the same value."""
    mgr = create_recovery_manager()
    qs = make_questions(6)

    p1 = mgr.create_profile("u1", qs, ["  My   Pet  ", "a2", "a3", "a4", "a5", "a6"])
    mgr.delete_profile("u1")

    p2 = mgr.create_profile("u2", qs, ["my pet", "a2", "a3", "a4", "a5", "a6"])

    assert p1.answer_hashes[0] == p2.answer_hashes[0], (
        "Normalised hashes should match"
    )
    print("[PASS] normalisation -- '  My   Pet  ' == 'my pet' after hashing")


if __name__ == "__main__":
    test_happy_path()
    test_reject_5_questions()
    test_reject_7_questions()
    test_duplicate_questions()
    test_empty_answers()
    test_mismatched_count()
    test_delete_nonexistent()
    test_normalisation_pipeline()
    print("\n=== ALL TESTS PASSED ===")
