"""Password hashing and stream-key masking helpers."""

from __future__ import annotations

import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """Return a salted SHA-256 hash. Stored format: ``salt$hex``.

    We avoid hard-pinning passlib/bcrypt because some Windows VPS images
    have trouble building bcrypt wheels; this still gives a non-trivial
    hash with a per-row salt.
    """

    salt = os.urandom(16).hex()
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    expected = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, digest)


def mask_stream_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return value[:3] + "*" * (len(value) - 6) + value[-3:]
