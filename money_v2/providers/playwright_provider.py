from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class InvisiblePlaywrightProvider(BaseProvider):
    """
    Provider Navigateur Furtif (invisible_playwright_mcp / patchright).
    Niveau 3 de la chaîne de repli pour les sites sous protection WAF / Cloudflare
    et pour les consultations LinkedIn unitaire ultra-encadrées (ADR-008).

    Règles absolues d'étanchéité :
    - N'écrit JAMAIS dans decision_maker, decision_maker_role, company_size, company_size_code.
    - Débit max 5 consultations/jour sur LinkedIn pour les dirigeants MATCH_CONFIRMED.
    """

    FORBIDDEN_FIELDS = {
        "decision_maker",
        "decision_maker_role",
        "company_size",
        "company_size_code",
    }

    def __init__(self, headless: bool = True, timeout_ms: int = 15000, enabled: bool = True):
        super().__init__(name="invisible_playwright_mcp", enabled=enabled)
        self.headless = headless
        self.timeout_ms = timeout_ms

    def is_available(self) -> bool:
        """Vérifie la présence du moteur furtif patchright ou de playwright."""
        try:
            import patchright.sync_api  # noqa: F401
            return True
        except ImportError:
            try:
                import playwright.sync_api  # noqa: F401
                return True
            except ImportError:
                return False

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        url = target.strip()
        lead_id = str(context.get("lead_id") or url)
        trigger_type = str(context.get("trigger_type") or "annuaire_fallback")
        field_target = str(context.get("field_target") or "main_offer")
        now_iso = get_current_iso_timestamp()

        # Contrôle machine de l'interdit de corruption Niveau 1/2
        if field_target in self.FORBIDDEN_FIELDS:
            raise ProviderError(
                f"Violation d'étanchéité : le provider Niveau 4 {self.name} "
                f"ne peut pas alimenter le champ légal '{field_target}'",
                ProviderStatus.INVALID_INPUT,
                recoverable=False
            )

        # Contrôle du débit ADR-008 pour LinkedIn
        if trigger_type == "linkedin_consultation":
            matching_status = context.get("matching_status", "")
            if matching_status != "MATCH_CONFIRMED":
                raise ProviderError(
                    f"ADR-008 : consultation LinkedIn refusée car matching SIRENE = '{matching_status}' (!= MATCH_CONFIRMED)",
                    ProviderStatus.BLOCKED,
                    recoverable=False
                )
            daily_count = int(context.get("linkedin_daily_count", 0))
            if daily_count >= 5:
                raise ProviderError(
                    f"ADR-008 : quota quotidien atteint ({daily_count}/5)",
                    ProviderStatus.RATE_LIMITED,
                    recoverable=False
                )

        # Tenter l'import du moteur furtif patchright en priorité
        engine = None
        try:
            from patchright.sync_api import sync_playwright
            engine = "patchright"
        except ImportError:
            try:
                from playwright.sync_api import sync_playwright
                engine = "playwright"
            except ImportError:
                raise ProviderError("Ni patchright ni playwright ne sont disponibles", ProviderStatus.TOOL_MISSING)

        evidences: List[Evidence] = []
        raw_info: Dict[str, Any] = {"engine": engine, "trigger_type": trigger_type}

        import shutil
        chrome_bin = shutil.which("google-chrome") or shutil.which("chromium")
        launch_kwargs: Dict[str, Any] = {
            "headless": self.headless,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
        if chrome_bin:
            launch_kwargs["executable_path"] = chrome_bin

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(**launch_kwargs)
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page.set_default_timeout(self.timeout_ms)

                try:
                    resp = page.goto(url, wait_until="domcontentloaded")
                except Exception as e:
                    browser.close()
                    err_text = str(e).lower()
                    if "timeout" in err_text:
                        return ProviderResult(provider=self.name, status=ProviderStatus.TIMEOUT, evidences=[])
                    return ProviderResult(provider=self.name, status=ProviderStatus.NETWORK_ERROR, evidences=[])

                status_code = resp.status if resp else 0
                raw_info["status_code"] = status_code

                if status_code in (403, 401):
                    # Tenter d'attendre un éventuel challenge
                    page.wait_for_timeout(2000)

                content = page.content()
                page_title = page.title()
                raw_info["title"] = page_title

                if trigger_type == "linkedin_consultation":
                    # Vérification unitaire d'activité éditoriale publique
                    has_recent_activity = bool(re.search(r'(activité|posts|articles|publications)', content, re.IGNORECASE))
                    evidences.append(Evidence(
                        field="decision_maker_linkedin_activity",
                        value=has_recent_activity,
                        source=url,
                        source_url=url,
                        observed_at=now_iso,
                        method=ObservationMethod.BROWSER_AUTOMATION.value,
                        provider=self.name,
                        provider_status=ProviderStatus.SUCCESS.value,
                        evidence_text=f"Activité LinkedIn consultée publiquement sans connexion : {has_recent_activity}",
                        confidence=ConfidenceLevel.HIGH.value,
                        lead_id=lead_id,
                        metadata={"profile_url": url, "engine": engine}
                    ))
                else:
                    # Repli site ou annuaire (PagesJaunes, Malt, Sortlist)
                    text_corpus = f"{page_title} {content[:10000]}".lower()
                    if any(k in text_corpus for k in ["création site", "webflow", "wordpress", "e-commerce", "shopify"]):
                        evidences.append(Evidence(
                            field="main_offer",
                            value="Conception de sites internet & solutions digitales",
                            source=url,
                            source_url=url,
                            observed_at=now_iso,
                            method=ObservationMethod.BROWSER_AUTOMATION.value,
                            provider=self.name,
                            provider_status=ProviderStatus.SUCCESS.value,
                            evidence_text=f"Offre observée via navigateur furtif : {page_title[:80]}",
                            confidence=ConfidenceLevel.MEDIUM.value,
                            lead_id=lead_id,
                            metadata={"engine": engine}
                        ))

                browser.close()

                status = ProviderStatus.SUCCESS if evidences else ProviderStatus.NO_RESULT
                return ProviderResult(
                    provider=self.name,
                    status=status,
                    evidences=evidences,
                    raw_payload=raw_info
                )

        except Exception as e:
            err_msg = str(e).lower()
            if "timeout" in err_msg:
                return ProviderResult(provider=self.name, status=ProviderStatus.TIMEOUT, evidences=[])
            return ProviderResult(provider=self.name, status=ProviderStatus.UNKNOWN_ERROR, evidences=[])
