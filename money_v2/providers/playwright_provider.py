from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class InvisiblePlaywrightProvider(BaseProvider):
    """
    Provider Navigateur Furtif via le vrai serveur MCP invisible-playwright-mcp.

    Rôle architectural :
    - Pilote le serveur MCP `uvx invisible-playwright-mcp` en subprocess via mcp_playwright_client.py.
    - Exécuté de manière isolée avec le SDK officiel MCP (client stdio) sans import direct
      de patchright ou playwright dans les dépendances du projet.
    - Utilisé pour des consultations unitaires strictes sur annuaires / profils professionnels (ADR-008).

    Règles absolues d'étanchéité (Niveau 4 -> Niveau 1/2) :
    - N'écrit JAMAIS dans siren, company_name, legal_status, company_size, company_size_code,
      decision_maker, decision_maker_role, decision_maker_is_person.
    - Débit strictement plafonné à 5 consultations unitaires/jour sur profils validés MATCH_CONFIRMED.
    """

    FORBIDDEN_FIELDS = {
        "siren",
        "company_name",
        "legal_status",
        "company_size",
        "company_size_code",
        "decision_maker",
        "decision_maker_role",
        "decision_maker_is_person",
    }

    def __init__(self, timeout_ms: int = 25000, enabled: bool = True):
        super().__init__(name="invisible_playwright_mcp", enabled=enabled)
        self.timeout_ms = timeout_ms

    def is_available(self) -> bool:
        """Vérifie la présence de uv dans le PATH système pour exécuter le serveur MCP."""
        return shutil.which("uv") is not None

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        url = target.strip()
        lead_id = str(context.get("lead_id") or url)
        trigger_type = str(context.get("trigger_type") or "annuaire_fallback")
        field_target = str(context.get("field_target") or "main_offer")
        matching_status = str(context.get("matching_status") or "")
        daily_count = int(context.get("linkedin_daily_count") or 0)
        now_iso = get_current_iso_timestamp()

        # Contrôle machine de l'interdit de corruption Niveau 1/2
        if field_target in self.FORBIDDEN_FIELDS:
            raise ProviderError(
                f"Violation d'étanchéité : le provider Niveau 4 {self.name} "
                f"ne peut pas alimenter le champ légal réservé '{field_target}'",
                ProviderStatus.INVALID_INPUT,
                recoverable=False
            )

        # Contrôle ADR-008 pour LinkedIn
        if trigger_type == "linkedin_consultation":
            if matching_status != "MATCH_CONFIRMED":
                raise ProviderError(
                    f"ADR-008 : consultation LinkedIn refusée car matching SIRENE = '{matching_status}' (!= MATCH_CONFIRMED)",
                    ProviderStatus.BLOCKED,
                    recoverable=False
                )
            if daily_count >= 5:
                raise ProviderError(
                    f"ADR-008 : quota quotidien atteint ({daily_count}/5)",
                    ProviderStatus.RATE_LIMITED,
                    recoverable=False
                )

        if not self.is_available():
            raise ProviderError(
                "Le binaire 'uv' est requis dans le PATH pour lancer 'invisible-playwright-mcp'.",
                ProviderStatus.TOOL_MISSING,
                recoverable=False
            )

        client_script = Path(__file__).resolve().parent.parent.parent / "mcp_playwright_client.py"
        if not client_script.exists():
            raise ProviderError(
                f"Script client MCP introuvable : {client_script}",
                ProviderStatus.CONFIG_ERROR,
                recoverable=False
            )

        cmd = [
            "uv", "run",
            "--with", "mcp",
            "--python", "3.11",
            "python3", str(client_script),
            "--url", url,
            "--trigger-type", trigger_type,
            "--field-target", field_target,
            "--matching-status", matching_status,
            "--daily-count", str(daily_count),
            "--timeout-sec", str(max(5.0, self.timeout_ms / 1000.0))
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=(self.timeout_ms / 1000.0) + 10.0,
                check=False
            )
        except subprocess.TimeoutExpired:
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.TIMEOUT,
                evidences=[],
                raw_payload={"url": url, "timeout_ms": self.timeout_ms}
            )
        except Exception as e:
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.NETWORK_ERROR,
                evidences=[],
                raw_payload={"url": url, "error": str(e)}
            )

        # Parsing de la réponse JSON du client MCP
        stdout_text = proc.stdout.strip()
        if not stdout_text:
            stderr_snippet = proc.stderr.strip()[:300]
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.TOOL_UNAVAILABLE,
                evidences=[],
                raw_payload={"url": url, "stderr": stderr_snippet}
            )

        # Recherche de la dernière ligne JSON émise
        json_payload: Optional[Dict[str, Any]] = None
        for line in reversed(stdout_text.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    json_payload = json.loads(line)
                    break
                except Exception:
                    continue

        if not json_payload:
            return ProviderResult(
                provider=self.name,
                status=ProviderStatus.PARSE_ERROR,
                evidences=[],
                raw_payload={"raw_stdout": stdout_text[:500]}
            )

        status_str = json_payload.get("status", "SUCCESS")
        if status_str == "TIMEOUT":
            return ProviderResult(provider=self.name, status=ProviderStatus.TIMEOUT, evidences=[], raw_payload=json_payload)
        elif status_str in ("BLOCKED", "RATE_LIMITED"):
            return ProviderResult(provider=self.name, status=ProviderStatus[status_str], evidences=[], raw_payload=json_payload)
        elif status_str != "SUCCESS":
            return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[], raw_payload=json_payload)

        # Construction des évidences
        evidences: List[Evidence] = []
        browser_reason = f"MCP invisible-playwright inspection ({trigger_type})"

        if trigger_type == "linkedin_consultation":
            has_activity = bool(json_payload.get("has_recent_activity", False))
            evidences.append(Evidence(
                field="decision_maker_linkedin_activity",
                value=has_activity,
                source=url,
                source_url=url,
                observed_at=now_iso,
                method=ObservationMethod.BROWSER_AUTOMATION.value,
                provider=self.name,
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text=f"Activité éditoriale publique observée via MCP : {has_activity}",
                confidence=ConfidenceLevel.HIGH.value if has_activity else ConfidenceLevel.MEDIUM.value,
                lead_id=lead_id,
                browser_usage_reason=browser_reason
            ))
            evidences.append(Evidence(
                field="decision_maker_linkedin_source",
                value=url,
                source=url,
                source_url=url,
                observed_at=now_iso,
                method=ObservationMethod.BROWSER_AUTOMATION.value,
                provider=self.name,
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text=f"URL du profil LinkedIn vérifiée via MCP",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id=lead_id,
                browser_usage_reason=browser_reason
            ))
        else:
            offer_clues = json_payload.get("offer_clues", [])
            page_title = json_payload.get("title", "")
            if offer_clues:
                evidences.append(Evidence(
                    field="main_offer",
                    value=f"Services web identifiés ({', '.join(offer_clues[:2])})",
                    source=url,
                    source_url=url,
                    observed_at=now_iso,
                    method=ObservationMethod.BROWSER_AUTOMATION.value,
                    provider=self.name,
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text=f"Indices extraits via MCP : {', '.join(offer_clues)} | Titre : {page_title}",
                    confidence=ConfidenceLevel.MEDIUM.value,
                    lead_id=lead_id,
                    browser_usage_reason=browser_reason
                ))

        status_result = ProviderStatus.SUCCESS if evidences else ProviderStatus.SUCCESS_EMPTY
        return ProviderResult(
            provider=self.name,
            status=status_result,
            evidences=evidences,
            raw_payload=json_payload
        )
