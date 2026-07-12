"""Utility helpers for the DotDash Recovery Module.

Public API:
- ``normalize_answer``  -- Canonicalise raw answer text.
- ``hash_answer``       -- SHA-256 hash of a normalised answer.
"""

from .normalization import normalize_answer
from .hashing import hash_answer

__all__ = ["normalize_answer", "hash_answer"]
