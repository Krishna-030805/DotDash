# DotDash Recovery Module

A secure, modular, custom-question-based account recovery system for Python applications. 

## Project Overview
The DotDash Recovery Module provides a robust foundation for implementing identity verification when primary authentication (e.g., passwords, OTP) fails or is unavailable. This module acts as the "Stage-1" engine of a two-stage recovery pipeline, strictly handling the lifecycle, validation, and constant-time verification of custom user-defined security questions.

## Purpose
The primary goal is to verify a user's identity securely and deterministically without ever exposing or comparing plaintext data. It defends against timing attacks, brute-force guessing, and normalisation-based evasion.

## Architecture
The module is strictly separated into focused, single-responsibility components adhering to SOLID principles:
- **Models:** Immutable domain dataclasses (`RecoveryProfile`, `RecoveryQuestion`, `VerificationResult`) and Enums (`SessionStatus`).
- **Validators:** Pure functions enforcing business rules (e.g., exact question count, answer presence, duplication prevention).
- **Selector:** Non-deterministic subset selection logic for dynamic challenge generation.
- **Normalisation & Hashing:** Pipeline enforcing Unicode NFKC canonicalisation, case-folding, and whitespace collapsing prior to SHA-256 hashing.
- **Verifier:** A pure, constant-time verification engine that avoids early-exit timing leaks.
- **Storage:** An `AbstractStorage` contract enabling dependency injection for database back-ends (ships with `InMemoryStorage` for testing).
- **Manager:** The high-level `RecoveryManager` orchestrating the flow and mutating state safely.

## Folder Structure
```
recovery/
├── __init__.py              # Public API exports
├── models.py                # Domain dataclasses & constants
├── exceptions.py            # Custom exception hierarchy
├── interface.py             # Factory for creating managers
├── manager.py               # RecoveryManager orchestrator
├── storage.py               # AbstractStorage interface
├── in_memory_storage.py     # Concrete dict-backed storage
├── question_selector.py     # Random question selection logic
├── validators.py            # Profile input validation rules
├── verifier.py              # Pure constant-time verification engine
└── utils/
    ├── __init__.py          
    ├── hashing.py           # SHA-256 and hmac.compare_digest wrappers
    └── normalization.py     # NFKC + whitespace + casing normalization
```

## Public API
The module exports the following components via `recovery.__init__`:
- **Models:** `RecoveryQuestion`, `RecoveryProfile`, `RecoverySession`, `VerificationResult`, `QuestionType`, `SessionStatus`
- **Constants:** `REQUIRED_QUESTIONS` (6), `MAX_RECOVERY_ATTEMPTS` (3)
- **Utilities:** `normalize_answer`, `hash_answer`, `validate_profile_input`, `select_questions`
- **Storage:** `AbstractStorage`, `InMemoryStorage`
- **Factory:** `RecoveryManager`, `create_recovery_manager`

## Security Considerations
- **No Plaintext Comparison:** Answers are rigorously normalised and hashed *before* storage or comparison.
- **Constant-Time Verification:** The engine utilises `hmac.compare_digest` and explicitly iterates over *all* required answers, refusing to break early, mitigating timing attacks.
- **Zero-Knowledge Return Types:** The `VerificationResult` and exception messages never reveal which specific answer failed, preventing progressive guessing.
- **Strict Lockouts:** Sessions lock out automatically after `MAX_RECOVERY_ATTEMPTS` (default: 3).

## Recovery Workflow
1. **Profile Creation:** The user sets up exactly 6 custom recovery questions and answers. The system normalises and hashes the answers, persisting them via the storage interface.
2. **Session Start:** The user requests recovery. The system randomly selects 3 of the 6 stored questions and creates an `ACTIVE` recovery session.
3. **Challenge/Response:** The selected questions (prompts only) are presented to the user.
4. **Verification:** The user submits their answers. The engine verifies them in constant time.
5. **Outcome:**
   - *Correct:* Status -> `VERIFIED`. Identity verified.
   - *Incorrect (Retries remain):* Status -> `ACTIVE`. Attempt count increments.
   - *Incorrect (Max attempts):* Status -> `FAILED`. Session locked.

## Example Usage
```python
from recovery import create_recovery_manager, RecoveryQuestion, QuestionType

# 1. Initialize the manager (uses InMemoryStorage by default)
manager = create_recovery_manager()

# 2. Create a profile with exactly 6 questions
questions = [
    RecoveryQuestion("q1", "What is your pet's name?"),
    RecoveryQuestion("q2", "In what city were you born?"),
    RecoveryQuestion("q3", "What is your favorite book?"),
    RecoveryQuestion("q4", "What was your first car?"),
    RecoveryQuestion("q5", "What is your mother's maiden name?"),
    RecoveryQuestion("q6", "What was the name of your first school?"),
]
manager.create_profile(
    "user_123", questions,
    ["Fido", "London", "Dune", "Honda", "Smith", "Greenwood"],
)

# 3. Start a recovery session (3 questions randomly selected from 6)
session, selected_questions = manager.start_recovery("user_123")
print([q.prompt for q in selected_questions])

# 4. Verify user answers
user_answers = {
    selected_questions[0].question_id: "Fido",
    selected_questions[1].question_id: "London",
    selected_questions[2].question_id: "Dune",
}
result = manager.verify_answers(session.session_id, user_answers)

if result.identity_verified:
    print("User authenticated successfully!")
else:
    print(result.message)
```

## Future Stage-2 Integration Notes
This module is strictly "Stage-1". It verifies identity but *does not* reset passwords or dispatch credentials. 

To implement Stage-2:
1. Provide a concrete database implementation extending `AbstractStorage`.
2. Wrap `RecoveryManager.verify_answers` in your web framework's route.
3. Upon receiving a `VerificationResult` where `identity_verified == True`, your downstream system should issue a temporary JWT, dispatch an OTP, or direct the user to a secure password reset form.
