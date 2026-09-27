from __future__ import annotations

import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class HttpProvider(BaseProvider):
    """
    Provider HTTP standard pour l'audit déterministe des sites vitrines d'agences.
    Niveau 1 de la chaîne de repli.
    """

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, timeout: float = 6.0, user_agent: Optional[str] = None):
        super().__init__(name="http_provider")
        self.timeout = timeout
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT

    def is_available(self) -> bool:
        return True

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        url = target.strip()
        lead_id = str(context.get("lead_id") or url)
        now_iso = get_current_iso_timestamp()

        if not url or not (url.startswith("http://") or url.startswith("https://")):
            raise ProviderError(f"URL invalide : {url}", ProviderStatus.INVALID_INPUT)

        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent}
        )
        ctx = ssl.create_default_context()

        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                status_code = resp.status
                if status_code != 200:
                    status = ProviderStatus.BLOCKED if status_code in (403, 401) else ProviderStatus.NETWORK_ERROR
                    return ProviderResult(
                        provider=self.name,
                        status=status,
                        evidences=[],
                        raw_payload={"status_code": status_code, "url": url}
                    )

                html_bytes = resp.read(80000)
                html = html_bytes.decode("utf-8", errors="ignore")

                evidences: List[Evidence] = []

                # Titre et description
                title_m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
                page_title = " ".join(title_m.group(1).split()) if title_m else ""

                desc_m = re.search(
                    r'<meta[^>]*name=[\"\']description[\"\'][^>]*content=[\"\']([^\"\']*)[\"\']',
                    html,
                    re.IGNORECASE
                )
                meta_desc = " ".join(desc_m.group(1).split()) if desc_m else ""
                text_corpus = f"{page_title} {meta_desc}".lower()

                # Détection de l'offre
                main_offer = None
                offer_evidence = ""
                if any(k in text_corpus for k in ["prestashop", "e-commerce", "shopify"]):
                    main_offer = "Création E-commerce & Refonte Web"
                    offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
                elif "webflow" in text_corpus:
                    main_offer = "Conception Webflow & Sites sur-mesure"
                    offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
                elif "wordpress" in text_corpus:
                    main_offer = "Création & Maintenance WordPress"
                    offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
                elif any(k in text_corpus for k in ["seo", "referencement"]):
                    main_offer = "Création de sites Web & Référencement SEO"
                    offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
                elif any(k in text_corpus for k in ["site internet", "site web", "agence web", "agence digitale"]):
                    main_offer = "Création et refonte de sites web"
                    offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"

                if main_offer:
                    evidences.append(Evidence(
                        field="main_offer",
                        value=main_offer,
                        source=url,
                        source_url=url,
                        observed_at=now_iso,
                        method=ObservationMethod.DOM_INSPECTION.value,
                        provider=self.name,
                        provider_status=ProviderStatus.SUCCESS.value,
                        evidence_text=offer_evidence,
                        confidence=ConfidenceLevel.HIGH.value,
                        lead_id=lead_id
                    ))

                # Détection cible client
                explicit_pme = re.search(r"\b(pme|tpe|eti|entreprises locales|grands comptes|startups?)\b", meta_desc.lower())
                if explicit_pme:
                    target_kw = explicit_pme.group(0).upper()
                    evidences.append(Evidence(
                        field="target_clients",
                        value=f"Entreprises cibles ({target_kw})",
                        source=url,
                        source_url=url,
                        observed_at=now_iso,
                        method=ObservationMethod.DOM_INSPECTION.value,
                        provider=self.name,
                        provider_status=ProviderStatus.SUCCESS.value,
                        evidence_text=f"Mention explicite meta description : '{meta_desc[:90]}'",
                        confidence=ConfidenceLevel.HIGH.value,
                        lead_id=lead_id
                    ))

                status = ProviderStatus.SUCCESS if evidences else ProviderStatus.NO_RESULT
                return ProviderResult(
                    provider=self.name,
                    status=status,
                    evidences=evidences,
                    raw_payload={"status_code": 200, "page_title": page_title, "meta_desc": meta_desc}
                )

        except urllib.error.HTTPError as he:
            if he.code in (403, 401):
                return ProviderResult(provider=self.name, status=ProviderStatus.BLOCKED, evidences=[])
            if he.code == 429:
                return ProviderResult(provider=self.name, status=ProviderStatus.RATE_LIMITED, evidences=[])
            return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])
        except (urllib.error.URLError, TimeoutError, socket.timeout) as ue:
            err_msg = str(ue).lower()
            if "timed out" in err_msg or isinstance(ue, (TimeoutError, socket.timeout)):
                return ProviderResult(provider=self.name, status=ProviderStatus.TIMEOUT, evidences=[])
            return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])
