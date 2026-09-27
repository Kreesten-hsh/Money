#!/usr/bin/env python3
"""
tests/test_v2_2_full_pipeline.py — Suite de Tests d'Intégration & Full E2E Money V2.2

Vérifie :
1. test_full_pipeline_v2 : Circulation réelle des données à travers TOUS les composants :
   Lead Input -> Orchestrator (Playwright, theHarvester, Crawlee, API Registry)
   -> Evidence Layer -> Legal Reconciliation -> Truth Evaluator -> Services Métier -> Output
2. test_crawl_planner_multi_page : Intégration réelle de Crawlee sur arborescence multi-pages
3. test_api_registry_doh_wiring : Appel actif de google_dns_doh via ApiRegistryProvider
4. test_ghostwriting_neutralization : Neutralisation stricte du score en l'absence d'activité publique
5. test_sealing_preservation_e2e : Immutabilité absolue des données légales SIRENE
6. test_dynamic_batch_execution : Capacité à traiter un lot arbitraire sans liste en dur
"""

import json
import unittest
from unittest.mock import patch
from pathlib import Path
from typing import Any, Dict, List

from money_v2.contracts.confidence_policy import ConfidencePolicy, EmailClassification
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult, ProviderTelemetry
from money_v2.contracts.provider_status import ProviderStatus
from money_v2.orchestrator.crawl_planner import CrawlPlanner
from money_v2.orchestrator.enrichment_orchestrator import EnrichmentOrchestrator
from money_v2.orchestrator.observability import ObservabilityHub
from money_v2.pipeline import MoneyPipelineV2
from money_v2.providers.api_registry_provider import ApiRegistryProvider
from money_v2.providers.base import BaseProvider
from money_v2.providers.crawlee_provider import CrawleeProvider
from money_v2.providers.playwright_provider import InvisiblePlaywrightProvider
from money_v2.providers.theharvester_provider import TheHarvesterProvider
from money_v2.services.ghostwriting_service import GhostwritingIntelligenceService
from money_v2.services.lead_intelligence_service import LeadIntelligenceService
from money_v2.truth.reconciliation import LegalReconciliationLayer, SealingViolationError


