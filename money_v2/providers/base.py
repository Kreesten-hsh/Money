from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from money_v2.contracts.evidence import Evidence, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult, ProviderTelemetry
from money_v2.contracts.provider_status import ProviderError, ProviderStatus


class BaseProvider(ABC):
    """
    Classe de base abstraite pour tous les providers d'enrichissement Money V2.
    Garantit l'encapsulation télémétrique, la gestion rigoureuse des erreurs
    et l'interdiction formelle de masquer une panne en absence de résultat.
    """

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled

    @abstractmethod
    def is_available(self) -> bool:
        """Indique si l'outil ou le service sous-jacent est disponible sur le système."""
        pass

    @abstractmethod
    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        """Logique métier spécifique du provider."""
        pass

    def execute(self, target: str, context: Optional[Dict[str, Any]] = None) -> ProviderResult:
        """
        Point d'entrée universel d'exécution avec mesure télémétrique et capture d'exception.
        """
        ctx = context or {}
        lead_id = str(ctx.get('lead_id') or target)
        started_at = get_current_iso_timestamp()
        t0 = time.perf_counter()

        if not self.enabled:
            finished_at = get_current_iso_timestamp()
            duration_ms = (time.perf_counter() - t0) * 1000.0
            telem = ProviderTelemetry(
                provider=self.name,
                lead_id=lead_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                status=ProviderStatus.AUTH_REQUIRED,
                records_found=0,
                evidence_count=0,
                error_type="ProviderDisabled",
                error_message_safe="Le provider est désactivé par configuration"
            )
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.AUTH_REQUIRED,
                evidences=[],
                telemetry=telem
            )

        if not self.is_available():
            finished_at = get_current_iso_timestamp()
            duration_ms = (time.perf_counter() - t0) * 1000.0
            missing_st = getattr(self, "missing_status", ProviderStatus.TOOL_MISSING)
            telem = ProviderTelemetry(
                provider=self.name,
                lead_id=lead_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                status=missing_st,
                records_found=0,
                evidence_count=0,
                error_type="ToolMissing",
                error_message_safe=f"L'outil ou dépendance de {self.name} est indisponible sur le système"
            )
            return ProviderResult(
                provider=self.name,
                status=missing_st,
                evidences=[],
                telemetry=telem
            )

        try:
            result = self._run(target, ctx)
            finished_at = get_current_iso_timestamp()
            duration_ms = (time.perf_counter() - t0) * 1000.0

            # Attach telemetry if missing
            if not result.telemetry:
                telem = ProviderTelemetry(
                    provider=self.name,
                    lead_id=lead_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    status=result.status,
                    records_found=len(result.evidences),
                    evidence_count=len(result.evidences)
                )
                return ProviderResult(
                    provider=self.name,
                    status=result.status,
                    evidences=result.evidences,
                    telemetry=telem,
                    raw_payload=result.raw_payload
                )
            return result

        except ProviderError as pe:
            finished_at = get_current_iso_timestamp()
            duration_ms = (time.perf_counter() - t0) * 1000.0
            telem = ProviderTelemetry(
                provider=self.name,
                lead_id=lead_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                status=pe.status,
                records_found=0,
                evidence_count=0,
                error_type="ProviderError",
                error_message_safe=pe.message
            )
            return ProviderResult(
                provider=self.name,
                status=pe.status,
                evidences=[],
                telemetry=telem
            )

        except TimeoutError as te:
            finished_at = get_current_iso_timestamp()
            duration_ms = (time.perf_counter() - t0) * 1000.0
            telem = ProviderTelemetry(
                provider=self.name,
                lead_id=lead_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                status=ProviderStatus.TIMEOUT,
                records_found=0,
                evidence_count=0,
                error_type="TimeoutError",
                error_message_safe=str(te)
            )
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.TIMEOUT,
                evidences=[],
                telemetry=telem
            )

        except Exception as e:
            finished_at = get_current_iso_timestamp()
            duration_ms = (time.perf_counter() - t0) * 1000.0
            telem = ProviderTelemetry(
                provider=self.name,
                lead_id=lead_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                status=ProviderStatus.UNKNOWN_ERROR,
                records_found=0,
                evidence_count=0,
                error_type=type(e).__name__,
                error_message_safe=str(e)[:200]
            )
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.UNKNOWN_ERROR,
                evidences=[],
                telemetry=telem
            )
