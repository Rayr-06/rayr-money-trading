"""
Symmetric encryption for sensitive credentials (API keys, secrets).

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the `cryptography` package.
The master key is read from MASTER_ENCRYPTION_KEY env var.

If the env var is missing, a key is auto-generated and persisted to
`.encryption_key` on first run. NEVER commit that file.
"""
from __future__ import annotations
import os
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken


_KEY_FILE = Path(os.getenv("ENCRYPTION_KEY_FILE", ".encryption_key"))


def _load_or_create_key() -> bytes:
    env_key = os.getenv("MASTER_ENCRYPTION_KEY", "").strip()
    if env_key:
        return env_key.encode()
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes().strip()
    # First run — generate and persist
    key = Fernet.generate_key()
    _KEY_FILE.write_bytes(key)
    try:
        os.chmod(_KEY_FILE, 0o600)  # owner read/write only
    except Exception:
        pass
    return key


_FERNET = Fernet(_load_or_create_key())


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns a URL-safe base64 token."""
    if plaintext is None:
        raise ValueError("cannot encrypt None")
    return _FERNET.encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a token previously produced by encrypt()."""
    try:
        return _FERNET.decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError(
            "Decryption failed. The MASTER_ENCRYPTION_KEY likely changed "
            "since the credentials were stored."
        ) from e


def mask(value: str, visible: int = 4) -> str:
    """Display helper — masks all but the last `visible` chars."""
    if not value or len(value) <= visible:
        return "****"
    return "*" * (len(value) - visible) + value[-visible:]
