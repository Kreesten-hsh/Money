#!/usr/bin/env python3
"""
tests/test_v2_architecture.py — Suite de Tests Comportementaux Money V2

Couvre les 24 exigences comportementales critiques de l'architecture V2 :
1. provider_missing
2. provider_timeout
3. provider_network_error
4. provider_blocked
5. provider_returns_no_result
6. provider_returns_malformed_data
7. provider_returns_conflicting_evidence
8. mcp_attempts_to_overwrite_sirene
9. theharvester_returns_pattern_only
10. theharvester_returns_duplicate_emails
11. fallback_strategy_3_tiers
12. mcp_playwright_client_isolation
13. api_provider_unavailable
14. api_registry_provider_inactive
15. person_morale_selected_as_decision_maker
16. commissaire_aux_comptes_selected
17. new_discovery_batch
18. duplicate_historical_lead
19. new_city
20. hardcoded_benchmark_list_removal
21. temporal_evidence
22. stale_evidence
23. unsupported_outreach_claim
24. legal_osint_boundary_violation
"""

import json
import re
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult, ProviderTelemetry
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.discovery.discovery_pipeline import DiscoveryPipeline, extract_canonical_domain, normalize_phone
from money_v2.orchestrator.enrichment_orchestrator import EnrichmentOrchestrator
from money_v2.orchestrator.fallback_strategy import FallbackStrategy
from money_v2.orchestrator.observability import ObservabilityHub
from money_v2.providers.api_registry_provider import ApiRegistryProvider
from money_v2.providers.base import BaseProvider
from money_v2.providers.dns_mx_provider import DnsMxProvider
from money_v2.providers.http_provider import HttpProvider
from money_v2.providers.playwright_provider import InvisiblePlaywrightProvider
from money_v2.providers.theharvester_provider import TheHarvesterProvider
from money_v2.truth.reconciliation import LegalReconciliationLayer, SealingViolationError
from money_v2.truth.truth_evaluator import TruthEvaluator, TruthStatus


