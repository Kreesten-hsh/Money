from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class TheHarvesterProvider(BaseProvider):
    """
    Provider theHarvester pour la collecte OSINT passive d'emails de domaine.
    Respecte strictement la politique de confiance et ne convertit jamais
    un pattern d'adresse en email vérifié.
    """

    BANNED_EMAIL_DOMAINS: Set[str] = {
        'gmail.com', 'googlemail.com', 'yahoo.com', 'yahoo.fr', 'hotmail.com',
        'hotmail.fr', 'outlook.com', 'outlook.fr', 'live.com', 'live.fr',
        'orange.fr', 'wanadoo.fr', 'free.fr', 'sfr.fr', 'laposte.net',
        'icloud.com', 'me.com', 'msn.com', 'bbox.fr', 'aol.com'
    }

    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    def __init__(
        self,
        config_path: Optional[Path] = None,
        binary_path: Optional[str] = None,
        timeout: int = 40,
        enabled: bool = True
    ):
        super().__init__(name="theharvester_provider", enabled=enabled)
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_path = config_path or (base_dir / "config" / "theHarvester.yaml")
        self.timeout = timeout
        self._binary_path = binary_path

    def _resolve_binary(self) -> Optional[str]:
        if self._binary_path and Path(self._binary_path).exists():
            return self._binary_path
        candidates = ["theHarvester", "theharvester"]
        for c in candidates:
            found = shutil.which(c)
            if found:
                return found
        return None

    def is_available(self) -> bool:
        """Vérifie la présence effective du binaire theHarvester dans le PATH."""
        return self._resolve_binary() is not None

    def _load_active_sources(self) -> List[str]:
        """Charge dynamiquement les sources passives autorisées depuis le YAML sans dépendance externe."""
        if not self.config_path.exists():
            return ["crtsh", "duckduckgo", "bing"]

        sources: List[str] = []
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                in_active = False
                for line in f:
                    clean = line.strip()
                    if clean.startswith("active_sources:"):
                        in_active = True
                        continue
                    if in_active:
                        if clean.startswith("-"):
                            src = clean.lstrip("-").split("#")[0].strip()
                            if src:
                                sources.append(src)
                        elif re.match(r"^[a-zA-Z_]+:", clean):
                            break
        except Exception:
            return ["crtsh", "duckduckgo", "bing"]

        return sources or ["crtsh", "duckduckgo", "bing"]

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        domain = target.strip().lower()
        lead_id = str(context.get("lead_id") or domain)
        now_iso = get_current_iso_timestamp()

        binary = self._resolve_binary()
        if not binary:
            raise ProviderError(
                "Le binaire theHarvester est introuvable dans le PATH.",
                ProviderStatus.TOOL_MISSING,
                recoverable=False
            )

        sources = self._load_active_sources()
        sources_arg = ",".join(sources)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_base = Path(tmp_dir) / f"th_{domain.replace('.', '_')}"
            cmd = [
                binary,
                "-d", domain,
                "-b", sources_arg,
                "-l", "100",
                "-f", str(output_base)
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False
                )
            except subprocess.TimeoutExpired:
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.TIMEOUT,
                    evidences=[],
                    raw_payload={"domain": domain, "timeout_seconds": self.timeout}
                )
            except Exception as e:
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.NETWORK_ERROR,
                    evidences=[],
                    raw_payload={"domain": domain, "error": str(e)}
                )

            json_file = Path(f"{output_base}.json")
            if not json_file.exists():
                matches = list(Path(tmp_dir).glob("*.json"))
                if matches:
                    json_file = matches[0]
                else:
                    # Aucune sortie JSON générée
                    if proc.returncode != 0:
                        return ProviderResult(
                            provider=self.name,
                            status=ProviderStatus.UNKNOWN_ERROR,
                            evidences=[],
                            raw_payload={"stderr": proc.stderr[:500], "returncode": proc.returncode}
                        )
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.NO_RESULT,
                        evidences=[]
                    )

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.UNKNOWN_ERROR,
                    evidences=[],
                    raw_payload={"json_parse_error": str(e)}
                )

            raw_emails = data.get("emails", [])
            valid_emails: List[str] = []
            evidences: List[Evidence] = []

            for raw_em in raw_emails:
                em = str(raw_em).strip().lower()
                if not self.EMAIL_REGEX.match(em):
                    continue
                em_domain = em.split("@")[1]
                if em_domain in self.BANNED_EMAIL_DOMAINS:
                    continue
                # Concordance stricte de domaine
                if domain and (em_domain != domain and not em_domain.endswith("." + domain)):
                    continue

                valid_emails.append(em)
                evidences.append(Evidence(
                    field="public_professional_email",
                    value=em,
                    source="theHarvester",
                    source_url=f"osint://theharvester/{domain}",
                    observed_at=now_iso,
                    method=ObservationMethod.OSINT_CLI.value,
                    provider=self.name,
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text=f"Email public indexé via OSINT passif ({','.join(sources)}) : {em}",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id=lead_id,
                    metadata={"target_domain": domain, "email_domain": em_domain}
                ))

            # Extraction éventuelle de patterns d'adresses (sans jamais les présenter comme emails réels)
            hosts = data.get("hosts", [])
            pattern_evidences: List[Evidence] = []
            if "@" not in "".join(hosts) and len(valid_emails) > 1:
                # Analyse de pattern indicative
                pattern_evidences.append(Evidence(
                    field="email_pattern_indication",
                    value="multi_user_domain",
                    source="theHarvester",
                    source_url=f"osint://theharvester/{domain}",
                    observed_at=now_iso,
                    method=ObservationMethod.OSINT_CLI.value,
                    provider=self.name,
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="Multiples boîtes nominatives observées, schéma potentiel",
                    confidence=ConfidenceLevel.PATTERN.value,
                    lead_id=lead_id
                ))

            status = ProviderStatus.SUCCESS if evidences else ProviderStatus.NO_RESULT
            return ProviderResult(
                provider=self.name,
                status=status,
                evidences=evidences + pattern_evidences,
                raw_payload={"emails_found": len(valid_emails), "hosts_found": len(hosts)}
            )
