from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class FirecrawlProvider(BaseProvider):
    """
    Provider Firecrawl pour l'extraction markdown et l'analyse de structure.
    Niveau 2 de la chaîne de repli.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0, enabled: bool = True):
        super().__init__(name="firecrawl_provider", enabled=enabled)
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "")
        self.timeout = timeout

    def is_available(self) -> bool:
        # Nécessite une clé d'API pour les requêtes distantes
        return bool(self.api_key.strip())

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        url = target.strip()
        lead_id = str(context.get("lead_id") or url)
        now_iso = get_current_iso_timestamp()

        if not self.is_available():
            raise ProviderError("Clé FIRECRAWL_API_KEY absente", ProviderStatus.AUTH_REQUIRED)

        endpoint = "https://api.firecrawl.dev/v1/scrape"
        payload = json.dumps({"url": url, "formats": ["markdown"]}).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.NETWORK_ERROR,
                        evidences=[]
                    )
                data = json.loads(resp.read().decode("utf-8"))
                markdown_text = data.get("data", {}).get("markdown", "")
                metadata = data.get("data", {}).get("metadata", {})

                evidences: List[Evidence] = []
                title = metadata.get("title", "")
                desc = metadata.get("description", "")

                if desc or title:
                    evidences.append(Evidence(
                        field="main_offer",
                        value=f"Extrait Firecrawl : {title[:60]}",
                        source=url,
                        source_url=url,
                        observed_at=now_iso,
                        method=ObservationMethod.DOM_INSPECTION.value,
                        provider=self.name,
                        provider_status=ProviderStatus.SUCCESS.value,
                        evidence_text=f"Firecrawl scrape validé : '{desc[:90] or title[:90]}'",
                        confidence=ConfidenceLevel.MEDIUM.value,
                        lead_id=lead_id
                    ))

                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.SUCCESS if evidences else ProviderStatus.NO_RESULT,
                    evidences=evidences,
                    raw_payload={"metadata": metadata, "markdown_length": len(markdown_text)}
                )

        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                return ProviderResult(provider=self.name, status=ProviderStatus.AUTH_REQUIRED, evidences=[])
            if he.code == 429:
                return ProviderResult(provider=self.name, status=ProviderStatus.RATE_LIMITED, evidences=[])
            return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])
        except (urllib.error.URLError, TimeoutError) as ue:
            err_msg = str(ue).lower()
            if "timed out" in err_msg:
                return ProviderResult(provider=self.name, status=ProviderStatus.TIMEOUT, evidences=[])
            return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])
