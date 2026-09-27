from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import Evidence
from money_v2.contracts.provider_status import ProviderStatus


@dataclass(frozen=True)
class ProviderTelemetry:
    """Télémétrie d'observabilité attachée à chaque exécution de provider."""
    provider: str
    lead_id: str
    started_at: str
    finished_at: str
    duration_ms: float
    status: ProviderStatus
    records_found: int
    evidence_count: int
    error_type: Optional[str] = None
    error_message_safe: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "lead_id": self.lead_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status.value,
            "records_found": self.records_found,
            "evidence_count": self.evidence_count,
            "error_type": self.error_type,
            "error_message_safe": self.error_message_safe
        }


@dataclass(frozen=True)
class ProviderResult:
    """Résultat consolidé retourné par un provider à l'orchestrateur."""
    provider: str
    status: ProviderStatus
    evidences: List[Evidence] = field(default_factory=list)
    telemetry: Optional[ProviderTelemetry] = None
    raw_payload: Optional[Dict[str, Any]] = None

    @property
    def is_success(self) -> bool:
        return self.status in {
            ProviderStatus.SUCCESS,
            ProviderStatus.SUCCESS_WITH_RESULTS,
            ProviderStatus.SUCCESS_EMPTY
        }

    @property
    def has_evidences(self) -> bool:
        return len(self.evidences) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status.value,
            "evidences": [e.to_dict() for e in self.evidences],
            "telemetry": self.telemetry.to_dict() if self.telemetry else None,
            "raw_payload": self.raw_payload
        }
