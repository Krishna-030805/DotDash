"""Answer normalisation utilities for the DotDash Recovery Module.

Before hashing, every raw answer passes through :func:`normalize_answer` to
ensure consistent comparisons regardless of casing or whitespace differences.

Normalisation pipeline:
1. Unicode NFKC normalisation (canonical decomposition + compatibility composition).
2. Strip leading / trailing whitespace.
3. Convert to lowercase.
4. Collapse runs of multiple spaces into a single space.
"""

from __future__ import annotations

import re
import unicodedata

# Pre-compiled pattern for collapsing multiple whitespace characters.
_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_answer(raw_answer: str) -> str:
    """Return a canonical form of *raw_answer*.

    Parameters
    ----------
    raw_answer : str
        The user-supplied answer text.

    Returns
    -------
    str
        Normalised answer -- NFKC-normalised, lowercase, trimmed,
        with collapsed spaces.

    Raises
    ------
    ValueError
        If *raw_answer* is empty or contains only whitespace.

    Examples
    --------
    >>> normalize_answer("  My   Pet   Buddy  ")
    'my pet buddy'

    >>> normalize_answer("NEW YORK")
    'new york'
    """
    if not isinstance(raw_answer, str):
        raise TypeError(
            f"raw_answer must be a str, got {type(raw_answer).__name__}."
        )

    # 1. Unicode NFKC normalisation (before anything else).
    nfkc = unicodedata.normalize("NFKC", raw_answer)

    stripped = nfkc.strip()
    if not stripped:
        raise ValueError("Answer must not be empty or whitespace-only.")

    lowered = stripped.lower()
    collapsed = _MULTI_SPACE_RE.sub(" ", lowered)
    return collapsed

