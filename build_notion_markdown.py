import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

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

    # Trier les vérifiés par lead_gen_score descendant
    verified.sort(key=lambda x: (x['lead_gen_score'], x['confidence_score'], x['ghostwriting_score']), reverse=True)

    md = []
    md.append('# 🎯 Lead Intelligence Room — Agences Web France')
    md.append('')
    md.append('> **Campagne** : AI Lead Intelligence & Founder Ghostwriting (MVP)  ')
    md.append('> **Dernière mise à jour** : 26 Septembre 2026 (Requalification Post-Audit)  ')
    md.append('> **Statut** : Échantillon Requalifié par les Registres Publics de l\'État (INSEE / SIRENE)  ')
    md.append(f"> **Données consolidées** : {len(verified)} vérifiées | {len(partially)} partiellement vérifiées | {len(requires_review)} à auditer | {len(disqualified)} disqualifiée")
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 01 — Campaign Overview')
    md.append('')
    md.append('Cette Lead Intelligence Room documente le premier lot audité d\'agences web françaises de 2 à 20 collaborateurs, conformément aux standards de vérité stricts du projet Money.')
    md.append('')
    md.append('### Métriques Clés Consolidées')
    md.append(f"- **Volume total analysé** : {total} entreprises.")
    md.append(f"- **Entités confirmées dans l'ICP (VERIFIED)** : **{len(verified)} agences** (SIREN actif, effectif salarié officiel de 1 à 19 salariés, dirigeant légal identifié).")
    md.append(f"- **Entités partiellement vérifiées (PARTIALLY VERIFIED)** : **{len(partially)} agences** (immatriculation active mais sans salarié déclaré ou effectif incertain).")
    md.append(f"- **Entités en révision (REQUIRES REVIEW)** : **{len(requires_review)} agences** (dénomination commerciale divergente du nom de société légale).")
    md.append(f"- **Entités disqualifiées (DISQUALIFIED)** : **{len(disqualified)} agence** (fermeture ou radiation au greffe).")
    md.append('- **Objectif financier** : 1 000 000 FCFA encaissés avant le 31 décembre 2026 via 2 à 3 pilotes payants.')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 02 — ICP & Criteria')
    md.append('')
    md.append('### Critères d\'Éligibilité Appliqués')
    md.append('1. **Statut Légal & Immatriculation** : Établissement actif au registre SIRENE / INSEE.')
    md.append('2. **Activité Cible** : Prestation de création/refonte de sites, SEO, acquisition digitale pour PME.')
    md.append('3. **Tranche d\'Effectif Réelle (2 à 20 salariés)** : Validée via la nomenclature officielle INSEE (codes 01, 02, 03, 11). Les avis Google ne sont plus utilisés pour inférer la taille.')
    md.append('4. **Scores Découplés** :')
    md.append('   - `Lead Gen Score` (0–100) : Potentiel d\'achat de leads B2B.')
    md.append('   - `Ghostwriting Score` (0–100) : Potentiel d\'accompagnement éditorial LinkedIn du dirigeant.')
    md.append('   - `Confidence Score` (0–100) : Solidité des preuves documentées (plafonné si données manquantes).')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 03 — Qualified Leads (Lot Requalifié des 30)')
    md.append('')
    md.append('| # | Entreprise | Ville | SIREN | Effectif Officiel | Dirigeant Légal | Scores (LG / GW / Conf) | Statut |')
    md.append('|---|---|---|---|---|---|---|---|')

    # Afficher d'abord les VERIFIED, puis les PARTIALLY, puis REQUIRES REVIEW, puis DISQUALIFIED
    ordered_leads = verified + partially + requires_review + disqualified

    for idx, l in enumerate(ordered_leads, 1):
        clean_name = l['brand_name'].split('|')[0].strip()
        dirigeant = l['decision_maker'].split('(')[0].strip()
        scores = f"`{l['lead_gen_score']}` / `{l['ghostwriting_score']}` / `{l['confidence_score']}`"
        status_badge = {
            'VERIFIED': '✅ VERIFIED',
            'PARTIALLY VERIFIED': '🟡 PARTIALLY',
            'REQUIRES REVIEW': '🔍 REVIEW',
            'DISQUALIFIED': '❌ DISQUALIFIED'
        }.get(l['verification_status'], l['verification_status'])
        
        md.append(f"| {idx:02d} | **{clean_name}** | {l['city']} | `{l['siren']}` | {l['company_size']} | {dirigeant} | {scores} | {status_badge} |")

    md.append('')
    md.append('---')
    md.append('')
    md.append('## 04 — Priority Leads (Top 5 Réellement Vérifiés)')
    md.append('')

    # Génération dynamique des 5 premiers leads VERIFIED
    top5 = verified[:5]
    for idx, p in enumerate(top5, 1):
        clean_name = p['brand_name'].split('|')[0].strip()
        dirigeant = p['decision_maker'].split('(')[0].strip()
        md.append(f"### {idx:02d} — {clean_name} ({p['city']})")
        md.append(f"- **Raison Sociale / SIREN** : {p['company_name']} | SIREN `{p['siren']}`")
        md.append(f"- **Site Web** : [{p['website']}]({p['website']}) | **Téléphone Direct** : `{p['public_phone']}`")
        md.append(f"- **Taille Officielle (INSEE)** : **{p['company_size']}** (Source : [{p['company_size_source']}]({p['evidence_url']}))")
        md.append(f"- **Dirigeant Identifié** : **{dirigeant}** ({p['decision_maker_role']})")
        md.append(f"- **Évaluation des Scores** :")
        md.append(f"  - `Lead Gen Score` : **{p['lead_gen_score']}/100**")
        md.append(f"  - `Ghostwriting Score` : **{p['ghostwriting_score']}/100**")
        md.append(f"  - `Confidence Score` : **{p['confidence_score']}/100**")
        signal_desc = p.get('commercial_signal') or "Aucun signal d'affaires récent détecté (audit manuel requis)"
        md.append(f"- **Signal Commercial Identifié** : {signal_desc}")
        md.append(f"- **Angle d'Approche Lead Intelligence** : Approche orientée apport d'affaires direct sur leur zone de chalandise pour PME cibles.")
        
        has_dirigeant = bool(dirigeant and not dirigeant.lower().startswith('non identifié') and dirigeant != 'Inconnu')
        if has_dirigeant:
            prenom = dirigeant.split()[0].title()
            salutation = f"Bonjour {prenom},"
            gw_angle_desc = f"Prise de parole de {dirigeant} sur l'expertise technique et les études de cas de {clean_name}."
        else:
            salutation = "Bonjour,"
            gw_angle_desc = f"Prise de parole du dirigeant sur l'expertise technique et les études de cas de {clean_name}."

        md.append(f"- **Angle d'Approche Ghostwriting** : {gw_angle_desc}")
        md.append(f"- **Message d'Outreach Recommandé (Manuel)** :")
        md.append(f"> \"{salutation} j'ai analysé les réalisations récentes de {clean_name} à {p['city']}. Votre positionnement auprès des PME régionales est très solide. Pour vous éviter les périodes de creux de prospection, nous avons pré-audité 3 entreprises de votre région ayant un besoin immédiat de refonte digitale. Seriez-vous ouvert à ce que je vous transmette ces 3 fiches gracieusement pour recueillir votre retour de dirigeant ?\"")
        md.append('')

    md.append('---')
    md.append('')
    md.append('## 05 — Outreach Queue & Cadencement Manuel')
    md.append('')
    md.append('1. **Approche 100% Manuelle** : Aucun outil d\'automatisation ni de mass-mailing.')
    md.append('2. **Cibles Immédiates** : Les 5 agences prioritaires disposant du statut `VERIFIED`.')
    md.append('3. **Cadencement** : 2 à 3 prises de contact personnalisées par jour.')
    md.append('4. **Livrable de Démonstration** : Remise systématique d\'un mini-échantillon gracieux de 3 prospects pré-qualifiés avant toute proposition financière de pilote payant.')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 06 — Market Signals & Analyse Terrain')
    md.append('')
    md.append('- **Écart entre perception et réalité légale** : Plusieurs agences très visibles sur Google Maps sont des structures unipersonnelles sous-traitant la production. La vérification SIRENE est indispensable pour ne pas prospecter des non-employeurs.')
    md.append('- **Niches à forte autorité (Ghostwriting)** : Les studios UI/UX et les agences éco-conçues (ex: Youdemus, MASHVP) présentent un potentiel éditorial supérieur à la moyenne pour le personal branding de leurs fondateurs.')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 07 — Sources & Evidence (Traçabilité)')
    md.append('')
    md.append('- **Données Légales & Effectifs** : Registre national SIRENE via l\'API publique `recherche-entreprises.api.gouv.fr`.')
    md.append('- **Données Commerciales** : Google Maps Scraper (Docker local).')
    md.append('- **Audit des Offres & Sites** : Firecrawl MCP & analyses DOM directes.')
    md.append('- **Datasets du Projet** :')
    md.append('  - `data/top30_leads_requalified.csv`')
    md.append('  - `data/top30_leads_requalified.json`')
    md.append('')
    md.append('---')
    md.append('')
    md.append('## 08 — Delivery History')
    md.append('')
    md.append('- **26/09/2026 (Audit Initial)** : Premier crawl et détection des failles méthodologiques.')
    md.append('- **26/09/2026 (Requalification Institutionnelle)** : Intégration SIRENE, découplage des scores, identification de 16 agences formellement vérifiées.')

    content = '\n'.join(md)
    output_file = BASE_DIR / 'data' / 'lead_intelligence_room.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Lead Intelligence Room générée avec succès : {len(content)} caractères.")
    return content

if __name__ == '__main__':
    generate_lead_intelligence_markdown()
