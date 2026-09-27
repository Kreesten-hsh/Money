from __future__ import annotations

import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class CmsTechnologyProvider(BaseProvider):
    """
    Provider de détection d'empreinte CMS & Stack technologique observable.
    Interroge le site vitrine et analyse les signatures HTML et en-têtes HTTP.
    """

    CMS_SIGNATURES = [
        ("WordPress", [
            (r'wp-content|wp-includes', "Balises ou ressources internes '/wp-content/' ou '/wp-includes/'"),
            (r'<meta[^>]*name=[\"\']generator[\"\'][^>]*content=[\"\']WordPress', "Balise meta generator WordPress explicite")
        ]),
        ("Webflow", [
            (r'assets\.website-files\.com|d3e54v103j8qbb\.cloudfront\.net', "Ressources CDN Webflow explicites"),
            (r'html[^>]*data-wf-page', "Attribut HTML 'data-wf-page' caractéristique de Webflow")
        ]),
        ("Shopify", [
            (r'cdn\.shopify\.com', "Ressources hébergées sur cdn.shopify.com"),
            (r'Shopify\.theme', "Objet Javascript global Shopify.theme")
        ]),
        ("PrestaShop", [
            (r'/modules/ps_|/themes/classic/', "Structure d'arborescence PrestaShop '/modules/ps_'"),
            (r'var prestashop =', "Objet global javascript 'var prestashop'")
        ]),
        ("Drupal", [
            (r'Drupal\.settings|/sites/default/files', "Arborescence standard Drupal '/sites/default/files'"),
            (r'<meta[^>]*name=[\"\']generator[\"\'][^>]*content=[\"\']Drupal', "Balise meta generator Drupal explicite")
        ]),
        ("Wix", [
            (r'static\.wixstatic\.com', "Ressources statiques CDN Wix"),
            (r'<meta[^>]*name=[\"\']generator[\"\'][^>]*content=[\"\']Wix\.com', "Meta generator Wix")
        ])
    ]

    def __init__(self, timeout: float = 6.0, enabled: bool = True):
        super().__init__(name="cms_provider", enabled=enabled)
        self.timeout = timeout

    def is_available(self) -> bool:
        return True

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        url = target.strip()
        lead_id = str(context.get("lead_id") or url)
        now_iso = get_current_iso_timestamp()

        if not url or not (url.startswith("http://") or url.startswith("https://")):
            raise ProviderError(f"URL cible invalide : {url}", ProviderStatus.INVALID_INPUT)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )
        ctx = ssl.create_default_context()

        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                headers_str = str(resp.headers).lower()
                body_chunk = resp.read(80000).decode("utf-8", errors="ignore")

                # Détection en-têtes
                detected_cms: Optional[str] = None
                evidence_text = ""

                if "x-powered-by" in headers_str and "wp" in headers_str:
                    detected_cms = "WordPress"
                    evidence_text = "En-tête HTTP 'X-Powered-By' indiquant WordPress"

                if not detected_cms:
                    for cms_name, rules in self.CMS_SIGNATURES:
                        for pattern, justification in rules:
                            if re.search(pattern, body_chunk, re.IGNORECASE):
                                detected_cms = cms_name
                                evidence_text = justification
                                break
                        if detected_cms:
                            break

                evidences: List[Evidence] = []
                if detected_cms:
                    evidences.append(Evidence(
                        field="cms_detected",
                        value=detected_cms,
                        source=url,
                        source_url=url,
                        observed_at=now_iso,
                        method=ObservationMethod.DOM_INSPECTION.value,
                        provider=self.name,
                        provider_status=ProviderStatus.SUCCESS.value,
                        evidence_text=evidence_text,
                        confidence=ConfidenceLevel.HIGH.value,
                        lead_id=lead_id,
                        metadata={"cms": detected_cms}
                    ))
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.SUCCESS,
                        evidences=evidences,
                        raw_payload={"cms": detected_cms, "evidence": evidence_text}
                    )

                return ProviderResult(
                    provider=self.name,
                    status=ProviderStatus.NO_RESULT,
                    evidences=[],
                    raw_payload={"inspected_url": url, "detected": False}
                )

        except urllib.error.HTTPError as he:
            if he.code in (403, 401):
                return ProviderResult(provider=self.name, status=ProviderStatus.BLOCKED, evidences=[])
            return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])
        except (urllib.error.URLError, TimeoutError) as ue:
            err_msg = str(ue).lower()
            if "timed out" in err_msg:
                return ProviderResult(provider=self.name, status=ProviderStatus.TIMEOUT, evidences=[])
            return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])
