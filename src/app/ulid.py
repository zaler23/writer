from __future__ import annotations

import secrets
import time

_CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_base32(value: int, length: int) -> str:
    chars = ["0"] * length
    for idx in range(length - 1, -1, -1):
        value, rem = divmod(value, 32)
        chars[idx] = _CROCKFORD_BASE32[rem]
    return "".join(chars)


def new_ulid(prefix: str | None = None) -> str:
    # ULID = 48-bit timestamp(ms) + 80-bit randomness => 26 Crockford chars.
    timestamp_ms = int(time.time() * 1000)
    random_bits = secrets.randbits(80)
    value = (timestamp_ms << 80) | random_bits
    raw = _encode_base32(value, 26)
    return f"{prefix}_{raw}" if prefix else raw

