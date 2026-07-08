import hashlib
import hmac
import secrets
from typing import Tuple


_HASH_ITERATIONS = 390000
_SALT_BYTES = 16


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(_SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        _HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${_HASH_ITERATIONS}${salt_value}${derived_key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_value, hash_value = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(derived_key, hash_value)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)
