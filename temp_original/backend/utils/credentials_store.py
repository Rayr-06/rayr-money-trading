"""
Encrypted on-disk credentials store. Single JSON file, all values encrypted.
Replace with a real DB in production — interface stays the same.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict
from .encryption import encrypt, decrypt

_STORE_PATH = Path("backend/.credentials.json")


def _read_raw() -> Dict[str, str]:
    if not _STORE_PATH.exists():
        return {}
    try:
        return json.loads(_STORE_PATH.read_text() or "{}")
    except json.JSONDecodeError:
        return {}


def _write_raw(data: Dict[str, str]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(data, indent=2))
    try:
        import os
        os.chmod(_STORE_PATH, 0o600)
    except Exception:
        pass


def save_credentials(namespace: str, **fields: str) -> None:
    """
    Encrypt + persist a set of fields under a namespace (e.g. 'alpaca').
    Non-secret booleans/strings can be passed too — they're stored as-is.
    """
    data = _read_raw()
    bucket: Dict[str, str] = {}
    for k, v in fields.items():
        if v is None:
            continue
        # Encrypt anything that looks like a key/secret/token
        if isinstance(v, str) and any(t in k.lower() for t in ("key", "secret", "token", "password")):
            bucket[k] = encrypt(v)
            bucket[f"_{k}_encrypted"] = "true"
        else:
            bucket[k] = v
    data[namespace] = bucket
    _write_raw(data)


def load_credentials(namespace: str) -> Optional[Dict[str, str]]:
    data = _read_raw()
    bucket = data.get(namespace)
    if not bucket:
        return None
    out: Dict[str, str] = {}
    for k, v in bucket.items():
        if k.startswith("_") and k.endswith("_encrypted"):
            continue
        if bucket.get(f"_{k}_encrypted") == "true":
            try:
                out[k] = decrypt(v)
            except Exception:
                return None
        else:
            out[k] = v
    return out


def delete_credentials(namespace: str) -> bool:
    data = _read_raw()
    if namespace in data:
        del data[namespace]
        _write_raw(data)
        return True
    return False
