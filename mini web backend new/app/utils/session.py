"""
Simple signed session tokens.

After verifying Telegram initData once, we issue our own compact token so the
frontend can just send that on future requests instead of the full initData
every time. It's signed the same way (HMAC) so it can't be forged, and it
carries an expiry.

This avoids pulling in a full JWT library for something this small — same idea
as JWT, simplified.
"""
import base64
import hashlib
import hmac
import json
import time

from app.config import settings


def _signing_key() -> bytes:
    return hashlib.sha256(settings.telegram_bot_token.encode()).digest()


def create_session_token(user_id: int, telegram_id: int) -> str:
    payload = {
        "user_id": user_id,
        "telegram_id": telegram_id,
        "exp": int(time.time()) + settings.session_ttl_hours * 3600,
    }
    payload_bytes = json.dumps(payload).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode().rstrip("=")

    signature = hmac.new(_signing_key(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_session_token(token: str) -> dict:
    try:
        payload_b64, signature = token.split(".")
    except ValueError:
        raise ValueError("Malformed token")

    expected_sig = hmac.new(_signing_key(), payload_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, signature):
        raise ValueError("Invalid token signature")

    padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))

    if payload["exp"] < time.time():
        raise ValueError("Token expired")

    return payload
