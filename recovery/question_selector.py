"""Random question selection for recovery sessions.

Always selects exactly **3** questions at random from the user's stored
set of 6 recovery questions.

Uses :mod:`random.sample` which guarantees no duplicates and varies
between calls (non-deterministic by default).
"""

from __future__ import annotations

import random
from typing import List, Sequence

from .models import RecoveryQuestion

# ── Selection constant ──────────────────────────────────────────────────────
QUESTIONS_PER_SESSION: int = 3
"""Number of questions randomly selected for each recovery session."""


def select_questions(
    questions: Sequence[RecoveryQuestion],
) -> List[RecoveryQuestion]:
    """Randomly select a subset of *questions* for a recovery session.

    Parameters
    ----------
    questions : Sequence[RecoveryQuestion]
        All questions from the user's recovery profile (exactly 6 items).

    Returns
    -------
    list[RecoveryQuestion]
        The randomly selected subset (exactly 3 items).

    Raises
    ------
    ValueError
        If *questions* is empty or has fewer items than
        ``QUESTIONS_PER_SESSION``.
    """
    if not questions:
        raise ValueError("Cannot select from an empty question list.")

    if len(questions) < QUESTIONS_PER_SESSION:
        raise ValueError(
            f"Need at least {QUESTIONS_PER_SESSION} questions to select from, "
            f"got {len(questions)}."
        )

    return random.sample(list(questions), QUESTIONS_PER_SESSION)