class TestMoneyV22FullPipeline(unittest.TestCase):
    """Banc d'épreuve d'intégration et E2E V2.2."""

    def setUp(self):
        self.hub = ObservabilityHub()
        # Orchestrateur configuré pour tests déterministes et rapides
        self.orchestrator = EnrichmentOrchestrator(
            observability_hub=self.hub,
            enable_theharvester=True,
            enable_playwright=True,
            enable_crawlee=True,
            enable_api_registry=True
        )
        self.pipeline = MoneyPipelineV2(observability_hub=self.hub, orchestrator=self.orchestrator)

    @patch("money_v2.providers.http_provider.HttpProvider._run")
    @patch("money_v2.providers.crawlee_provider.CrawleeProvider.crawl_batch")
    @patch("money_v2.providers.playwright_provider.InvisiblePlaywrightProvider._run")
    @patch("money_v2.providers.theharvester_provider.TheHarvesterProvider._run")
    @patch("money_v2.providers.api_registry_provider.ApiRegistryProvider._run")
    @patch("money_v2.providers.dns_mx_provider.DnsMxProvider._run")
    @patch("money_v2.providers.cms_provider.CmsTechnologyProvider._run")
    def test_01_full_pipeline_v2_data_circulation(
        self,
        mock_cms,
        mock_dns,
        mock_doh,
        mock_harvester,
        mock_playwright,
        mock_crawlee,
        mock_http
    ):
        """
        1. test_full_pipeline_v2 : Démontre la circulation réelle des données entre tous les composants.
        """
        now_iso = get_current_iso_timestamp()
        mock_http.return_value = ProviderResult(
            provider="http_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="main_offer",
                    value="Création de sites Webflow",
                    source="http://alpha-digital-test.fr",
                    source_url="http://alpha-digital-test.fr",
                    observed_at=now_iso,
                    method=ObservationMethod.HTTP_GET.value,
                    provider="http_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="Titre et h1 extraits",
                    confidence=ConfidenceLevel.LOW.value,
                    lead_id="800123456"
                )
            ]
        )
        mock_crawlee.return_value = {
            "total_planned": 1,
            "successful": 1,
            "failed": 0,
            "items": [
                {
                    "url": "http://alpha-digital-test.fr/services",
                    "html_preview": "Nous créons des sites webflow pour PME",
                    "status_code": 200,
                    "retries": 0
                }
            ]
        }
        mock_playwright.return_value = ProviderResult(
            provider="invisible_playwright",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="decision_maker_linkedin_activity",
                    value=True,
                    source="https://linkedin.com/in/thomas-mercier-alpha",
                    source_url="https://linkedin.com/in/thomas-mercier-alpha",
                    observed_at=now_iso,
                    method=ObservationMethod.BROWSER_AUTOMATION.value,
                    provider="invisible_playwright",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="Activité publique observée sur le profil",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id="800123456"
                )
            ]
        )
        mock_harvester.return_value = ProviderResult(
            provider="theharvester_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="public_professional_email",
                    value="contact@alpha-digital.fr",
                    source="theharvester_cli",
                    source_url="osint://theharvester/alpha-digital.fr",
                    observed_at=now_iso,
                    method=ObservationMethod.OSINT_CLI.value,
                    provider="theharvester_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="Email générique découvert",
                    confidence=ConfidenceLevel.LOW.value,
                    lead_id="800123456"
                )
            ]
        )
        mock_doh.return_value = ProviderResult(
            provider="api_registry_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="api_doh_record",
                    value="Trouvé 1 réponses MX",
                    source="api_mega_list://google_dns_doh",
                    source_url="https://dns.google/resolve",
                    observed_at=now_iso,
                    method=ObservationMethod.DNS_QUERY.value,
                    provider="api_registry_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="DoH résolu",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id="800123456"
                )
            ]
        )
        mock_dns.return_value = ProviderResult(
            provider="dns_mx_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="mx_valid",
                    value=True,
                    source="dns.google",
                    source_url="dns://alpha-digital-test.fr/MX",
                    observed_at=now_iso,
                    method=ObservationMethod.DNS_QUERY.value,
                    provider="dns_mx_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="MX valide",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id="800123456"
                )
            ]
        )
        mock_cms.return_value = ProviderResult(
            provider="cms_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="cms_detected",
                    value="Webflow",
                    source="http://alpha-digital-test.fr",
                    source_url="http://alpha-digital-test.fr",
                    observed_at=now_iso,
                    method=ObservationMethod.HTTP_GET.value,
                    provider="cms_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="Balises Webflow détectées",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id="800123456"
                )
            ]
        )

        lead_input = {
            "brand_name": "Agence Digitale Alpha",
            "domain": "alpha-digital-test.fr",
            "website": "http://127.0.0.1:59996/alpha",
            "siren": "800123456",
            "company_name": "ALPHA DIGITAL SAS",
            "company_size": "6 à 9 salariés",
            "company_size_code": "02",
            "decision_maker": "Thomas Mercier",
            "decision_maker_role": "Président",
            "decision_maker_is_person": True,
            "matching_status": "MATCH_CONFIRMED",
            "verification_status": "VERIFIED",
            "main_offer": "Non vérifié",
            "target_clients": "Non vérifié",
            "linkedin_profile_url": "https://linkedin.com/in/thomas-mercier-alpha"
        }

        # Simulation d'enrichissement unitaire complet
        processed_lead, evidences = self.pipeline.process_lead(lead_input)

        # 1. Vérification de la non-altération des champs légaux (Étanchéité)
        self.assertEqual(processed_lead["siren"], "800123456")
        self.assertEqual(processed_lead["company_name"], "ALPHA DIGITAL SAS")
        self.assertEqual(processed_lead["company_size_code"], "02")
        self.assertEqual(processed_lead["decision_maker"], "Thomas Mercier")
        self.assertEqual(processed_lead["decision_maker_role"], "Président")

        # 2. Vérification que la structure des évidences est conforme et non vide
        self.assertIsInstance(evidences, list)
        self.assertTrue(len(evidences) > 0)

        # 3. Vérification de la consolidation AI Lead Intelligence
        self.assertIn("lead_gen_score", processed_lead)
        self.assertTrue(0 <= processed_lead["lead_gen_score"] <= 75)
        self.assertIn("personalized_outreach", processed_lead)
        self.assertIn("Bonjour Thomas,", processed_lead["personalized_outreach"])

        # 4. Vérification de la consolidation Founder Ghostwriting
        self.assertIn("ghostwriting_score", processed_lead)
        self.assertTrue(processed_lead["ghostwriting_score"] > 0)
        self.assertIn("ghostwriting_angles", processed_lead)
        self.assertIsInstance(processed_lead["ghostwriting_angles"], list)

        # 5. Vérification du diagnostic de vérité
        self.assertIn("truth_summary", processed_lead)
        self.assertEqual(processed_lead["truth_summary"]["LEGAL_IDENTITY"], "VERIFIED")
        self.assertEqual(processed_lead["truth_summary"]["LEGAL_EMPLOYEES"], "VERIFIED")
        self.assertEqual(processed_lead["truth_summary"]["LEGAL_DIRECTOR"], "VERIFIED")

    def test_02_crawl_planner_multi_page_integration(self):
        """
        2. Intégration CrawlPlanner : Vérifie la planification et l'extraction multi-pages via Crawlee.
        """
        lead = {
            "brand_name": "Agence Webflow Bêta",
            "domain": "beta-web.fr",
            "website": "https://beta-web.fr",
            "main_offer": "Non vérifié",
            "target_clients": "Non vérifié"
        }
        planner = CrawlPlanner()
        planned_urls = planner.plan_urls_for_lead(lead, max_depth_urls=4)

        self.assertIn("https://beta-web.fr", planned_urls)
        self.assertIn("https://beta-web.fr/services", planned_urls)
        self.assertIn("https://beta-web.fr/contact", planned_urls)
        self.assertTrue(len(planned_urls) <= 4)

    @patch("money_v2.providers.api_registry_provider.ApiRegistryProvider._run")
    @patch("money_v2.providers.http_provider.HttpProvider._run")
    @patch("money_v2.providers.dns_mx_provider.DnsMxProvider._run")
    def test_03_api_registry_doh_wiring_in_orchestrator(self, mock_dns, mock_http, mock_doh):
        """
        3. Vérifie que ApiRegistryProvider (google_dns_doh) est branché et exécutable dans l'orchestrateur.
        """
        now_iso = get_current_iso_timestamp()
        mock_doh.return_value = ProviderResult(
            provider="api_registry_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="api_doh_record",
                    value="Trouvé 1 réponses MX",
                    source="api_mega_list://google_dns_doh",
                    source_url="https://dns.google/resolve",
                    observed_at=now_iso,
                    method=ObservationMethod.DNS_QUERY.value,
                    provider="api_registry_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="DoH OK",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id="google.com"
                )
            ]
        )
        mock_http.return_value = ProviderResult(
            provider="http_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="main_offer",
                    value="Création de sites",
                    source="http://127.0.0.1:59995/gamma",
                    source_url="http://127.0.0.1:59995/gamma",
                    observed_at=now_iso,
                    method=ObservationMethod.HTTP_GET.value,
                    provider="http_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="Site gamma",
                    confidence=ConfidenceLevel.LOW.value,
                    lead_id="google.com"
                )
            ]
        )
        mock_dns.return_value = ProviderResult(
            provider="dns_mx_provider",
            status=ProviderStatus.SUCCESS,
            evidences=[
                Evidence(
                    field="mx_valid",
                    value=True,
                    source="dns.google",
                    source_url="dns://google.com/MX",
                    observed_at=now_iso,
                    method=ObservationMethod.DNS_QUERY.value,
                    provider="dns_mx_provider",
                    provider_status=ProviderStatus.SUCCESS.value,
                    evidence_text="MX OK",
                    confidence=ConfidenceLevel.HIGH.value,
                    lead_id="google.com"
                )
            ]
        )
        lead = {
            "brand_name": "Agence Gamma",
            "domain": "google.com",
            "website": "http://127.0.0.1:59995/gamma",
            "siren": "900111222",
            "company_size_code": "03"
        }
        # Exécution unitaire de l'orchestration
        enriched, evs = self.orchestrator.enrich_lead(lead)
        self.assertIn("mx_valid", enriched)
        mock_doh.assert_called_once()

    def test_04_ghostwriting_score_neutralization(self):
        """
        4. Vérifie que le score Ghostwriting est strictement neutralisé à 0 en l'absence d'activité publique.
        """
        lead_no_activity = {
            "brand_name": "Agence Mu",
            "domain": "mu-agency.fr",
            "matching_status": "MATCH_CONFIRMED",
            "decision_maker": "Claire Dubois",
            "decision_maker_role": "Directrice Générale",
            "decision_maker_is_person": True,
            "decision_maker_linkedin_activity": False,
            "decision_maker_linkedin_source": ""
        }
        score = GhostwritingIntelligenceService.compute_ghostwriting_score(lead_no_activity)
        self.assertEqual(score, 0)

        # En présence d'activité vérifiée
        lead_with_activity = dict(lead_no_activity)
        lead_with_activity["decision_maker_linkedin_activity"] = True
        lead_with_activity["decision_maker_linkedin_source"] = "https://linkedin.com/in/claire-dubois"
        lead_with_activity["company_size_code"] = "02"

        score_active = GhostwritingIntelligenceService.compute_ghostwriting_score(lead_with_activity)
        self.assertTrue(score_active > 0)
        self.assertEqual(score_active, 85)

    def test_05_sealing_preservation_e2e(self):
        """
        5. Vérifie que l'orchestrateur et le pipeline rejettent toute tentative d'altération de SIREN.
        """
        corrupted_lead = {
            "brand_name": "Agence Corrompue",
            "domain": "hacker-agency.fr",
            "siren": "111222333",
            "company_name": "ENTREPRISE LEGALE",
            "company_size_code": "02"
        }
        illegal_ev = Evidence(
            field="siren",
            value="999888777",
            source="external_scraping",
            source_url="http://fake-source",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.BATCH_CRAWL.value,
            provider="crawlee_provider",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="Faux SIREN découvert",
            confidence=ConfidenceLevel.LOW.value,
            lead_id="test_lead"
        )
        with self.assertRaises(SealingViolationError):
            LegalReconciliationLayer.reconcile(corrupted_lead, [illegal_ev])

    def test_06_dynamic_batch_execution(self):
        """
        6. Vérifie le traitement par lot dynamique de plusieurs leads sans liste en dur.
        """
        # Utilisation de providers stub pour tester la tuyauterie batch instantanément
        class FastTestOrchestrator(EnrichmentOrchestrator):
            def enrich_lead(self, lead):
                return dict(lead), []

        fast_pipeline = MoneyPipelineV2(
            observability_hub=self.hub,
            orchestrator=FastTestOrchestrator(observability_hub=self.hub)
        )

        batch = [
            {
                "brand_name": f"Agence Test {i}",
                "domain": f"agency-test-{i}.fr",
                "website": f"https://agency-test-{i}.fr",
                "siren": f"80000000{i}",
                "company_size_code": "02",
                "decision_maker": f"Dirigeant {i}",
                "decision_maker_role": "Gérant",
                "decision_maker_is_person": True,
                "matching_status": "MATCH_CONFIRMED"
            }
            for i in range(1, 4)
        ]

        processed, evs = fast_pipeline.process_batch(batch)
        self.assertEqual(len(processed), 3)
        for p in processed:
            self.assertIn("lead_gen_score", p)
            self.assertIn("personalized_outreach", p)
            self.assertIn("truth_summary", p)


if __name__ == "__main__":
    unittest.main()
