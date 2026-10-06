from typing import Any, Optional


class KkhayApiError(Exception):
    """
    Standard API error returned when a K Khay endpoint fails.
    """

    def __init__(
        self,
        status: int,
        message: str,
        code: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(f"KkhayApiError [HTTP {status}]: {message}")
        self.status = status
        self.message = message
        self.code = code
        self.details = details

    def __repr__(self) -> str:
        return f"<KkhayApiError status={self.status} code={self.code!r} message={self.message!r}>"


class SignatureVerificationError(Exception):
    """
    Raised when an incoming IPN webhook payload fails HMAC signature verification.
    """
    pass

