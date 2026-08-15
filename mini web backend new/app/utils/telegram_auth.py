"""
Verifies data sent from a Telegram Mini App frontend.

When your React app opens inside Telegram, Telegram gives it a string called
`initData`. That string contains the user's info (id, name, username) PLUS a
`hash` signed with your bot token. We must recompute that hash on the backend
and compare it — this proves the request really came from Telegram and wasn't
faked by someone calling your API directly.

Official algorithm: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.config import settings


class InvalidInitData(Exception):
    pass


def verify_init_data(init_data: str, max_age_seconds: int = 86400) -> dict:
    """
    Verifies the initData string from the Telegram Web App SDK.
    Returns the parsed Telegram user dict if valid, raises InvalidInitData otherwise.
    """
    if not settings.telegram_bot_token:
        raise InvalidInitData("Server misconfigured: TELEGRAM_BOT_TOKEN not set")

    # initData looks like: "query_id=...&user=...&auth_date=...&hash=..."
    parsed = dict(parse_qsl(init_data, strict_parsing=True))

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InvalidInitData("Missing hash in initData")

    # Build the data-check-string: all fields sorted alphabetically, "key=value" joined by \n
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )

    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.telegram_bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    # computed_hash = HMAC-SHA256(secret_key, data_check_string)
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InvalidInitData("Hash mismatch — data did not come from Telegram")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > max_age_seconds:
        raise InvalidInitData("initData has expired, please reopen the app")

    user_json = parsed.get("user")
    if not user_json:
        raise InvalidInitData("Missing user field in initData")

    return json.loads(user_json)
