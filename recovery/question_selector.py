"""Random question selection for recovery sessions.

Selection rules:
- Profile with exactly 4 questions -> select **2** at random.
- Profile with 5-8 questions       -> select **3** at random.

Uses :mod:`random.sample` which guarantees no duplicates and varies
between calls (non-deterministic by default).
"""

from __future__ import annotations

import random
from typing import List, Sequence

from .models import RecoveryQuestion

# ── Selection thresholds ────────────────────────────────────────────────────
_THRESHOLD_SMALL = 4
"""Profile sizes at or below this value get fewer selected questions."""

_SELECT_COUNT_SMALL = 2
"""How many questions to select for profiles with exactly 4 questions."""

_SELECT_COUNT_LARGE = 3
"""How many questions to select for profiles with 5-8 questions."""


def _determine_selection_count(total_questions: int) -> int:
    """Return how many questions to select based on *total_questions*.

    Parameters
    ----------
    total_questions : int
        The number of questions in the user's recovery profile.

    Returns
    -------
    int
        ``2`` when *total_questions* == 4, otherwise ``3``.
    """
    if total_questions <= _THRESHOLD_SMALL:
        return _SELECT_COUNT_SMALL
    return _SELECT_COUNT_LARGE


def select_questions(
    questions: Sequence[RecoveryQuestion],
) -> List[RecoveryQuestion]:
    """Randomly select a subset of *questions* for a recovery session.

    Parameters
    ----------
    questions : Sequence[RecoveryQuestion]
        All questions from the user's recovery profile (4-8 items).

    Returns
    -------
    list[RecoveryQuestion]
        The randomly selected subset (2 or 3 items).

    Raises
    ------
    ValueError
        If *questions* is empty or has fewer items than the selection count.
    """
    if not questions:
        raise ValueError("Cannot select from an empty question list.")

    count = _determine_selection_count(len(questions))

    if len(questions) < count:
        raise ValueError(
            f"Need at least {count} questions to select from, "
            f"got {len(questions)}."
        )

    return random.sample(list(questions), count)
