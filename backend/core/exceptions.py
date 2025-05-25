from typing import Any, Dict, Optional


class OpinionFlowException(Exception):
    """Base exception for OpinionFlow"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ExtractionError(OpinionFlowException):
    """Failed to extract product information"""

    def __init__(self, store: str, url: str, reason: str):
        super().__init__(
            message=f"Failed to extract product from {store}",
            status_code=422,
            details={"store": store, "url": url, "reason": reason}
        )


class StoreNotSupportedError(OpinionFlowException):
    """Store not supported"""

    def __init__(self, store: str):
        super().__init__(
            message=f"Store {store} not supported",
            status_code=400,
            details={"store": store}
        )


class RateLimitExceeded(OpinionFlowException):
    """Rate limit exceeded"""

    def __init__(self, wait_time: int):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            details={"wait_seconds": wait_time}
        )
