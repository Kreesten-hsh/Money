import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def get_current_iso_timestamp() -> str:
    """Génère dynamiquement un horodatage ISO 8601 UTC réel sans date hardcodée."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def generate_lead_intelligence_markdown():
    input_file = BASE_DIR / 'data' / 'top30_leads_requalified.json'
    with open(input_file, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    # Statistiques réelles
    total = len(leads)
    verified = [l for l in leads if l['verification_status'] == 'VERIFIED']
    partially = [l for l in leads if l['verification_status'] == 'PARTIALLY VERIFIED']
    requires_review = [l for l in leads if l['verification_status'] == 'REQUIRES REVIEW']
    disqualified = [l for l in leads if l['verification_status'] == 'DISQUALIFIED']

    # Trier les vérifiés par lead_gen_score descendant puis confidence_score
    verified.sort(key=lambda x: (x['lead_gen_score'], x['confidence_score']), reverse=True)

    generation_date = get_current_iso_timestamp()

    md = []
    md.append('# 🎯 Lead Intelligence Room — Agences Web France')
    md.append('')
    md.append('> **Campagne** : AI Lead Intelligence & Founder Ghostwriting (MVP)  ')
    md.append(f"> **Dernière mise à jour** : {generation_date} (Audit Déterminisme SIRENE & Preuves Séparées)  ")
    md.append('> **Statut** : Registres Publics (INSEE / SIRENE) + Matching Multi-Critères + Contrôle HTTP  ')
    md.append(f"> **Données consolidées** : {len(verified)} vérifiées | {len(partially)} partiellement vérifiées | {len(requires_review)} à auditer | {len(disqualified)} disqualifiées")
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 01 — Campaign Overview')
    md.append('')
    md.append('Cette Lead Intelligence Room documente le lot audité d\'agences web françaises de 2 à 20 collaborateurs, conformément aux standards de vérité stricts du projet Money (zéro hallucination, preuves traçables, détection d\'incohérences).')
    md.append('')
    md.append('### Métriques Clés Consolidées')
    md.append(f"- **Volume total analysé** : {total} entreprises issues de la shortlist dédupliquée.")
    md.append(f"- **Entités confirmées dans l'ICP (VERIFIED)** : **{len(verified)} agences** (SIREN actif, effectif vérifié 2 à 20 personnes avec double preuve pour tranche 01, dirigeant légal officiel vérifié, matching confirmé sans ambiguïté, site HTTPS accessible).")
    md.append(f"- **Entités partiellement vérifiées (PARTIALLY VERIFIED)** : **{len(partially)} agence** (immatriculation active mais données d'effectif partielles ou discordantes).")
    md.append(f"- **Entités en révision (REQUIRES REVIEW)** : **{len(requires_review)} agences** (homonymie, ambiguïté concurrentielle SIRENE avec delta < 20, ou site web sous-domaine/inaccessible).")
    md.append(f"- **Entités disqualifiées (DISQUALIFIED)** : **{len(disqualified)} agences** (non employeur tranche NN/00, cessation d'activité ou effectif hors cible >20).")
    md.append('- **Objectif financier** : 1 000 000 FCFA encaissés avant le 31 décembre 2026 via 2 à 3 pilotes payants.')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 02 — ICP & Criteria')
    md.append('')
    md.append('### Critères d\'Éligibilité Appliqués')
    md.append('1. **Statut Légal & Immatriculation** : Établissement actif au registre national SIRENE / INSEE.')
    md.append('2. **Matching SIRENE Déterministe & Détection d\'Ambiguïté** :')
    md.append('   - `MATCH_CONFIRMED` : Concordance nom, code postal strict, voie et NAF (score >= 75) avec delta >= 20 vis-à-vis du 2ème candidat.')
    md.append('   - `MATCH_UNCERTAIN` : Dès qu\'un 2ème candidat concurrent est proche (score >= 55 et delta < 20) ou informations insuffisantes.')
    md.append('3. **Tranche d\'Effectif Réelle (2 à 20 personnes)** :')
    md.append('   - Tranches INSEE `02` (3-5), `03` (6-9), `11` (10-19) admises.')
    md.append('   - Tranche INSEE `01` (1 ou 2 salariés) : Admise uniquement avec preuve secondaire publique (co-gérance / multiples dirigeants au greffe prouvant >= 2 personnes). Sans cette preuve, maintien en `REQUIRES REVIEW`.')
    md.append('   - Tranches `NN` et `00` (non employeur / 0 salarié) : Disqualifiées d\'office.')
    md.append('4. **Scores Découplés & Justifiés** :')
    md.append('   - `Lead Gen Score` (0–100) : Activité (30), Taille (25), Signal commercial (25), Traction (20). En Phase 1, faute de signal d\'affaires externe vérifié, le signal commercial est à 0 (pénalité de 25 points documentée, score max effectif = 75/100).')
    md.append('   - `Ghostwriting Score` (0–100) : Neutralisé à 0/100 en Phase 1 (aucun audit LinkedIn public conduit, refus des heuristiques artificielles).')
    md.append('   - `Confidence Score` (0–100) : Solidité des preuves (plafonné à 60 si non VERIFIED, 40 si matching incertain).')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 03 — Qualified Leads (Lot Requalifié des 30)')
    md.append('')
    md.append('| # | Entreprise | Ville | SIREN | Effectif Officiel | Dirigeant Légal (Rôle Officiel) | Matching | Scores (LG / GW / Conf) | Statut |')
    md.append('|---|---|---|---|---|---|---|---|---|')

    ordered_leads = verified + partially + requires_review + disqualified

    for idx, l in enumerate(ordered_leads, 1):
        clean_name = l['brand_name'].split('|')[0].strip()
        dirigeant = l['decision_maker'].split('(')[0].strip()
        role = l.get('decision_maker_role', '')
        dm_display = f"{dirigeant} ({role})" if role and role != 'Inconnu' else dirigeant
        scores = f"`{l['lead_gen_score']}` / `{l['ghostwriting_score']}` / `{l['confidence_score']}`"
        status_badge = {
            'VERIFIED': '✅ VERIFIED',
            'PARTIALLY VERIFIED': '🟡 PARTIALLY',
            'REQUIRES REVIEW': '🔍 REVIEW',
            'DISQUALIFIED': '❌ DISQUALIFIED'
        }.get(l['verification_status'], l['verification_status'])
        
        md.append(f"| {idx:02d} | **{clean_name}** | {l['city']} | `{l['siren']}` | {l['company_size']} | {dm_display} | `{l['matching_status']}` | {scores} | {status_badge} |")

    md.append('')
    md.append('---')
    md.append('')
    md.append('## 04 — Priority Leads (Top 5 Réellement Vérifiés & Sans Ambiguïté)')
    md.append('')

    # Sélection dynamique des 5 premiers leads VERIFIED ayant un MATCH_CONFIRMED
    eligible_top = [l for l in verified if l.get('matching_status') == 'MATCH_CONFIRMED']
    top5 = eligible_top[:5]

    for idx, p in enumerate(top5, 1):
        clean_name = p['brand_name'].split('|')[0].strip()
        dirigeant = p['decision_maker'].split('(')[0].strip()
        role = p.get('decision_maker_role', 'Dirigeant légal')
        
        md.append(f"### {idx:02d} — {clean_name} ({p['city']})")
        md.append(f"- **Raison Sociale / SIREN** : {p['company_name']} | SIREN `{p['siren']}` (Source : [{p['siren_source']}]({p['evidence_url']}))")
        md.append(f"- **Site Web** : [{p['website']}]({p['website']}) | **Téléphone Direct** : `{p['public_phone']}`")
        md.append(f"- **Taille Officielle (INSEE)** : **{p['company_size']}** ({p['company_size_interpretation']})")
        if p.get('has_secondary_size_proof') and p.get('secondary_size_proof_details'):
            md.append(f"  - *Preuve d'effectif vérifiée* : {p['secondary_size_proof_details']}")
        md.append(f"- **Dirigeant Identifié** : **{dirigeant}** ({role}) (Source : [{p['decision_maker_source']}]({p['decision_maker_source']}))")
        md.append(f"- **Matching SIRENE Déterministe** : `{p['matching_status']}` (Score candidat: {p['sirene_candidate_score']}/100 | Delta 2ème candidat: {p['sirene_score_delta']} | {p['sirene_matching_decision_reason']})")
        md.append(f"- **Preuve de l'Offre Principale (`main_offer`)** :")
        md.append(f"  - Offre : **{p['main_offer']}**")
        md.append(f"  - Preuve : {p['main_offer_evidence']}")
        md.append(f"  - Source : [{p['main_offer_source']}]({p['main_offer_source']}) (vérifié le `{p['main_offer_checked_at']}`)")
        md.append(f"- **Preuve de la Clientèle Cible (`target_clients`)** :")
        md.append(f"  - Cible : **{p['target_clients']}**")
        md.append(f"  - Preuve : {p['target_clients_evidence']}")
        target_src_txt = f"[{p['target_clients_source']}]({p['target_clients_source']})" if p['target_clients_source'] else "Aucune source externe (non inféré)"
        md.append(f"  - Source : {target_src_txt} (vérifié le `{p['target_clients_checked_at']}`)")
        md.append(f"- **Évaluation des Scores** :")
        md.append(f"  - `Lead Gen Score` : **{p['lead_gen_score']}/100** (Plafond effectif 75/100 en Phase 1 : pénalité de 25 pts en l'absence de signal commercial externe vérifié)")
        md.append(f"  - `Ghostwriting Score` : **{p['ghostwriting_score']}/100** (Neutralisé — en attente d'audit éditorial direct)")
        md.append(f"  - `Confidence Score` : **{p['confidence_score']}/100** (Preuves légales, effectif, site HTTPS et canal direct vérifiés)")

        # Construction du message d'outreach conforme aux 4 principes stricts :
        # 1. Ce qu'on a observé
        # 2. Où on l'a observé
        # 3. Pourquoi cela a conduit à sélectionner l'entreprise
        # 4. Ce que nous proposons
        # Salutation : conditionnée strictement à decision_maker_is_person
        is_person = str(p.get('decision_maker_is_person', '')).lower() in ('true', '1')
        has_dirigeant = bool(dirigeant and not dirigeant.lower().startswith('non identifié') and dirigeant != 'Inconnu')

        if is_person and has_dirigeant:
            prenom = dirigeant.split()[0].title()
            salutation = f"Bonjour {prenom},"
        else:
            salutation = f"Bonjour l'équipe {clean_name},"

        if p.get('main_offer') and p['main_offer'] != 'Non vérifié':
            observation = f"J'ai pris connaissance de vos réalisations sur votre site ({p['website']}), qui met en avant votre activité en {p['main_offer'].lower()} à {p['city']}."
        else:
            observation = f"J'ai identifié votre agence ({p['website']}) implantée à {p['city']}."

        selection_reason = "Dans le cadre de l'initiative Money, nous sélectionnons des agences web régionales indépendantes de 2 à 20 collaborateurs afin de tester un protocole de qualification ciblée d'opportunités d'affaires."
        proposal = "Seriez-vous ouvert à un court échange afin de découvrir notre démarche et évaluer si ce format présente une pertinence pour votre développement ?"

        outreach_msg = f"{salutation} {observation} {selection_reason} {proposal}"

        md.append(f"- **Message d'Outreach Recommandé (Manuel & 100% Vérifiable)** :")
        md.append(f"> \"{outreach_msg}\"")
        md.append('')

    md.append('---')
    md.append('')
    md.append('## 05 — Outreach Queue & Cadencement Manuel')
    md.append('')
    md.append('1. **Approche 100% Manuelle** : Aucun outil d\'automatisation, aucun cold emailing massif, aucun scraping sauvage.')
    md.append('2. **Cibles Immédiates** : Uniquement les agences disposant du statut `VERIFIED` avec rapprochement `MATCH_CONFIRMED`.')
    md.append('3. **Cadencement** : 2 à 3 prises de contact personnalisées par jour après audit approfondi de chaque projet.')
    md.append('4. **Règle de Clarté Commerciale** : Aucune promesse non prouvée, aucune affirmation d\'urgence infondée.')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 06 — Market Signals & Analyse Terrain')
    md.append('')
    md.append('- **Divergence Enseigne Commerciale / Dénomination Juridique** : Plusieurs agences utilisent un nom commercial non déposé au RCS. La recherche SIRENE exige une validation croisée du code postal et du numéro de voie pour éviter les faux homonymes.')
    md.append('- **Détection des Ambiguïtés SIRENE** : L\'algorithme pénalise les résultats concurrents proches (delta score < 20), empêchant tout faux rapprochement arbitraire.')
    md.append('- **Effectifs Déclarés vs Effectifs Réels** : La tranche INSEE 01 (« 1 ou 2 salariés ») n\'est acceptée en `VERIFIED` qu\'en présence avérée d\'au moins deux personnes (co-dirigeants déclarés au greffe).')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 07 — Sources & Evidence (Traçabilité)')
    md.append('')
    md.append('- **Données Légales & Effectifs** : Registre national SIRENE via l\'API publique `recherche-entreprises.api.gouv.fr`.')
    md.append('- **Données Commerciales** : Google Maps Scraper (Docker local) dédupliqué et filtré par pôle urbain.')
    md.append('- **Audit des Offres & Sites** : Contrôle HTTP/HTTPS direct et inspection de contenu.')
    md.append('- **Datasets du Projet** :')
    md.append('  - `data/gmaps_agences_web_shortlist.csv`')
    md.append('  - `data/top30_leads_requalified.csv`')
    md.append('  - `data/top30_leads_requalified.json`')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 08 — Delivery History')
    md.append('')
    md.append('- **26/09/2026 (Audit Initial)** : Premier crawl et détection des failles méthodologiques.')
    md.append('- **26/09/2026 (Correction Commit db02a84)** : Ajout SIRENE initial et découplage.')
    md.append(f"- **{generation_date[:10]} (Refonte Preuves Métier & Ambiguïté SIRENE)** : Matching SIRENE avec détection d'ambiguïté (delta), séparation stricte offre/cible, preuves structurées, outreach vérifié et dates 100% dynamiques.")

    content = '\n'.join(md)
    output_file = BASE_DIR / 'data' / 'lead_intelligence_room.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Lead Intelligence Room générée avec succès : {len(content)} caractères.")
    return content

if __name__ == '__main__':
    generate_lead_intelligence_markdown()
