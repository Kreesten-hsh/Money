from __future__ import annotations

import re
import urllib.parse
from typing import Any, Dict, List, Optional, Set, Tuple
from money_v2.contracts.confidence_policy import ConfidencePolicy, EmailClassification
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderStatus
from money_v2.providers.crawlee_provider import CrawleeProvider


class CrawlPlanner:
    """
    Planificateur de crawl industriel multi-pages pilotant CrawleeProvider.
    Identifie les besoins d'enrichissement profond d'un lead (offres, cibles, contacts, mentions légales),
    génère la file d'attente d'URLs ciblées et normalise les évidences extraites avec provenance exacte.
    """

    CANDIDATE_SUBPATHS = [
        "",
        "/services",
        "/offres",
        "/expertises",
        "/contact",
        "/mentions-legales"
    ]

    OFFER_KEYWORDS = [
        "création de site", "développement web", "webflow", "wordpress",
        "shopify", "e-commerce", "sur-mesure", "refonte", "seo", "ux/ui"
    ]

    TARGET_KEYWORDS = [
        "pme", "eti", "artisans", "b2b", "startups", "commerçants", "entreprises"
    ]

    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

    def __init__(self, crawlee_provider: Optional[CrawleeProvider] = None):
        self.crawlee = crawlee_provider or CrawleeProvider(concurrency=3, max_retries=2, timeout_sec=8)

    def plan_urls_for_lead(self, lead: Dict[str, Any], max_depth_urls: int = 4) -> List[str]:
        """
        Détermine dynamiquement les URLs à crawler selon les informations manquantes du lead.
        """
        website = str(lead.get("website") or "").strip()
        domain = str(lead.get("domain") or "").strip()

        if not website:
            if not domain:
                return []
            website = f"https://{domain}"

        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"

        base_url = website.rstrip("/")
        planned: List[str] = [base_url]

        # Si l'offre ou la cible est manquante, planifier les pages de services
        curr_offer = str(lead.get("main_offer") or "").strip()
        if not curr_offer or curr_offer in ("Non vérifié", "Non renseigné", "Inconnu"):
            planned.append(f"{base_url}/services")
            planned.append(f"{base_url}/offres")

        # Si le contact ou les mentions légales manquent
        curr_email = str(lead.get("public_professional_email") or "").strip()
        if not curr_email:
            planned.append(f"{base_url}/contact")
            planned.append(f"{base_url}/mentions-legales")

        # Dédupliquer et borner au maximum requis
        unique_urls: List[str] = []
        for u in planned:
            if u not in unique_urls:
                unique_urls.append(u)
            if len(unique_urls) >= max_depth_urls:
                break

        return unique_urls

    def execute_lead_crawl(
        self,
        lead: Dict[str, Any],
        max_urls: int = 3
    ) -> Tuple[List[Evidence], Dict[str, Any]]:
        """
        Exécute le crawl planifié pour un lead et extrait les évidences structurées.
        """
        urls = self.plan_urls_for_lead(lead, max_depth_urls=max_urls)
        if not urls:
            return [], {"total_planned": 0, "status": "NO_URLS"}

        lead_id = str(lead.get("brand_name") or lead.get("domain") or "unknown_lead")
        lead_domain = str(lead.get("domain") or "").strip().lower()
        now_iso = get_current_iso_timestamp()

        crawl_summary = self.crawlee.crawl_batch(urls)
        evidences: List[Evidence] = []

        for item in crawl_summary.get("items", []):
            page_url = item.get("url", "")
            html_preview = item.get("html_preview", "")
            text_lower = html_preview.lower()

            # 1. Évidence de crawl générale avec source URL exacte
            evidences.append(Evidence(
                field="crawled_content",
                value=f"Page crawlée avec succès (retries: {item.get('retries', 0)})",
                source=page_url,
                source_url=page_url,
                observed_at=now_iso,
                method=ObservationMethod.BATCH_CRAWL.value,
                provider=self.crawlee.name,
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text=f"Exploration Crawlee réussie de la page {page_url}",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id=lead_id,
                metadata={"status_code": item.get("status_code", 200), "retries": item.get("retries", 0)}
            ))

            # 2. Extraction d'offre si mots-clés détectés sur page de services ou accueil
            matched_offers = [k for k in self.OFFER_KEYWORDS if k in text_lower]
            if matched_offers and (not lead.get("main_offer") or lead.get("main_offer") == "Non vérifié"):
                evidences.append(Evidence(
                    field="main_offer",
                    value=f"Services web & digitaux observés ({', '.join(matched_offers[:2])})",
                    source=page_url,
                    source_url=page_url,
                    observed_at=now_iso,
                    method=ObservationMethod.BATCH_CRAWL.value,
                    provider=self.crawlee.name,
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text=f"Prestation observée sur {page_url} : signaux {', '.join(matched_offers)}",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id=lead_id
                ))

            # 3. Extraction de cible si mots-clés détectés
            matched_targets = [t for t in self.TARGET_KEYWORDS if t in text_lower]
            if matched_targets and (not lead.get("target_clients") or lead.get("target_clients") == "Non vérifié"):
                evidences.append(Evidence(
                    field="target_clients",
                    value=f"Clients cibles observés : {', '.join(matched_targets[:2])}",
                    source=page_url,
                    source_url=page_url,
                    observed_at=now_iso,
                    method=ObservationMethod.BATCH_CRAWL.value,
                    provider=self.crawlee.name,
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text=f"Typologie client mentionnée sur {page_url}",
                    confidence=ConfidenceLevel.MEDIUM.value,
                    lead_id=lead_id
                ))

            # 4. Extraction d'email professionnel sur page de contact ou mentions légales
            if not lead.get("public_professional_email"):
                found_emails = self.EMAIL_REGEX.findall(html_preview)
                for em in found_emails:
                    em_clean = em.strip().lower()
                    em_domain = em_clean.split("@")[1] if "@" in em_clean else ""
                    if lead_domain and (em_domain == lead_domain or em_domain.endswith("." + lead_domain)):
                        classification = ConfidencePolicy.classify_email(em_clean, lead.get("decision_maker"))
                        evidences.append(Evidence(
                            field="public_professional_email",
                            value=em_clean,
                            source=page_url,
                            source_url=page_url,
                            observed_at=now_iso,
                            method=ObservationMethod.BATCH_CRAWL.value,
                            provider=self.crawlee.name,
                            provider_status=ProviderStatus.SUCCESS.value,
                            evidence_text=f"Email public extrait sur la page {page_url} [{classification.value}]",
                            confidence=ConfidenceLevel.HIGH.value if classification != EmailClassification.GENERIC_EMAIL else ConfidenceLevel.MEDIUM.value,
                            lead_id=lead_id,
                            email_classification=classification.value
                        ))
                        break

        return evidences, crawl_summary
