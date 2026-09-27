from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from money_v2.contracts.evidence import Evidence
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderStatus
from money_v2.providers.base import BaseProvider
from money_v2.providers.crawlee_provider import CrawleeProvider
from money_v2.providers.firecrawl_provider import FirecrawlProvider
from money_v2.providers.http_provider import HttpProvider
from money_v2.providers.playwright_provider import InvisiblePlaywrightProvider


class FallbackStrategy:
    """
    Gestionnaire de la chaîne de repli déterministe à 4 paliers pour l'inspection de site :
    Palier 1 : HttpProvider (rapide, sans état, stdlib)
    Palier 2 : FirecrawlProvider (API/MCP d'extraction markdown si configurée)
    Palier 3 : InvisiblePlaywrightProvider (navigateur furtif Turnstile/WAF unitaire)
    Palier 4 : CrawleeProvider (moteur de batch crawl multi-pages avec file d'attente et retries)
    Palier 5 : Défaillance technique enregistrée (ERROR) sans masquer la cause.
    """

    def __init__(
        self,
        http_provider: Optional[HttpProvider] = None,
        firecrawl_provider: Optional[FirecrawlProvider] = None,
        playwright_provider: Optional[InvisiblePlaywrightProvider] = None,
        crawlee_provider: Optional[CrawleeProvider] = None
    ):
        self.http_provider = http_provider or HttpProvider()
        self.firecrawl_provider = firecrawl_provider or FirecrawlProvider()
        self.playwright_provider = playwright_provider or InvisiblePlaywrightProvider()
        self.crawlee_provider = crawlee_provider or CrawleeProvider()

    def execute_inspection_chain(
        self,
        url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ProviderResult, List[Dict[str, Any]]]:
        """
        Exécute la chaîne séquentiellement jusqu'à succès ou épuisement des 4 paliers.
        Retourne le ProviderResult final et le journal d'audit de la chaîne.
        """
        ctx = context or {}
        audit_trail: List[Dict[str, Any]] = []

        # Palier 1 : HTTP direct
        res_http = self.http_provider.execute(url, ctx)
        audit_trail.append({
            "tier": 1,
            "provider": self.http_provider.name,
            "status": res_http.status.value,
            "evidences": len(res_http.evidences)
        })

        if res_http.status == ProviderStatus.SUCCESS and res_http.has_evidences:
            return res_http, audit_trail

        # Palier 2 : Firecrawl (si dispo)
        if self.firecrawl_provider.is_available():
            res_fc = self.firecrawl_provider.execute(url, ctx)
            audit_trail.append({
                "tier": 2,
                "provider": self.firecrawl_provider.name,
                "status": res_fc.status.value,
                "evidences": len(res_fc.evidences)
            })
            if res_fc.status == ProviderStatus.SUCCESS and res_fc.has_evidences:
                return res_fc, audit_trail
        else:
            audit_trail.append({
                "tier": 2,
                "provider": self.firecrawl_provider.name,
                "status": ProviderStatus.TOOL_MISSING.value,
                "note": "Clé Firecrawl non configurée"
            })

        # Palier 3 : Invisible Playwright MCP (navigateur furtif)
        if self.playwright_provider.is_available():
            res_pw = self.playwright_provider.execute(url, ctx)
            audit_trail.append({
                "tier": 3,
                "provider": self.playwright_provider.name,
                "status": res_pw.status.value,
                "evidences": len(res_pw.evidences)
            })
            if res_pw.status == ProviderStatus.SUCCESS and res_pw.has_evidences:
                return res_pw, audit_trail
        else:
            audit_trail.append({
                "tier": 3,
                "provider": self.playwright_provider.name,
                "status": ProviderStatus.TOOL_MISSING.value,
                "note": "Playwright/patchright non disponible"
            })

        # Palier 4 : Crawlee Batch Multi-pages
        if self.crawlee_provider.is_available():
            # Exploration d'arborescence multi-pages sur les services
            base_url = url.rstrip("/")
            candidate_urls = [base_url, f"{base_url}/services"]
            ctx_crawlee = dict(ctx)
            ctx_crawlee["urls"] = candidate_urls

            res_cr = self.crawlee_provider.execute(url, ctx_crawlee)
            audit_trail.append({
                "tier": 4,
                "provider": self.crawlee_provider.name,
                "status": res_cr.status.value,
                "evidences": len(res_cr.evidences)
            })
            if res_cr.is_success and res_cr.has_evidences:
                return res_cr, audit_trail
        else:
            audit_trail.append({
                "tier": 4,
                "provider": self.crawlee_provider.name,
                "status": ProviderStatus.TOOL_MISSING.value,
                "note": "Node/Crawlee non disponible"
            })

        # Épuisement complet de la chaîne : retourner le résultat le plus informatif
        return res_http, audit_trail
