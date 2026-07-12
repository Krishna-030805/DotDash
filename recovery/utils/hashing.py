"""SHA-256 hashing utilities for the DotDash Recovery Module.

Answers are always normalised via :func:`normalize_answer` before hashing so
that minor formatting differences (casing, extra spaces) do not cause
verification failures.
"""

from __future__ import annotations

import hashlib
import hmac

from .normalization import normalize_answer


def hash_answer(raw_answer: str) -> str:
    """Normalise *raw_answer* and return its SHA-256 hex digest.

    Parameters
    ----------
    raw_answer : str
        The user-supplied answer text (will be normalised before hashing).

    Returns
    -------
    str
        64-character lowercase hex digest of the SHA-256 hash.

    Raises
    ------
    ValueError
        Propagated from :func:`normalize_answer` if the answer is empty.

    Examples
    --------
    >>> hash_answer("  My   Pet   Buddy  ")  # normalises to "my pet buddy"
    'c2a5e3f4...'  # (truncated for docstring brevity)
    """
    normalised = normalize_answer(raw_answer)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def verify_answer_hash(raw_answer: str, expected_hash: str) -> bool:
    """Check whether *raw_answer* matches *expected_hash* in constant time.

    Uses :func:`hmac.compare_digest` to avoid timing side-channels.

    Parameters
    ----------
    raw_answer : str
        The user-supplied answer text.
    expected_hash : str
        The previously stored SHA-256 hex digest.

    Returns
    -------
    bool
        ``True`` if the hash of the normalised answer matches.
    """
    computed = hash_answer(raw_answer)
    return hmac.compare_digest(computed, expected_hash)
