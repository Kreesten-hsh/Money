from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from money_v2.contracts.provider_result import ProviderTelemetry
from money_v2.contracts.provider_status import ProviderStatus


class ObservabilityHub:
    """
    Centre d'observabilité télémétrique pour Money V2.
    Trace chaque tentative d'enrichissement et fournit un diagnostic instantané
    sur la cause de non-enrichissement d'un lead sans devoir inspecter 5 scripts.
    """

    def __init__(self, log_path: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.log_path = log_path or (base_dir / "data" / "telemetry_events.json")
        self._events: List[ProviderTelemetry] = []
        self._load_persisted()

    def _load_persisted(self) -> None:
        if not self.log_path.exists():
            return
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
                for item in raw_list:
                    self._events.append(ProviderTelemetry(
                        provider=item["provider"],
                        lead_id=item["lead_id"],
                        started_at=item["started_at"],
                        finished_at=item["finished_at"],
                        duration_ms=float(item["duration_ms"]),
                        status=ProviderStatus(item["status"]),
                        records_found=int(item["records_found"]),
                        evidence_count=int(item["evidence_count"]),
                        error_type=item.get("error_type"),
                        error_message_safe=item.get("error_message_safe")
                    ))
        except Exception:
            pass

    def record(self, telemetry: ProviderTelemetry) -> None:
        """Enregistre un événement télémétrique en mémoire et persiste si configuré."""
        self._events.append(telemetry)

    def explain_lead_enrichment(self, lead_id: str) -> Dict[str, Any]:
        """
        Génère une explication claire et actionnable :
        'Pourquoi ce lead n'a-t-il pas été enrichi ?'
        """
        lead_events = [e for e in self._events if e.lead_id == lead_id]

        if not lead_events:
            return {
                "lead_id": lead_id,
                "diagnosis": "AUCUNE_TENTATIVE",
                "explanation": f"Aucun provider n'a été sollicité pour le lead '{lead_id}'.",
                "recommendation": "Vérifier si le lead a été filtré en amont lors du dédoublonnage ou du matching SIRENE."
            }

        successful_providers = [e.provider for e in lead_events if e.status == ProviderStatus.SUCCESS]
        failed_providers = [
            {
                "provider": e.provider,
                "status": e.status.value,
                "error_type": e.error_type,
                "error_message": e.error_message_safe,
                "duration_ms": e.duration_ms
            }
            for e in lead_events
            if e.status != ProviderStatus.SUCCESS
        ]

        if not failed_providers:
            return {
                "lead_id": lead_id,
                "diagnosis": "ENRICHISSEMENT_COMPLET",
                "explanation": f"Tous les providers sollicités ({', '.join(successful_providers)}) ont réussi.",
                "successful_providers": successful_providers
            }

        # Déterminer la cause principale
        causes: List[str] = []
        for fp in failed_providers:
            st = fp["status"]
            prov = fp["provider"]
            if st == ProviderStatus.TOOL_MISSING.value:
                causes.append(f"L'outil sous-jacent pour '{prov}' est manquant (non installé dans le PATH).")
            elif st == ProviderStatus.BLOCKED.value:
                causes.append(f"Le site a bloqué la requête sur '{prov}' (WAF / HTTP 403 / anti-bot).")
            elif st == ProviderStatus.TIMEOUT.value:
                causes.append(f"Le serveur distant n'a pas répondu dans le délai alloué sur '{prov}'.")
            elif st == ProviderStatus.RATE_LIMITED.value:
                causes.append(f"Le quota de requêtes a été dépassé pour '{prov}'.")
            elif st == ProviderStatus.NO_RESULT.value:
                causes.append(f"Le provider '{prov}' s'est exécuté sans erreur mais aucune donnée n'a été indexée publiquement.")
            else:
                causes.append(f"Erreur d'infrastructure sur '{prov}' : {fp.get('error_message')}")

        return {
            "lead_id": lead_id,
            "diagnosis": "ENRICHISSEMENT_PARTIEL_OU_ECHOUE",
            "successful_providers": successful_providers,
            "failed_attempts": failed_providers,
            "detailed_causes": causes,
            "recommendation": (
                "Vérifier la connectivité réseau, l'installation des outils nécessaires "
                "ou solliciter le palier de repli (Invisible Playwright)."
            )
        }

    def persist(self) -> None:
        """Sauvegarde les événements dans data/telemetry_events.json."""
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            data = [e.to_dict() for e in self._events]
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
