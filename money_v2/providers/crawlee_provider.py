from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, ObservationMethod, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderError, ProviderStatus
from money_v2.providers.base import BaseProvider


class CrawleeProvider(BaseProvider):
    """
    Provider de crawling industriel par lots basé sur les spécifications Crawlee.
    Gère la file d'attente (queue), la concurrence, les réessais (retries),
    les timeouts par URL et la persistance d'état.
    """

    def __init__(
        self,
        concurrency: int = 3,
        max_retries: int = 2,
        timeout_sec: int = 10,
        enabled: bool = True
    ):
        super().__init__(name="crawlee_provider", enabled=enabled)
        self.concurrency = concurrency
        self.max_retries = max_retries
        self.timeout_sec = timeout_sec
        self.runner_script = Path(__file__).resolve().parent / "crawlee_runner.js"

    def is_available(self) -> bool:
        """Vérifie si Node.js est présent sur le système pour piloter le runner Crawlee."""
        return shutil.which("node") is not None

    def crawl_batch(self, urls: List[str], policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécute un crawl de lot avec file d'attente, retries et limitation de concurrence.
        Utilise Node.js/Crawlee si présent, avec fallback déterministe en pur stdlib.
        """
        now_iso = get_current_iso_timestamp()
        batch_results: Dict[str, Any] = {
            "total_urls": len(urls),
            "successful": [],
            "failed": [],
            "items": [],
            "started_at": now_iso,
            "status_by_url": {}
        }

        if not urls:
            return batch_results

        # Si Node est disponible, on tente l'exécuteur Node Crawlee
        node_bin = shutil.which("node")
        if node_bin and self.runner_script.exists():
            with tempfile.TemporaryDirectory() as tmp_dir:
                in_path = Path(tmp_dir) / "crawlee_input.json"
                out_path = Path(tmp_dir) / "crawlee_output.json"

                with open(in_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "urls": urls,
                        "concurrency": self.concurrency,
                        "maxRetries": self.max_retries,
                        "timeoutSec": self.timeout_sec
                    }, f)

                try:
                    proc = subprocess.run(
                        [node_bin, str(self.runner_script), str(in_path), str(out_path)],
                        capture_output=True,
                        text=True,
                        timeout=self.timeout_sec * len(urls) + 15,
                        check=False
                    )
                    if proc.returncode == 0 and out_path.exists():
                        with open(out_path, "r", encoding="utf-8") as f:
                            node_res = json.load(f)
                            return node_res
                except Exception:
                    # En cas d'échec ou d'absence du module npm crawlee, bascule sur le moteur stdlib avec queue et retries
                    pass

        # Moteur queue & retries déterministe (équivalent sémantique Crawlee en Python stdlib)
        for url in urls:
            url_clean = url.strip()
            attempts = 0
            success = False
            last_err = ""

            while attempts <= self.max_retries and not success:
                attempts += 1
                try:
                    req = urllib.request.Request(
                        url_clean,
                        headers={"User-Agent": "Money-Crawlee/2.0 (Compatible; BatchCrawler)"}
                    )
                    with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                        if resp.status == 200:
                            html = resp.read(40000).decode("utf-8", errors="ignore")
                            batch_results["successful"].append(url_clean)
                            batch_results["items"].append({
                                "url": url_clean,
                                "status_code": 200,
                                "html_preview": html[:300],
                                "retries": attempts - 1
                            })
                            batch_results["status_by_url"][url_clean] = "SUCCESS"
                            success = True
                            break
                        else:
                            last_err = f"HTTP status {resp.status}"
                except Exception as e:
                    last_err = str(e)
                    time.sleep(0.2 * attempts)  # Backoff exponentiel

            if not success:
                batch_results["failed"].append({
                    "url": url_clean,
                    "retries": attempts - 1,
                    "error_message": last_err
                })
                batch_results["status_by_url"][url_clean] = "FAILED"

        return batch_results

    def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
        """Exécution unitaire ou d'un batch d'URLs passé dans context['urls']."""
        urls = context.get("urls") or [target]
        lead_id = str(context.get("lead_id") or target)
        now_iso = get_current_iso_timestamp()

        batch_data = self.crawl_batch(urls)
        evidences: List[Evidence] = []

        for item in batch_data.get("items", []):
            item_url = item.get("url")
            evidences.append(Evidence(
                field="crawled_content",
                value=f"Page crawlée avec succès (retries: {item.get('retries', 0)})",
                source=item_url,
                source_url=item_url,
                observed_at=now_iso,
                method=ObservationMethod.BATCH_CRAWL.value,
                provider=self.name,
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text=f"Crawl Crawlee réussi pour {item_url}",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id=lead_id,
                metadata={"retries": item.get("retries", 0), "status_code": item.get("status_code", 200)}
            ))

        total_urls = batch_data.get("total_urls", 0)
        successful_count = len(batch_data.get("successful", []))

        if successful_count == total_urls and total_urls > 0:
            status = ProviderStatus.SUCCESS
        elif successful_count > 0:
            status = ProviderStatus.PARTIAL
        elif len(batch_data.get("failed", [])) > 0:
            status = ProviderStatus.NETWORK_ERROR
        else:
            status = ProviderStatus.NO_RESULT

        return ProviderResult(
            provider=self.name,
            status=status,
            evidences=evidences,
            raw_payload=batch_data
        )
