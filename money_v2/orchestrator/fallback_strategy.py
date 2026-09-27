from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from money_v2.contracts.evidence import Evidence
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderStatus
from money_v2.providers.base import BaseProvider
from money_v2.providers.firecrawl_provider import FirecrawlProvider
from money_v2.providers.http_provider import HttpProvider


class FallbackStrategy:
    """
    Gestionnaire de la chaîne de repli déterministe à 3 paliers pour l'audit de site web :
    Palier 1 : HttpProvider (rapide, sans état, stdlib)
    Palier 2 : FirecrawlProvider (API/MCP d'extraction markdown si configurée)
    Palier 3 : Consignation Technique (statut réel sans masquer la cause).

    L'enrichissement via invisible_playwright_mcp reste HORS de cette chaîne synchrone
    et opère via le contrat de staging ou consultation encadrée (ADR-008).
    """

    def __init__(
        self,
        http_provider: Optional[HttpProvider] = None,
        firecrawl_provider: Optional[FirecrawlProvider] = None
    ):
        self.http_provider = http_provider or HttpProvider()
        self.firecrawl_provider = firecrawl_provider or FirecrawlProvider()

    def execute_inspection_chain(
        self,
        url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ProviderResult, List[Dict[str, Any]]]:
        """
        Exécute la chaîne séquentiellement jusqu'à succès ou épuisement des 2 paliers actifs.
        Retourne le ProviderResult final et le journal d'audit de la chaîne.
        """
        ctx = context or {}
        audit_trail: List[Dict[str, Any]] = []

        # Palier 1 : HTTP direct (stdlib)
        res_http = self.http_provider.execute(url, ctx)
        audit_trail.append({
            "tier": 1,
            "provider": self.http_provider.name,
            "status": res_http.status.value,
            "evidences": len(res_http.evidences)
        })

        if res_http.status == ProviderStatus.SUCCESS and res_http.has_evidences:
            return res_http, audit_trail

        # Palier 2 : Firecrawl (si disponible)
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

        # Palier 3 : Consignation Technique
        # Épuisement complet de la chaîne : retourner le résultat d'origine (ou le plus informatif)
        audit_trail.append({
            "tier": 3,
            "provider": "technical_consignation",
            "status": res_http.status.value,
            "note": "Épuisement de la chaîne d'inspection HTTP"
        })
        return res_http, audit_trail
