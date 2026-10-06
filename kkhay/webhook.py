import hashlib
import hmac
import json
import secrets
from typing import Any, Dict, Optional, Union

from .errors import SignatureVerificationError
from .types import KkhayWebhookEvent


def verify_webhook_signature(
    payload: Union[str, bytes, Dict[str, Any]],
    signature: Optional[str] = None,
    ipn_secret: Optional[str] = None,
) -> bool:
    """
    Verifies the cryptographic HMAC-SHA256 signature sent with incoming K Khay IPN webhooks.

    :param payload: The raw request body string, bytes, or parsed dict
    :param signature: The signature header value ('x-kkhay-signature')
    :param ipn_secret: Your merchant IPN Secret Key
    :return: True if valid, False otherwise
    """
    if not signature or not ipn_secret:
        return False

    if isinstance(payload, bytes):
        raw_bytes = payload
    elif isinstance(payload, str):
        raw_bytes = payload.encode("utf-8")
    else:
        raw_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    try:
        secret_bytes = ipn_secret.encode("utf-8")
        computed_hex = hmac.new(secret_bytes, raw_bytes, hashlib.sha256).hexdigest()
        return secrets.compare_digest(computed_hex, signature.strip())
    except Exception:
        return False


def parse_webhook_event(
    raw_body: Union[str, bytes],
    signature: Optional[str],
    ipn_secret: str,
) -> KkhayWebhookEvent:
    """
    Validates and safely parses an incoming K Khay webhook event.
    Raises SignatureVerificationError if signature does not match.

    :param raw_body: The raw request body
    :param signature: The 'x-kkhay-signature' header value
    :param ipn_secret: Your merchant IPN Secret Key
    :return: Typed KkhayWebhookEvent
    """
    if not verify_webhook_signature(raw_body, signature, ipn_secret):
        raise SignatureVerificationError("Invalid K Khay webhook signature: Request rejected.")

    try:
        if isinstance(raw_body, bytes):
            text = raw_body.decode("utf-8")
        else:
            text = raw_body
        data = json.loads(text)
        return KkhayWebhookEvent.from_dict(data)
    except Exception as e:
        if isinstance(e, SignatureVerificationError):
            raise
        raise ValueError(f"Failed to parse webhook JSON payload: {e}") from e
