#!/usr/bin/env python3
"""
mcp_playwright_client.py — Client MCP Stdio Dédié pour invisible-playwright-mcp.

Exécuté de manière isolée en subprocess :
`uv run --with mcp --python 3.11 python3 mcp_playwright_client.py <args>`

Rôle :
- Établit la connexion stdio avec le vrai serveur MCP `uvx invisible-playwright-mcp`.
- Appelle les outils réels (`browser_navigate`, `browser_read_text`, `browser_snapshot`, `browser_close`).
- Applique les garde-fous stricts :
  * FORBIDDEN_FIELDS (aucune corruption de l'identité légale SIRENE Niveau 1/2).
  * ADR-008 (quota journalier et exigence MATCH_CONFIRMED pour consultation LinkedIn).
- Restitue un JSON structuré et auditable sur stdout.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

FORBIDDEN_FIELDS = {
    "siren",
    "company_name",
    "legal_status",
    "company_size",
    "company_size_code",
    "decision_maker",
    "decision_maker_role",
    "decision_maker_is_person",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Client MCP pour invisible-playwright-mcp")
    parser.add_argument("--url", required=True, help="URL cible à inspecter")
    parser.add_argument("--trigger-type", default="annuaire_fallback", help="Type de déclenchement (annuaire_fallback, linkedin_consultation, etc.)")
    parser.add_argument("--field-target", default="main_offer", help="Champ ciblé par l'inspection")
    parser.add_argument("--matching-status", default="", help="Statut SIRENE pour consultation LinkedIn")
    parser.add_argument("--daily-count", type=int, default=0, help="Nombre de consultations déjà effectuées ce jour (ADR-008)")
    parser.add_argument("--timeout-sec", type=float, default=25.0, help="Timeout global en secondes")
    return parser.parse_args()


async def execute_mcp_inspection(
    url: str,
    trigger_type: str,
    timeout_sec: float
) -> Dict[str, Any]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = os.environ.copy()
    env["INVPW_TRUE_HEADLESS"] = "1"
    server_params = StdioServerParameters(
        command="uvx",
        args=["invisible-playwright-mcp"],
        env=env
    )

    result_payload: Dict[str, Any] = {
        "status": "SUCCESS",
        "url": url,
        "title": "",
        "text": "",
        "has_recent_activity": False,
        "extracted_emails": [],
        "offer_clues": [],
        "mcp_tools_used": []
    }

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 1. Ouverture du navigateur furtif Firefox
            await session.call_tool("browser_open", arguments={"browser": "main"})
            result_payload["mcp_tools_used"].append("browser_open")

            try:
                # 2. Navigation furtive
                nav_args = {"url": url, "wait_until": "domcontentloaded", "browser": "main"}
                await session.call_tool("browser_navigate", arguments=nav_args)
                result_payload["mcp_tools_used"].append("browser_navigate")

                # 3. Lecture du texte visible de la page
                read_args = {"selector": "body", "max_chars": 6000, "browser": "main"}
                read_res = await session.call_tool("browser_read_text", arguments=read_args)
                result_payload["mcp_tools_used"].append("browser_read_text")

                page_text = ""
                if read_res and read_res.content:
                    for block in read_res.content:
                        if getattr(block, "type", "") == "text":
                            page_text += block.text

                result_payload["text"] = page_text

                # 4. Snapshot (structure interactive et titre)
                try:
                    snap_res = await session.call_tool("browser_snapshot", arguments={"browser": "main"})
                    result_payload["mcp_tools_used"].append("browser_snapshot")
                    if snap_res and snap_res.content:
                        for block in snap_res.content:
                            if getattr(block, "type", "") == "text":
                                match_title = re.search(r"Title:\s*(.+)", block.text)
                                if match_title:
                                    result_payload["title"] = match_title.group(1).strip()
                except Exception:
                    pass

            finally:
                # 5. Fermeture propre et garantie du navigateur
                try:
                    await session.call_tool("browser_close", arguments={"browser": "main"})
                    result_payload["mcp_tools_used"].append("browser_close")
                except Exception:
                    pass

            # Analyse spécifique selon trigger_type
            if trigger_type == "linkedin_consultation":
                has_activity = bool(re.search(r"(activité|posts|articles|publications|expérience|fondateur)", page_text, re.IGNORECASE))
                result_payload["has_recent_activity"] = has_activity
            else:
                # Extraction emails et indices d'offres
                email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
                emails = list(set(email_regex.findall(page_text)))
                result_payload["extracted_emails"] = emails

                for kw in ["création de site", "développement web", "webflow", "wordpress", "shopify", "seo", "refonte"]:
                    if kw in page_text.lower():
                        result_payload["offer_clues"].append(kw)

    return result_payload


def main() -> None:
    args = parse_args()

    # Contrôle de sécurité Niveau 1/2
    if args.field_target in FORBIDDEN_FIELDS:
        print(json.dumps({
            "status": "FORBIDDEN_FIELD_VIOLATION",
            "error": f"Interdiction formelle d'alimenter le champ légal réservé '{args.field_target}' via invisible_playwright_mcp"
        }), file=sys.stderr)
        sys.exit(2)

    # Contrôle ADR-008
    if args.trigger_type == "linkedin_consultation":
        if args.matching_status != "MATCH_CONFIRMED":
            print(json.dumps({
                "status": "BLOCKED",
                "error": f"ADR-008 : consultation LinkedIn refusée car matching = '{args.matching_status}' (!= MATCH_CONFIRMED)"
            }))
            sys.exit(0)
        if args.daily_count >= 5:
            print(json.dumps({
                "status": "RATE_LIMITED",
                "error": f"ADR-008 : quota quotidien atteint ({args.daily_count}/5)"
            }))
            sys.exit(0)

    try:
        payload = asyncio.run(
            asyncio.wait_for(
                execute_mcp_inspection(
                    url=args.url,
                    trigger_type=args.trigger_type,
                    timeout_sec=args.timeout_sec
                ),
                timeout=args.timeout_sec
            )
        )
        print(json.dumps(payload, ensure_ascii=False))
    except asyncio.TimeoutError:
        print(json.dumps({
            "status": "TIMEOUT",
            "error": f"Délai d'exécution dépassé ({args.timeout_sec}s) sur {args.url}"
        }))
        sys.exit(0)
    except Exception as e:
        err_msg = str(e)
        status = "NETWORK_ERROR"
        if "403" in err_msg or "blocked" in err_msg.lower() or "challenge" in err_msg.lower():
            status = "BLOCKED"
        print(json.dumps({
            "status": status,
            "error": err_msg
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
