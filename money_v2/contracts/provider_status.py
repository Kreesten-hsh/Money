from __future__ import annotations

from enum import Enum
from typing import Optional


class ProviderStatus(str, Enum):
    """
    Statut d'exécution normalisé pour tout provider.
    Interdiction absolue d'assimiler une panne technique à un NO_RESULT.
    """
    SUCCESS = "SUCCESS"
    NO_RESULT = "NO_RESULT"
    PARTIAL = "PARTIAL"
    RATE_LIMITED = "RATE_LIMITED"
    BLOCKED = "BLOCKED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    TOOL_MISSING = "TOOL_MISSING"
    INVALID_INPUT = "INVALID_INPUT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

    @property
    def is_technical_failure(self) -> bool:
        """Indique si le statut relève d'une défaillance d'infrastructure."""
        return self in {
            ProviderStatus.RATE_LIMITED,
            ProviderStatus.BLOCKED,
            ProviderStatus.TIMEOUT,
            ProviderStatus.NETWORK_ERROR,
            ProviderStatus.AUTH_REQUIRED,
            ProviderStatus.TOOL_MISSING,
            ProviderStatus.UNKNOWN_ERROR
        }


class ProviderError(Exception):
    """Exception levée ou encapsulée lors d'une défaillance de provider."""
    def __init__(self, message: str, status: ProviderStatus, recoverable: bool = True):
        super().__init__(f"[{status.value}] {message}")
        self.message = message
        self.status = status
        self.recoverable = recoverable