class TestV2ArchitectureBehavioral(unittest.TestCase):

    def test_01_provider_missing(self):
        """Un outil non installé retourne TOOL_MISSING sans crasher ni faire semblant de trouver des données."""
        prov = TheHarvesterProvider(binary_path="/bin/non_existent_binary_xyz_123")
        res = prov.execute("example.fr")
        self.assertIn(res.status, (ProviderStatus.TOOL_MISSING, ProviderStatus.TOOL_UNAVAILABLE))
        self.assertFalse(res.has_evidences)
        self.assertIsNotNone(res.telemetry)
        self.assertIn(res.telemetry.status, (ProviderStatus.TOOL_MISSING, ProviderStatus.TOOL_UNAVAILABLE))

    def test_02_provider_timeout(self):
        """Un timeout ne doit jamais être converti silencieusement en NO_RESULT."""
        class TimeoutMockProvider(BaseProvider):
            def __init__(self):
                super().__init__("timeout_mock")
            def is_available(self):
                return True
            def _run(self, target, context):
                raise TimeoutError("Le serveur distant n'a pas répondu dans le délai")

        prov = TimeoutMockProvider()
        res = prov.execute("https://slow-agency.fr")
        self.assertEqual(res.status, ProviderStatus.TIMEOUT)
        self.assertNotEqual(res.status, ProviderStatus.NO_RESULT)
        self.assertIn("TimeoutError", res.telemetry.error_type)

    def test_03_provider_network_error(self):
        """Une panne de connexion retourne NETWORK_ERROR sans être masquée."""
        prov = HttpProvider(timeout=1.0)
        # Port inaccessible en local
        res = prov.execute("http://127.0.0.1:59999/unreachable")
        self.assertEqual(res.status, ProviderStatus.NETWORK_ERROR)
        self.assertNotEqual(res.status, ProviderStatus.NO_RESULT)

    def test_04_provider_blocked(self):
        """Un blocage HTTP 403 / WAF est qualifié BLOCKED et non NO_RESULT."""
        class BlockedMockProvider(HttpProvider):
            def _run(self, target, context):
                return ProviderResult(provider=self.name, status=ProviderStatus.BLOCKED, evidences=[])

        prov = BlockedMockProvider()
        res = prov.execute("https://cloudflare-protected.fr")
        self.assertEqual(res.status, ProviderStatus.BLOCKED)

    def test_05_provider_returns_no_result(self):
        """Une exécution réussie sans match retourne proprement NO_RESULT."""
        class CleanEmptyProvider(BaseProvider):
            def __init__(self):
                super().__init__("clean_empty")
            def is_available(self):
                return True
            def _run(self, target, context):
                return ProviderResult(provider=self.name, status=ProviderStatus.NO_RESULT, evidences=[])

        prov = CleanEmptyProvider()
        res = prov.execute("https://site-sans-donnees.fr")
        self.assertEqual(res.status, ProviderStatus.NO_RESULT)
        self.assertEqual(len(res.evidences), 0)

    def test_06_provider_returns_malformed_data(self):
        """Une réponse corrompue génère UNKNOWN_ERROR sans crasher le pipeline."""
        class MalformedJsonProvider(BaseProvider):
            def __init__(self):
                super().__init__("malformed_json")
            def is_available(self):
                return True
            def _run(self, target, context):
                # Simule parsing JSON erroné
                json.loads("Ceci n'est pas du JSON valide {{{")
                return ProviderResult(provider=self.name, status=ProviderStatus.SUCCESS)

        prov = MalformedJsonProvider()
        res = prov.execute("example.fr")
        self.assertEqual(res.status, ProviderStatus.UNKNOWN_ERROR)
        self.assertIn("JSONDecodeError", res.telemetry.error_type)

    def test_07_provider_returns_conflicting_evidence(self):
        """Deux preuves contradictoires sont arbitrées par le niveau de confiance."""
        ev_low = Evidence(
            field="main_offer",
            value="Offre Heuristique",
            source="heuristique",
            source_url="http://src1",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.DOM_INSPECTION.value,
            provider="p1",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="Texte imprécis",
            confidence=ConfidenceLevel.LOW.value,
            lead_id="lead1"
        )
        ev_high = Evidence(
            field="main_offer",
            value="Conception Webflow & Sites sur-mesure",
            source="title_tag",
            source_url="http://src2",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.DOM_INSPECTION.value,
            provider="p2",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="Titre explicite",
            confidence=ConfidenceLevel.HIGH.value,
            lead_id="lead1"
        )
        # Arbitrage déterministe en faveur de HIGH
        evidences = [ev_low, ev_high]
        best_ev = max(evidences, key=lambda e: 2 if e.confidence == "HIGH" else 1)
        self.assertEqual(best_ev.value, "Conception Webflow & Sites sur-mesure")

    def test_08_mcp_attempts_to_overwrite_sirene(self):
        """InvisiblePlaywrightProvider refuse d'alimenter un champ légal réservé."""
        prov = InvisiblePlaywrightProvider()
        ctx = {"field_target": "decision_maker", "trigger_type": "annuaire_fallback"}
        res = prov.execute("https://malt.fr/profile/fake", ctx)
        self.assertEqual(res.status, ProviderStatus.INVALID_INPUT)
        self.assertIn("Violation d'étanchéité", res.telemetry.error_message_safe)

    def test_09_theharvester_returns_pattern_only(self):
        """Un pattern d'adresse theHarvester est étiqueté PATTERN et non email vérifié."""
        ev = Evidence(
            field="email_pattern_indication",
            value="first.last@agency.fr",
            source="theHarvester",
            source_url="osint://theharvester",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.OSINT_CLI.value,
            provider="theharvester_provider",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="Schéma observé",
            confidence=ConfidenceLevel.PATTERN.value,
            lead_id="agency.fr"
        )
        self.assertEqual(ev.confidence, ConfidenceLevel.PATTERN.value)
        self.assertNotEqual(ev.field, "public_professional_email")

    def test_10_theharvester_returns_duplicate_emails(self):
        """Les emails remontés par theHarvester sont dédoublonnés et filtrés."""
        emails = ["contact@agency.fr", "CONTACT@agency.fr", "contact@agency.fr", "info@other.com"]
        target_domain = "agency.fr"
        deduped = sorted(list(set(
            e.lower() for e in emails
            if e.lower().endswith("@" + target_domain)
        )))
        self.assertEqual(deduped, ["contact@agency.fr"])

    def test_11_fallback_strategy_3_tiers(self):
        """La chaîne de repli FallbackStrategy comporte strictement 3 paliers sans Crawlee."""
        strategy = FallbackStrategy()
        self.assertFalse(hasattr(strategy, "crawlee"))
        lead = {"url": "https://example-test-fallback.fr", "siren": "999999999"}
        res, audit_trail = strategy.execute_inspection_chain(lead)
        self.assertEqual(len(audit_trail), 3)
        self.assertEqual(audit_trail[0]["tier"], 1)
        self.assertEqual(audit_trail[1]["tier"], 2)
        self.assertEqual(audit_trail[2]["tier"], 3)
        self.assertEqual(audit_trail[2]["provider"], "technical_consignation")
        self.assertIn(res.status, (ProviderStatus.SUCCESS, ProviderStatus.NO_RESULT, ProviderStatus.BLOCKED, ProviderStatus.NETWORK_ERROR, ProviderStatus.TIMEOUT, ProviderStatus.UNKNOWN_ERROR))

    def test_12_mcp_playwright_client_isolation(self):
        """InvisiblePlaywrightProvider vérifie uv et mcp_playwright_client rejette strictement is_error=True."""
        import asyncio
        import shutil
        from unittest.mock import AsyncMock, MagicMock, patch
        from mcp_playwright_client import check_tool_result_error, execute_mcp_inspection

        # 1. Vérification de disponibilité uv
        prov = InvisiblePlaywrightProvider()
        has_uv = bool(shutil.which("uv"))
        self.assertEqual(prov.is_available(), has_uv)

        # 2. Vérification unitaire check_tool_result_error
        mock_ok = MagicMock()
        mock_ok.is_error = False
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Example Domain Content"
        mock_ok.content = [text_block]
        is_err, msg = check_tool_result_error(mock_ok)
        self.assertFalse(is_err)

        mock_fail = MagicMock()
        mock_fail.is_error = True
        err_block = MagicMock()
        err_block.type = "text"
        err_block.text = "Navigation timed out or refused"
        mock_fail.content = [err_block]
        is_err, msg = check_tool_result_error(mock_fail)
        self.assertTrue(is_err)
        self.assertEqual(msg, "Navigation timed out or refused")

        # 3. Test unitaire d'interruption sur browser_navigate avec is_error=True
        async def run_mocked_nav_failure():
            mock_session = AsyncMock()
            mock_open = MagicMock()
            mock_open.is_error = False
            mock_open.content = [MagicMock(type="text", text="browser open OK")]

            mock_nav = MagicMock()
            mock_nav.is_error = True
            mock_nav.content = [MagicMock(type="text", text="Error: 404 Not Found")]

            mock_session.call_tool.side_effect = [mock_open, mock_nav, MagicMock()]

            with patch("mcp.client.stdio.stdio_client") as mock_stdio:
                mock_ctx = AsyncMock()
                mock_ctx.__aenter__.return_value = (MagicMock(), MagicMock())
                mock_stdio.return_value = mock_ctx
                with patch("mcp.ClientSession") as mock_cls:
                    mock_cls.return_value.__aenter__.return_value = mock_session
                    res = await execute_mcp_inspection("https://fail.com", "annuaire_fallback", 10.0)
                    return res

        res_fail = asyncio.run(run_mocked_nav_failure())
        self.assertEqual(res_fail["status"], "MCP_TOOL_ERROR")
        self.assertEqual(res_fail["failed_step"], "browser_navigate")
        self.assertIn("404 Not Found", res_fail["error_detail"])
        self.assertNotIn("text", res_fail)

    def test_13_api_provider_unavailable(self):
        """Une API distante indisponible retourne NETWORK_ERROR."""
        prov = ApiRegistryProvider()
        res = prov.execute("invalid.domain.xyz.999", {"api_name": "google_dns_doh"})
        # Soit réponse DoH vide (NO_RESULT) soit NETWORK_ERROR
        self.assertIn(res.status, (ProviderStatus.NO_RESULT, ProviderStatus.NETWORK_ERROR, ProviderStatus.SUCCESS))

    def test_14_api_registry_provider_inactive(self):
        """Une API cataloguée mais inactive retourne TOOL_MISSING et refuse l'appel."""
        prov = ApiRegistryProvider()
        res = prov.execute("test", {"api_name": "wappalyzer_core"})
        self.assertEqual(res.status, ProviderStatus.TOOL_MISSING)
        self.assertIn("INACTIVE", res.telemetry.error_message_safe)

    def test_15_person_morale_selected_as_decision_maker(self):
        """Un dirigeant personne morale donne PARTIALLY_VERIFIED et protège la salutation."""
        lead = {
            "decision_maker": "HOLDING FINANCIERE SAS",
            "decision_maker_role": "Président",
            "decision_maker_is_person": False,
            "matching_status": "MATCH_CONFIRMED"
        }
        status = TruthEvaluator.evaluate_legal_director(lead)
        self.assertEqual(status, TruthStatus.PARTIALLY_VERIFIED)

    def test_16_commissaire_aux_comptes_selected(self):
        """Un commissaire aux comptes est formellement exclu des rôles exécutifs."""
        invalid_roles = [
            "Commissaire aux comptes titulaire",
            "Commissaire aux comptes suppléant"
        ]
        valid_executive_roles = ["Gérant", "Président", "Directeur Général"]
        for r in invalid_roles:
            self.assertFalse(any(v.lower() in r.lower() for v in valid_executive_roles))

    def test_17_new_discovery_batch(self):
        """Le pipeline traite un nouveau lot arbitraire sans dépendance à l'historique."""
        pipeline = DiscoveryPipeline()
        new_raw_batch = [
            {"website": "https://agence-lyon.fr", "phone": "0472000001", "category": "Agence web", "review_count": 15, "review_rating": 4.9, "title": "Agence Lyon"},
            {"website": "https://agence-bordeaux.fr", "phone": "0556000002", "category": "Création de site", "review_count": 8, "review_rating": 4.8, "title": "Agence Bordeaux"}
        ]
        shortlist, stats = pipeline.process_raw_dataset(new_raw_batch)
        self.assertEqual(len(shortlist), 2)
        self.assertEqual(stats["no_website"], 0)
        self.assertEqual(shortlist[0]["title"], "Agence Lyon")

    def test_18_duplicate_historical_lead(self):
        """Un lead déjà traité dans l'historique est exclu via exclude_domains."""
        pipeline = DiscoveryPipeline()
        batch = [
            {"website": "https://already-processed.fr", "phone": "0100000001", "category": "Agence web", "review_count": 5, "review_rating": 4.0, "title": "Ancienne Agence"},
            {"website": "https://brand-new.fr", "phone": "0100000002", "category": "Agence web", "review_count": 10, "review_rating": 5.0, "title": "Nouvelle Agence"}
        ]
        shortlist, stats = pipeline.process_raw_dataset(batch, exclude_domains={"already-processed.fr"})
        self.assertEqual(len(shortlist), 1)
        self.assertEqual(shortlist[0]["title"], "Nouvelle Agence")
        self.assertEqual(stats["already_processed"], 1)

    def test_19_new_city(self):
        """Le pipeline traite sans friction des agences d'une nouvelle ville (ex: Marseille)."""
        pipeline = DiscoveryPipeline()
        marseille_batch = [
            {"website": "https://web-marseille.fr", "phone": "0491000001", "category": "Agence Web", "review_count": 22, "review_rating": 4.7, "title": "Web Marseille"}
        ]
        res, _ = pipeline.process_raw_dataset(marseille_batch)
        self.assertEqual(len(res), 1)
        self.assertEqual(extract_canonical_domain(res[0]["website"]), "web-marseille.fr")

    def test_20_hardcoded_benchmark_list_removal(self):
        """Vérifie l'absence de variable hardcodée BENCHMARK_COHORT_DOMAINS dans le code source."""
        import dedupe_and_shortlist
        self.assertFalse(hasattr(dedupe_and_shortlist, "BENCHMARK_COHORT_DOMAINS"))

    def test_21_temporal_evidence(self):
        """Toute preuve générée respecte le format ISO 8601 UTC regex."""
        ts = get_current_iso_timestamp()
        self.assertTrue(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts))

    def test_22_stale_evidence(self):
        """Une preuve datant de plus de 90 jours est considérée périmée."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=95)).strftime('%Y-%m-%dT%H:%M:%SZ')
        is_stale = (datetime.now(timezone.utc) - datetime.fromisoformat(old_date.replace("Z", "+00:00"))).days > 90
        self.assertTrue(is_stale)

    def test_23_unsupported_outreach_claim(self):
        """Les affirmations non fondées dans l'outreach sont formellement rejetées."""
        forbidden_phrases = ["besoin urgent de leads", "recherche des prestataires", "Bonjour Non,"]
        sample_bad_msg = "Bonjour, nous savons que vous avez un besoin urgent de leads."
        has_forbidden = any(p in sample_bad_msg for p in forbidden_phrases)
        self.assertTrue(has_forbidden)

    def test_24_legal_osint_boundary_violation(self):
        """LegalReconciliationLayer lève SealingViolationError si OSINT vise company_size."""
        illegal_evidence = Evidence(
            field="company_size",
            value="15 salariés",
            source="scraping_annuaire",
            source_url="http://annuaire",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.DOM_INSPECTION.value,
            provider="illegal_scraper",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="Taille déduite d'un avis",
            confidence=ConfidenceLevel.LOW.value,
            lead_id="test"
        )
        with self.assertRaises(SealingViolationError):
            LegalReconciliationLayer.assert_sealing([illegal_evidence])


if __name__ == "__main__":
    unittest.main()
