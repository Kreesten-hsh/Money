from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class ApiRegistryProvider(BaseProvider):
    """
    Provider orchestrant les APIs sélectionnées issues du catalogue API-mega-list.
    Ne prétend JAMAIS qu'une API est active si elle n'est pas réellement implémentée
    et vérifiée dans le registre.
    """

    def __init__(self, config_path: Optional[Path] = None, enabled: bool = True):
        super().__init__(name="api_registry_provider", enabled=enabled)
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_path = config_path or (base_dir / "config" / "providers.yaml")
        self._registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        """Lit la section api_registry de config/providers.yaml en pur stdlib."""
        if not self.config_path.exists():
            return {}

        registry: Dict[str, Dict[str, Any]] = {}
        current_api: Optional[str] = None
        in_api_section = False

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                for line in f:
                    clean = line.rstrip()
                    if clean.strip() == "api_registry:":
                        in_api_section = True
                        continue
                    if in_api_section:
                        if clean and not clean.startswith(" ") and not clean.startswith("#"):
                            break
                        # Clé API niveau 1 (2 espaces)
                        if clean.startswith("  ") and not clean.startswith("    ") and ":" in clean:
                            current_api = clean.strip().rstrip(":")
                            registry[current_api] = {}
                        elif clean.startswith("    ") and current_api and ":" in clean:
                            k, v = clean.strip().split(":", 1)
                            val = v.strip().strip('"').strip("'")
                            registry[current_api][k.strip()] = val
        except Exception:
            return {}

        return registry

    def is_available(self) -> bool:
        return len(self._registry) > 0

    def get_api_status(self, api_key: str) -> str:
        api_info = self._registry.get(api_key, {})
        return str(api_info.get("status", "UNKNOWN"))

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        api_name = str(context.get("api_name") or "google_dns_doh")
        lead_id = str(context.get("lead_id") or target)
        now_iso = get_current_iso_timestamp()

        if api_name not in self._registry:
            raise ProviderError(
                f"L'API '{api_name}' n'est pas répertoriée dans le registre API-mega-list",
                ProviderStatus.INVALID_INPUT
            )

        api_meta = self._registry[api_name]
        status = api_meta.get("status", "INACTIVE")

        if status != "ACTIVE":
            raise ProviderError(
                f"L'API '{api_name}' est enregistrée sous le statut '{status}' et n'est pas activement branchée.",
                ProviderStatus.TOOL_MISSING,
                recoverable=False
            )

        # Implémentation réelle pour les APIs déclarées ACTIVE
        if api_name == "google_dns_doh":
            endpoint = api_meta.get("endpoint", "https://dns.google/resolve")
            doh_url = f"{endpoint}?name={urllib.parse.quote(target)}&type=MX"
            try:
                req = urllib.request.Request(
                    doh_url,
                    headers={"Accept": "application/dns-json", "User-Agent": "Money-V2/ApiRegistry"}
                )
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    if resp.status == 200:
                        try:
                            payload = json.loads(resp.read().decode("utf-8"))
                        except Exception as e:
                            return ProviderResult(
                                provider=self.name,
                                status=ProviderStatus.PARSE_ERROR,
                                evidences=[],
                                raw_payload={"json_parse_error": str(e)}
                            )
                        if not isinstance(payload, dict):
                            return ProviderResult(
                                provider=self.name,
                                status=ProviderStatus.PARSE_ERROR,
                                evidences=[],
                                raw_payload={"invalid_schema": "Expected dictionary response"}
                            )
                        answers = payload.get("Answer", [])
                        evidences: List[Evidence] = []
                        if answers:
                            evidences.append(Evidence(
                                field="api_doh_record",
                                value=f"Trouvé {len(answers)} réponses MX",
                                source="api_mega_list://google_dns_doh",
                                source_url=doh_url,
                                observed_at=now_iso,
                                method=ObservationMethod.DNS_QUERY.value,
                                provider=self.name,
                                provider_status=ProviderStatus.SUCCESS.value,
                                evidence_text=f"API google_dns_doh exécutée avec succès pour {target}",
                                confidence=ConfidenceLevel.HIGH.value,
                                lead_id=lead_id
                            ))
                        return ProviderResult(
                            provider=self.name,
                            status=ProviderStatus.SUCCESS if evidences else ProviderStatus.NO_RESULT,
                            evidences=evidences,
                            raw_payload=payload
                        )
                    return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])
            except Exception as e:
                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.NETWORK_ERROR,
                    evidences=[],
                    raw_payload={"error": str(e)}
                )

        raise ProviderError(f"Handler d'exécution manquant pour l'API active '{api_name}'", ProviderStatus.UNKNOWN_ERROR)
