from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union


def get_current_iso_timestamp() -> str:
    """Génère dynamiquement un horodatage ISO 8601 UTC strict."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class ConfidenceLevel(str, Enum):
    """Niveaux de confiance déterministes sur une observation."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    PATTERN = "PATTERN"  # Pour schémas ou heuristiques sans vérification directe


class ObservationMethod(str, Enum):
    """Méthode d'observation mise en œuvre par le provider."""
    HTTP_GET = "HTTP_GET"
    DOM_INSPECTION = "DOM_INSPECTION"
    DNS_QUERY = "DNS_QUERY"
    OSINT_CLI = "OSINT_CLI"
    REGISTRY_API = "REGISTRY_API"
    BROWSER_AUTOMATION = "BROWSER_AUTOMATION"
    BATCH_CRAWL = "BATCH_CRAWL"


@dataclass(frozen=True)
class Evidence:
    """
    Modèle universel d'évidence pour toute observation collectée.
    Répond strictement aux 11 dimensions requises par l'architecture Money V2.
    """
    field: str
    value: Union[str, bool, int, float, None]
    source: str
    source_url: str
    observed_at: str
    method: str
    provider: str
    provider_status: str
    evidence_text: str
    confidence: str
    lead_id: str
    metadata: Dict[str, Union[str, int, float, bool]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "source": self.source,
            "source_url": self.source_url,
            "observed_at": self.observed_at,
            "method": self.method,
            "provider": self.provider,
            "provider_status": self.provider_status,
            "evidence_text": self.evidence_text,
            "confidence": self.confidence,
            "lead_id": self.lead_id,
            "metadata": dict(self.metadata)
        }
