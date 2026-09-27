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


class EvidenceValidationError(ValueError):
    """Exception levée en cas de schéma d'évidence invalide ou de provenance manquante."""
    pass


@dataclass(frozen=True)
class Evidence:
    """
    Modèle universel d'évidence pour toute observation collectée.
    Répond strictement aux 11 dimensions requises par l'architecture Money V2,
    enrichie des métadonnées de justification de navigateur et de classification d'email.
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
    browser_usage_reason: Optional[str] = None
    email_classification: Optional[str] = None
    metadata: Dict[str, Union[str, int, float, bool]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source or not str(self.source).strip():
            raise EvidenceValidationError("Le champ 'source' de l'évidence ne peut pas être vide.")
        if not self.source_url or not str(self.source_url).strip():
            raise EvidenceValidationError("Le champ 'source_url' de l'évidence ne peut pas être vide.")
        if not self.provider or not str(self.provider).strip():
            raise EvidenceValidationError("Le champ 'provider' de l'évidence ne peut pas être vide.")
        if not self.observed_at or not str(self.observed_at).strip():
            raise EvidenceValidationError("Le champ 'observed_at' est obligatoire et ne peut pas être vide.")
        
        # Validation stricte du format ISO 8601 complet (avec date et heure)
        raw_iso = str(self.observed_at).strip()
        if "T" not in raw_iso:
            raise EvidenceValidationError(
                f"Le champ 'observed_at' ({raw_iso}) doit contenir un horodatage ISO 8601 complet avec 'T'."
            )
        try:
            datetime.fromisoformat(raw_iso.replace("Z", "+00:00"))
        except Exception as err:
            raise EvidenceValidationError(
                f"Le champ 'observed_at' ({raw_iso}) n'est pas un horodatage ISO 8601 valide : {err}"
            )

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
            "browser_usage_reason": self.browser_usage_reason,
            "email_classification": self.email_classification,
            "metadata": dict(self.metadata)
        }
