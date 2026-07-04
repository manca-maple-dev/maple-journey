"""Field-level encryption for sensitive identifiers (IRCC file #, foreign ID).
Key is derived from JWT_SECRET so no extra secret management is needed."""
import base64
import hashlib

from cryptography.fernet import Fernet

from core.config import get_jwt_secret


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(get_jwt_secret().encode()).digest())
    return Fernet(key)


def encrypt(value: str) -> str:
    if not value:
        return ""
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except Exception:
        return ""
