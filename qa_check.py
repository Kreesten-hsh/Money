import csv
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent

ISO_TIMESTAMP_REGEX = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$'

def extract_canonical_domain(url: str) -> str:
    """Extrait le nom de domaine canonique sans sous-domaine www."""
    if not url:
        return ''
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        netloc = urllib.parse.urlsplit(url).netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc.split(':')[0]
    except Exception:
        return ''

def run_qa_checks(csv_path: Path = None, json_path: Path = None, md_path: Path = None) -> Tuple[bool, Dict[str, bool], Dict[str, List[str]]]:
    """
    Exécute les 20 contrôles de vérité métier et de preuves structurées sur le dataset spécifié.
    """
    csv_file = csv_path or (BASE_DIR / 'data' / 'top30_leads_requalified.csv')
    json_file = json_path or (BASE_DIR / 'data' / 'top30_leads_requalified.json')
    markdown_file = md_path or (BASE_DIR / 'data' / 'lead_intelligence_room.md')

    if not csv_file.exists():
        print(f"FAIL: Fichier {csv_file} introuvable.")
        return False, {}, {"Dataset": [f"Fichier {csv_file} inexistant"]}

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    # Charger JSON si existant pour types stricts (booléens, listes)
    json_leads = []
    if json_file and json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_leads = json.load(f)
        except Exception:
            json_leads = []

    results = {}
    failures = {}

    def record_check(name: str, check_failures: List[str]):
        results[name] = len(check_failures) == 0
        failures[name] = check_failures

    # 1. Intégrité des URLs & HTTPS
    c1 = []
    for idx, l in enumerate(leads, 1):
        site = l.get('website', '').strip()
        notes = l.get('notes', '')
        if not site:
            c1.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: URL manquante.")
        elif not (site.startswith('http://') or site.startswith('https://')):
            c1.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Schéma URL invalide ({site}).")
        elif not site.startswith('https://') and 'site inaccessible' not in notes.lower():
            c1.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: URL non-HTTPS sans mention dans les notes ({site}).")
    record_check("Contrôle 01 (Intégrité des URLs & HTTPS)", c1)

    # 2. SIREN & Preuve Légale Structurée
    c2 = []
    for idx, l in enumerate(leads, 1):
        status = l.get('verification_status')
        siren = l.get('siren', '').strip()
        siren_src = l.get('siren_source', '').strip()
        evidence_url = l.get('evidence_url', '').strip()
        if status in ('VERIFIED', 'PARTIALLY VERIFIED'):
            if not re.match(r'^\d{9}$', siren):
                c2.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: SIREN invalide ou absent ('{siren}') pour statut {status}.")
            if not siren_src or siren_src == 'Non trouvé':
                c2.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Source SIREN manquante pour statut {status}.")
            if not evidence_url or 'annuaire-entreprises.data.gouv.fr' not in evidence_url:
                c2.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: URL officielle Annuaire des Entreprises manquante ({evidence_url}).")
    record_check("Contrôle 02 (SIREN & Preuve Légale Structurée)", c2)

    # 3. Matching SIRENE Déterministe & Traçabilité Télémétrique
    c3 = []
    allowed_matching = {'MATCH_CONFIRMED', 'MATCH_PLAUSIBLE', 'MATCH_UNCERTAIN', 'NO_MATCH'}
    required_telemetry = [
        'sirene_candidate_selected',
        'sirene_candidate_score',
        'sirene_second_candidate_score',
        'sirene_score_delta',
        'sirene_matching_decision_reason'
    ]
    for idx, l in enumerate(leads, 1):
        m_status = l.get('matching_status', '').strip()
        if m_status not in allowed_matching:
            c3.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: matching_status non reconnu ('{m_status}').")
        for field in required_telemetry:
            if field not in l or l[field] is None or str(l[field]).strip() == '':
                c3.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Champ télémétrique '{field}' manquant.")
    record_check("Contrôle 03 (Matching SIRENE Déterministe & Télémétrie)", c3)

    # 4. Vraie Détection d'Ambiguïté SIRENE
    c4 = []
    for idx, l in enumerate(leads, 1):
        m_status = l.get('matching_status', '').strip()
        v_status = l.get('verification_status', '').strip()
        try:
            sec_score = int(l.get('sirene_second_candidate_score', 0))
            delta = int(l.get('sirene_score_delta', 0))
            cand_score = int(l.get('sirene_candidate_score', 0))
        except ValueError:
            sec_score, delta, cand_score = 0, 0, 0

        # Règle d'ambiguïté : 2ème candidat >= 55 et delta < 20 interdit MATCH_CONFIRMED
        if sec_score >= 55 and delta < 20 and m_status == 'MATCH_CONFIRMED':
            c4.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Candidats concurrents proches (2ème score {sec_score}, delta {delta} < 20) mais MATCH_CONFIRMED forcé.")
        
        # Règle de score minimum pour MATCH_CONFIRMED
        if cand_score < 75 and m_status == 'MATCH_CONFIRMED':
            c4.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score candidat insuffisant ({cand_score} < 75) pour MATCH_CONFIRMED.")

        # Interdiction absolue de VERIFIED si matching incertain ou absent
        if v_status == 'VERIFIED' and m_status != 'MATCH_CONFIRMED':
            c4.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Statut VERIFIED accordé avec matching '{m_status}'.")
    record_check("Contrôle 04 (Vraie Détection d'Ambiguïté SIRENE)", c4)

    # 5. ICP Strict 2-20 & Exclusion Non-Employeurs / >20
    c5 = []
    for idx, l in enumerate(leads, 1):
        size = l.get('company_size', '')
        size_code = l.get('company_size_code', '')
        v_status = l.get('verification_status')
        conf = int(l.get('confidence_score', 0))

        if size_code in ('NN', '00') or '0 salarié' in size or 'Non employeur' in size:
            if v_status != 'DISQUALIFIED':
                c5.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Structure non-employeur non disqualifiée ({v_status}).")
            if conf != 0:
                c5.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score de confiance non nul ({conf}) pour non-employeur.")

        if size_code in ('12', '21', '22') or any(b in size for b in ['20 à 49', '50 à 99', '100 à']):
            if v_status != 'DISQUALIFIED':
                c5.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Structure > 20 salariés non disqualifiée ({size}).")
    record_check("Contrôle 05 (ICP Strict 2-20 & Exclusion Non-Employeurs)", c5)

    # 6. Preuve Structurée Effectif & Tranche 01
    c6 = []
    for idx, l in enumerate(leads, 1):
        v_status = l.get('verification_status')
        size_code = l.get('company_size_code', '')
        has_sec = str(l.get('has_secondary_size_proof', '')).lower() in ('true', '1')
        sec_src = l.get('secondary_size_proof_source', '').strip()
        sec_details = l.get('secondary_size_proof_details', '').strip()

        if v_status == 'VERIFIED':
            if size_code == '01':
                if not has_sec:
                    c6.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Tranche 01 marquée VERIFIED sans has_secondary_size_proof.")
                if not sec_src:
                    c6.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Tranche 01 marquée VERIFIED sans source de preuve secondaire.")
                if not sec_details or len(sec_details) < 10:
                    c6.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Tranche 01 marquée VERIFIED sans détails des co-dirigeants greffe.")
            elif size_code not in ('02', '03', '11'):
                c6.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Statut VERIFIED avec code d'effectif invalide ({size_code}).")

        # Tranche 01 sans preuve secondaire doit être REQUIRES REVIEW
        if size_code == '01' and not has_sec and v_status in ('VERIFIED', 'PARTIALLY VERIFIED'):
            c6.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Tranche 01 sans preuve secondaire doit rester REQUIRES REVIEW (actuel: {v_status}).")
    record_check("Contrôle 06 (Preuve Structurée Effectif & Tranche 01)", c6)

    # 7. Preuve Structurée Dirigeant & Rôle Officiel
    c7 = []
    for idx, l in enumerate(leads, 1):
        v_status = l.get('verification_status')
        dm = l.get('decision_maker', '').strip()
        role = l.get('decision_maker_role', '').strip()
        dm_src = l.get('decision_maker_source', '').strip()
        dm_dt = l.get('decision_maker_checked_at', '').strip()

        if v_status == 'VERIFIED':
            if not dm or 'non identifié' in dm.lower() or dm == 'Inconnu':
                c7.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Dirigeant non identifié pour statut VERIFIED.")
            if not role or role in ('Inconnu', 'Non identifié'):
                c7.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Rôle officiel manquant pour statut VERIFIED ({role}).")
            if not dm_src:
                c7.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Source du dirigeant manquante pour statut VERIFIED.")
            if not dm_dt or not re.match(ISO_TIMESTAMP_REGEX, dm_dt):
                c7.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Horodatage ISO du dirigeant manquant ou invalide ({dm_dt}).")
    record_check("Contrôle 07 (Preuve Structurée Dirigeant & Rôle Officiel)", c7)

    # 8. Preuves Indépendantes Main Offer
    c8 = []
    for idx, l in enumerate(leads, 1):
        offer = l.get('main_offer', '').strip()
        src = l.get('main_offer_source', '').strip()
        ev = l.get('main_offer_evidence', '').strip()
        dt = l.get('main_offer_checked_at', '').strip()

        if offer != 'Non vérifié':
            if not src or not src.startswith('http'):
                c8.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: main_offer renseignée ('{offer}') sans URL source valide.")
            if not ev:
                c8.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: main_offer renseignée sans extrait de preuve.")
            if not dt or not re.match(ISO_TIMESTAMP_REGEX, dt):
                c8.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Horodatage ISO main_offer invalide ({dt}).")
    record_check("Contrôle 08 (Preuves Indépendantes Main Offer)", c8)

    # 9. Preuves Indépendantes Target Clients
    c9 = []
    for idx, l in enumerate(leads, 1):
        target = l.get('target_clients', '').strip()
        src = l.get('target_clients_source', '').strip()
        ev = l.get('target_clients_evidence', '').strip()
        dt = l.get('target_clients_checked_at', '').strip()

        if target != 'Non vérifié':
            if not src or not src.startswith('http'):
                c9.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: target_clients renseignée ('{target}') sans URL source.")
            if not ev:
                c9.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: target_clients renseignée sans preuve textuelle explicite.")
            if not dt or not re.match(ISO_TIMESTAMP_REGEX, dt):
                c9.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Horodatage ISO target_clients invalide ({dt}).")
        else:
            if src != '':
                c9.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: target_clients est 'Non vérifié' mais target_clients_source n'est pas vide.")
            if not ev:
                c9.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Justification d'absence de cible manquante dans target_clients_evidence.")
    record_check("Contrôle 09 (Preuves Indépendantes Target Clients)", c9)

    # 10. Temporalité Dynamique & Zéro Date Hardcodée
    c10 = []
    temporal_fields = [
        'last_checked',
        'siren_checked_at',
        'company_size_checked_at',
        'decision_maker_checked_at',
        'main_offer_checked_at',
        'target_clients_checked_at'
    ]
    for idx, l in enumerate(leads, 1):
        for fld in temporal_fields:
            val = l.get(fld, '').strip()
            if not val:
                c10.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Champ temporel '{fld}' manquant.")
            elif not re.match(ISO_TIMESTAMP_REGEX, val):
                c10.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Date non dynamique ou non ISO dans '{fld}' ('{val}').")
            elif val == '2026-09-27':
                c10.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Date statique hardcodée '2026-09-27' détectée dans '{fld}'.")

        # Confusion date vérification vs date signal
        sig_date = l.get('signal_date', '').strip()
        last_chk = l.get('last_checked', '').strip()
        if sig_date and sig_date == last_chk:
            c10.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Confusion entre date de signal et date de vérification.")
    record_check("Contrôle 10 (Temporalité Dynamique & Zéro Date Hardcodée)", c10)

    # 11. Non-Redondance Domaine
    c11 = []
    seen_domains = {}
    for idx, l in enumerate(leads, 1):
        site = l.get('website', '').strip()
        if site:
            domain = urllib.parse.urlsplit(site).netloc.lower().replace('www.', '')
            if domain in seen_domains:
                c11.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Doublon de domaine '{domain}' déjà vu ligne {seen_domains[domain]}.")
            else:
                seen_domains[domain] = idx
    record_check("Contrôle 11 (Non-Redondance Domaine)", c11)

    # 12. Non-Redondance Téléphone
    c12 = []
    seen_phones = {}
    for idx, l in enumerate(leads, 1):
        raw_phone = l.get('public_phone', '')
        digits = re.sub(r'\D', '', raw_phone)
        if len(digits) >= 9:
            if digits in seen_phones:
                c12.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Doublon de téléphone '{raw_phone}' déjà vu ligne {seen_phones[digits]}.")
            else:
                seen_phones[digits] = idx
    record_check("Contrôle 12 (Non-Redondance Téléphone)", c12)

    # 13. Non-Redondance SIREN
    c13 = []
    seen_sirens = {}
    for idx, l in enumerate(leads, 1):
        siren = l.get('siren', '').strip()
        if re.match(r'^\d{9}$', siren):
            if siren in seen_sirens:
                c13.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Doublon SIREN '{siren}' déjà vu ligne {seen_sirens[siren]}.")
            else:
                seen_sirens[siren] = idx
    record_check("Contrôle 13 (Non-Redondance SIREN)", c13)

    # 14. Cohérence Score Lead Gen (Modèle 4 Piliers /100, Max 75)
    c14 = []
    for idx, l in enumerate(leads, 1):
        try:
            lg = int(l.get('lead_gen_score', -1))
            if not (0 <= lg <= 100):
                c14.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Lead Gen hors bornes 0-100 ({lg}).")
            sig = l.get('commercial_signal', '').strip()
            # En l'absence de signal commercial vérifié, le score ne peut pas dépasser 75
            if not sig and lg > 75:
                c14.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Lead Gen {lg} > 75 sans signal commercial vérifié.")
        except ValueError:
            c14.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Lead Gen non entier.")
    record_check("Contrôle 14 (Modèle Score Lead Gen /100 & Max 75)", c14)

    # 15. Score Ghostwriting Neutralisé
    c15 = []
    for idx, l in enumerate(leads, 1):
        try:
            gw = int(l.get('ghostwriting_score', -1))
            if gw != 0:
                c15.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Ghostwriting non neutralisé ({gw}) sans audit éditorial.")
        except ValueError:
            c15.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Ghostwriting non entier.")
    record_check("Contrôle 15 (Score Ghostwriting Neutralisé)", c15)

    # 16. Cohérence Score Confiance & Plafonds
    c16 = []
    for idx, l in enumerate(leads, 1):
        v_status = l.get('verification_status')
        m_status = l.get('matching_status')
        try:
            conf = int(l.get('confidence_score', -1))
            if not (0 <= conf <= 100):
                c16.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score confiance hors bornes 0-100 ({conf}).")
            if v_status != 'VERIFIED' and conf > 60:
                c16.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Non-VERIFIED avec score confiance {conf} > 60.")
            if m_status in ('MATCH_UNCERTAIN', 'NO_MATCH') and conf > 40:
                c16.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Matching incertain avec score confiance {conf} > 40.")
            if v_status == 'DISQUALIFIED' and conf != 0:
                c16.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: DISQUALIFIED avec score confiance non nul ({conf}).")
        except ValueError:
            c16.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score confiance non entier.")
    record_check("Contrôle 16 (Cohérence Score Confiance & Plafonds)", c16)

    # 17. Hard Gates Statut VERIFIED
    c17 = []
    for idx, l in enumerate(leads, 1):
        v_status = l.get('verification_status')
        if v_status == 'VERIFIED':
            conf = int(l.get('confidence_score', 0))
            m_status = l.get('matching_status')
            siren = l.get('siren', '')
            dm = l.get('decision_maker', '')
            site = l.get('website', '')
            if conf < 80:
                c17.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED avec score confiance {conf} < 80.")
            if m_status != 'MATCH_CONFIRMED':
                c17.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED avec matching '{m_status}'.")
            if not re.match(r'^\d{9}$', siren):
                c17.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED sans SIREN valide.")
            if not dm or 'non identifié' in dm.lower() or dm == 'Inconnu':
                c17.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED sans dirigeant officiel.")
            if not site.startswith('https://'):
                c17.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED avec site non HTTPS.")
    record_check("Contrôle 17 (Hard Gates Statut VERIFIED)", c17)

    # 18. Traçabilité des Justifications Reasons
    c18 = []
    for idx, l in enumerate(leads, 1):
        reasons = l.get('reasons', '').strip()
        if not reasons:
            c18.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Champ 'reasons' manquant ou vide.")
        elif 'Lead Gen' not in reasons or 'GW' not in reasons or 'Confidence' not in reasons:
            c18.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Champ 'reasons' incomplet (doit couvrir LG, GW et Confidence).")
    record_check("Contrôle 18 (Traçabilité Justifications Reasons)", c18)

    # 19. Véracité Message d'Outreach Notion
    c19 = []
    if markdown_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        banned_phrases = [
            'besoin urgent',
            'besoin immédiat',
            'besoin actuel',
            'intention d\'achat',
            'recherchent actuellement des prestataires',
            'recherchent des prestataires',
            'recherche activement',
            'positionnement très solide',
            'échantillon préparé',
            'pré-audité 3 entreprises',
            'Bonjour Non',
            'Bonjour ,',
            '{prenom}',
            '{role}'
        ]
        for phrase in banned_phrases:
            if phrase.lower() in md_text.lower():
                c19.append(f"Présence de formulation non prouvée ou placeholder corrompu : '{phrase}'.")
    else:
        c19.append(f"Fichier de restitution {markdown_file} introuvable.")
    record_check("Contrôle 19 (Véracité Message d'Outreach)", c19)

    # 20. Synchronisation Notion / Dataset & Pipeline Réel
    c20 = []
    if markdown_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        verified_sirens = [l['siren'] for l in leads if l.get('verification_status') == 'VERIFIED']
        for s in verified_sirens:
            if s not in md_content:
                c20.append(f"SIREN vérifié '{s}' absent du rapport Markdown.")
    else:
        c20.append("Fichier Markdown introuvable.")

    shortlist_file = BASE_DIR / 'data' / 'gmaps_agences_web_shortlist.csv'
    requalify_script = BASE_DIR / 'requalify_leads.py'
    legacy_json = BASE_DIR / 'data' / 'top30_leads_qualified.json'
    legacy_csv = BASE_DIR / 'data' / 'top30_leads_qualified.csv'

    if not shortlist_file.exists():
        c20.append(f"Shortlist {shortlist_file} inexistante.")
    if legacy_json.exists() or legacy_csv.exists():
        c20.append("Anciens artefacts obsolètes présents dans data/.")
    if requalify_script.exists():
        with open(requalify_script, 'r', encoding='utf-8') as f:
            code = f.read()
        if 'gmaps_agences_web_shortlist.csv' not in code:
            c20.append("requalify_leads.py ne consomme pas gmaps_agences_web_shortlist.csv.")
        if 'top30_leads_qualified.json' in code:
            c20.append("requalify_leads.py référence encore l'ancien fichier temporaire.")
    record_check("Contrôle 20 (Synchronisation Notion / Dataset & Pipeline)", c20)

    # 21. Salutation Personne Morale (TÂCHE 4)
    c21 = []
    if markdown_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_text = f.read()

        # Interdiction formelle globale de toute salutation sur les personnes morales auditées (ex: WATTZ, SAMOTHRACE)
        banned_historical_holdings = ["wattz", "wattz office", "samothrace"]
        for bh in banned_historical_holdings:
            if f"bonjour {bh}" in md_text.lower():
                c21.append(f"Salutation nominative résiduelle interdite 'Bonjour {bh.title()}' détectée dans le markdown.")

        for idx, l in enumerate(leads, 1):
            is_person = str(l.get('decision_maker_is_person', '')).lower() in ('true', '1')
            dm = l.get('decision_maker', '').strip()
            clean_name = l.get('brand_name', '').split('|')[0].strip()

            if not is_person and dm and dm not in ('Non identifié au registre', 'Inconnu'):
                first_word = dm.split()[0].title()
                banned_salutations = [f"Bonjour {first_word},", f"Bonjour {first_word} "]
                for b_sal in banned_salutations:
                    if b_sal.lower() in md_text.lower():
                        c21.append(f"Ligne {idx:02d} [{clean_name}]: Salutation nominative non autorisée '{b_sal}' pour la personne morale '{dm}'.")
    else:
        c21.append(f"Fichier Markdown {markdown_file} introuvable.")
    record_check("Contrôle 21 (Salutation Personne Morale)", c21)

    # 22. Auditabilité & Concordance Email Professionnel (ADR-009 & Schéma v2)
    c22 = []
    for idx, l in enumerate(leads, 1):
        email = l.get('public_professional_email', '').strip()
        e_src = l.get('email_source', '').strip()
        e_ev = l.get('email_evidence', '').strip()
        e_time = l.get('email_checked_at', '').strip()
        website = l.get('website', '').strip()
        site_domain = extract_canonical_domain(website)

        if email and email not in ('Non extrait (Option)', 'Non extrait', 'Inconnu', 'Non trouvé'):
            if '@' not in email or not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                c22.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Format email invalide ('{email}').")
            if not e_src:
                c22.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: email renseigné ('{email}') sans email_source.")
            if not e_ev:
                c22.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: email renseigné ('{email}') sans email_evidence.")
            if not e_time or not re.match(ISO_TIMESTAMP_REGEX, e_time):
                c22.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: email renseigné ('{email}') avec email_checked_at non-ISO.")
            
            email_domain = email.split('@')[1].lower() if '@' in email else ''
            if site_domain and email_domain != site_domain and not email_domain.endswith('.' + site_domain):
                c22.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Discordance domaine email '{email_domain}' vs site web '{site_domain}'.")
    record_check("Contrôle 22 (Auditabilité & Concordance Email Professionnel)", c22)

    # 23. Preuve & Auditabilité Empreinte CMS (Schéma v2)
    c23 = []
    for idx, l in enumerate(leads, 1):
        cms = l.get('cms_detected', '').strip()
        cms_src = l.get('cms_source', '').strip()
        cms_ev = l.get('cms_evidence', '').strip()
        cms_time = l.get('cms_checked_at', '').strip()

        if cms and cms not in ('Inconnu', 'Non vérifié', 'Non extrait'):
            if not cms_src:
                c23.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: CMS détecté ('{cms}') sans cms_source.")
            if not cms_ev:
                c23.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: CMS détecté ('{cms}') sans cms_evidence.")
            if cms_time and not re.match(ISO_TIMESTAMP_REGEX, cms_time):
                c23.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: CMS détecté ('{cms}') avec cms_checked_at non-ISO.")
    record_check("Contrôle 23 (Preuve & Auditabilité Empreinte CMS)", c23)

    # 24. Étanchéité Staging MCP vs Registre Légal (ADR-008 & Niveau 4 vs Niveau 1/2)
    c24 = []
    mcp_staging_file = BASE_DIR / 'data' / 'mcp_audit_staging.json'
    mcp_prohibited_values: Set[str] = set()
    if mcp_staging_file.exists():
        try:
            with open(mcp_staging_file, 'r', encoding='utf-8') as f:
                mcp_data = json.load(f)
                entries = mcp_data.get('entries', []) if isinstance(mcp_data, dict) else mcp_data
                for entry in entries:
                    val = str(entry.get('extracted_value', '')).strip()
                    if val and len(val) >= 4 and val.lower() not in ('true', 'false', 'inconnu', 'non extrait', 'non vérifié', 'none', 'null'):
                        mcp_prohibited_values.add(val.lower())
        except Exception:
            pass

    for idx, l in enumerate(leads, 1):
        dm = str(l.get('decision_maker', '')).strip().lower()
        dm_role = str(l.get('decision_maker_role', '')).strip().lower()
        c_size = str(l.get('company_size', '')).strip().lower()
        c_size_code = str(l.get('company_size_code', '')).strip().lower()

        for prohibited in mcp_prohibited_values:
            if prohibited in dm or dm == prohibited:
                c24.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Fuite MCP staging dans decision_maker ('{l.get('decision_maker')}').")
            if prohibited in dm_role or dm_role == prohibited:
                c24.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Fuite MCP staging dans decision_maker_role ('{l.get('decision_maker_role')}').")
            if prohibited in c_size or c_size == prohibited:
                c24.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Fuite MCP staging dans company_size ('{l.get('company_size')}').")
            if prohibited in c_size_code or c_size_code == prohibited:
                c24.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Fuite MCP staging dans company_size_code ('{l.get('company_size_code')}').")
    record_check("Contrôle 24 (Étanchéité Staging MCP vs Registre Légal)", c24)

    # 25. Absence d'Erreurs Techniques MCP dans les Données (Filet de Sécurité Anti-Régression)
    c25 = []
    banned_mcp_error_patterns = [
        "error executing tool",
        "the main browser is not open",
        "the main browser did not start",
        "requires xvfb",
        "browser.newpage: no response in",
        "mcp_tool_error",
        "engine_not_ready"
    ]
    monitored_fields = [
        "main_offer",
        "target_clients",
        "decision_maker_linkedin_activity",
        "notes",
        "reasons_lead_gen",
        "reasons_gw",
        "reasons_confidence"
    ]

    for idx, l in enumerate(leads, 1):
        clean_name = l.get('brand_name', '').split('|')[0].strip()
        for field in monitored_fields:
            val = str(l.get(field, '')).strip().lower()
            for pattern in banned_mcp_error_patterns:
                if pattern in val:
                    c25.append(f"Ligne {idx:02d} [{clean_name}]: Champ '{field}' contient un message d'erreur MCP non filtré : '{pattern}'.")
    record_check("Contrôle 25 (Absence d'Erreurs Techniques MCP dans les Données)", c25)

    all_passed = all(results.values())
    return all_passed, results, failures

def run_negative_tests() -> Tuple[bool, int, int]:
    """
    Exécute le banc de tests négatifs couvrant les 5 domaines critiques exigés par la section 7 :
    - SIRENE (ambiguïté, mauvais CP, mauvais nom, candidat insuffisant)
    - Preuves (source SIRENE manquante, preuve effectif manquante, preuve dirigeant manquante, tranche 01 sans preuve, offre/cible sans source)
    - Outreach (besoin non observé, fausse urgence, placeholder vide, compliment non prouvé)
    - Temporalité (last_checked hardcodé, confusion date signal/vérification)
    - Scoring (points signal commercial artificiels, score hors borne)
    """
    print("\n=== BANC DE TESTS NÉGATIFS (FIXTURES CORROMPUES — SECTION 7) ===")

    csv_file = BASE_DIR / 'data' / 'top30_leads_requalified.csv'
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        base_leads = list(reader)

    fixtures = [
        # SIRENE
        {
            "name": "SIRENE 1 : Deux candidats presque équivalents (delta 5 < 20) marqués MATCH_CONFIRMED",
            "modify": lambda rows: rows[0].update({
                "sirene_second_candidate_score": "80",
                "sirene_score_delta": "5",
                "matching_status": "MATCH_CONFIRMED"
            }),
            "expected_fail": "Contrôle 04 (Vraie Détection d'Ambiguïté SIRENE)"
        },
        {
            "name": "SIRENE 2 : Candidat avec score insuffisant (60 < 75) marqué MATCH_CONFIRMED",
            "modify": lambda rows: rows[0].update({
                "sirene_candidate_score": "60",
                "matching_status": "MATCH_CONFIRMED"
            }),
            "expected_fail": "Contrôle 04 (Vraie Détection d'Ambiguïté SIRENE)"
        },
        {
            "name": "SIRENE 3 : Lead VERIFIED avec matching MATCH_UNCERTAIN",
            "modify": lambda rows: rows[0].update({
                "verification_status": "VERIFIED",
                "matching_status": "MATCH_UNCERTAIN"
            }),
            "expected_fail": "Contrôle 04 (Vraie Détection d'Ambiguïté SIRENE)"
        },

        # PREUVES
        {
            "name": "Preuves 1 : VERIFIED sans source SIRENE officielle",
            "modify": lambda rows: rows[0].update({
                "verification_status": "VERIFIED",
                "siren_source": ""
            }),
            "expected_fail": "Contrôle 02 (SIREN & Preuve Légale Structurée)"
        },
        {
            "name": "Preuves 2 : Tranche 01 marquée VERIFIED sans preuve secondaire (has_secondary_size_proof=False)",
            "modify": lambda rows: rows[0].update({
                "verification_status": "VERIFIED",
                "company_size_code": "01",
                "has_secondary_size_proof": "False",
                "secondary_size_proof_details": ""
            }),
            "expected_fail": "Contrôle 06 (Preuve Structurée Effectif & Tranche 01)"
        },
        {
            "name": "Preuves 3 : VERIFIED sans preuve de dirigeant officiel",
            "modify": lambda rows: rows[0].update({
                "verification_status": "VERIFIED",
                "decision_maker": "Non identifié au registre",
                "decision_maker_role": "Inconnu"
            }),
            "expected_fail": "Contrôle 07 (Preuve Structurée Dirigeant & Rôle Officiel)"
        },
        {
            "name": "Preuves 4 : main_offer renseignée sans URL source",
            "modify": lambda rows: rows[0].update({
                "main_offer": "Création WordPress PME",
                "main_offer_source": ""
            }),
            "expected_fail": "Contrôle 08 (Preuves Indépendantes Main Offer)"
        },
        {
            "name": "Preuves 5 : target_clients renseignée sans URL source",
            "modify": lambda rows: rows[0].update({
                "target_clients": "PME & ETI",
                "target_clients_source": ""
            }),
            "expected_fail": "Contrôle 09 (Preuves Indépendantes Target Clients)"
        },

        # TEMPORALITÉ
        {
            "name": "Temporalité 1 : last_checked hardcodé '2026-09-27' non-ISO",
            "modify": lambda rows: rows[0].update({
                "last_checked": "2026-09-27"
            }),
            "expected_fail": "Contrôle 10 (Temporalité Dynamique & Zéro Date Hardcodée)"
        },
        {
            "name": "Temporalité 2 : Confusion date de signal utilisée comme date de vérification",
            "modify": lambda rows: rows[0].update({
                "signal_date": "2026-09-27T12:00:00Z",
                "last_checked": "2026-09-27T12:00:00Z"
            }),
            "expected_fail": "Contrôle 10 (Temporalité Dynamique & Zéro Date Hardcodée)"
        },

        # SCORING
        {
            "name": "Scoring 1 : Attribution artificielle de points sans signal commercial (score 90 > 75)",
            "modify": lambda rows: rows[0].update({
                "commercial_signal": "",
                "lead_gen_score": "90"
            }),
            "expected_fail": "Contrôle 14 (Modèle Score Lead Gen /100 & Max 75)"
        },
        {
            "name": "Scoring 2 : Score Lead Gen dépassant la borne (> 100)",
            "modify": lambda rows: rows[0].update({
                "lead_gen_score": "105"
            }),
            "expected_fail": "Contrôle 14 (Modèle Score Lead Gen /100 & Max 75)"
        },
        {
            "name": "Scoring 3 : Score Ghostwriting non neutralisé (80/100)",
            "modify": lambda rows: rows[0].update({
                "ghostwriting_score": "80"
            }),
            "expected_fail": "Contrôle 15 (Score Ghostwriting Neutralisé)"
        },

        # REDONDANCE
        {
            "name": "Redondance 1 : Doublon SIREN artificiel",
            "modify": lambda rows: rows[1].update({
                "siren": rows[0]["siren"]
            }),
            "expected_fail": "Contrôle 13 (Non-Redondance SIREN)"
        },

        # OSINT & ENRICHISSEMENT (ADR-009 & Schéma v2)
        {
            "name": "OSINT 1 : Email professionnel renseigné sans source et avec discordance de domaine",
            "modify": lambda rows: rows[0].update({
                "public_professional_email": "contact@agence-externe-inconnue.com",
                "email_source": "",
                "email_evidence": "",
                "email_checked_at": ""
            }),
            "expected_fail": "Contrôle 22 (Auditabilité & Concordance Email Professionnel)"
        },
        {
            "name": "OSINT 2 : CMS détecté renseigné sans source ni extrait de preuve",
            "modify": lambda rows: rows[0].update({
                "cms_detected": "WordPress 6.4",
                "cms_source": "",
                "cms_evidence": ""
            }),
            "expected_fail": "Contrôle 23 (Preuve & Auditabilité Empreinte CMS)"
        },
        # ÉTANCHÉITÉ MCP STAGING & ERREURS TECHNIQUES (Contrôles 24 & 25)
        {
            "name": "MCP 1 : Valeur issue du staging MCP ayant fuité dans decision_maker légal",
            "modify": lambda rows: rows[0].update({
                "decision_maker": "Création de sites web vitrines et e-commerce sur-mesure"
            }),
            "expected_fail": "Contrôle 24 (Étanchéité Staging MCP vs Registre Légal)"
        },
        {
            "name": "MCP 2 : Erreur technique MCP injectée dans main_offer",
            "modify": lambda rows: rows[0].update({
                "main_offer": "Error executing tool browser_read_text: the main browser is not open."
            }),
            "expected_fail": "Contrôle 25 (Absence d'Erreurs Techniques MCP dans les Données)"
        }
    ]

    # Test Markdown Outreach spécifique
    md_file = BASE_DIR / 'data' / 'lead_intelligence_room.md'
    with open(md_file, 'r', encoding='utf-8') as f:
        base_md = f.read()

    md_fixtures = [
        {
            "name": "Outreach 1 : Message affirmant un besoin non observé ('besoin urgent')",
            "corrupt_md": base_md + "\n> Bonjour Axel, nous avons identifié votre besoin urgent en acquisition.",
            "expected_fail": "Contrôle 19 (Véracité Message d'Outreach)"
        },
        {
            "name": "Outreach 2 : Message affirmant que des prestataires sont recherchés",
            "corrupt_md": base_md + "\n> Des entreprises locales recherchent des prestataires web dans votre ville.",
            "expected_fail": "Contrôle 19 (Véracité Message d'Outreach)"
        },
        {
            "name": "Outreach 3 : Placeholder corrompu ('Bonjour Non,')",
            "corrupt_md": base_md + "\n> Bonjour Non, voici une opportunité commerciale.",
            "expected_fail": "Contrôle 19 (Véracité Message d'Outreach)"
        },
        {
            "name": "Outreach 4 : Salutation nominative sur personne morale ('Bonjour Wattz,')",
            "corrupt_md": base_md + "\n> Bonjour Wattz, nous avons identifié votre agence Kwantic.",
            "expected_fail": "Contrôle 21 (Salutation Personne Morale)"
        }
    ]

    passed_count = 0
    total_count = len(fixtures) + len(md_fixtures)
    temp_csv = BASE_DIR / 'data' / 'temp_negative_fixture.csv'
    temp_md = BASE_DIR / 'data' / 'temp_negative_fixture.md'

    import copy
    for fix in fixtures:
        corrupted = copy.deepcopy(base_leads)
        fix["modify"](corrupted)
        with open(temp_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(corrupted[0].keys()))
            writer.writeheader()
            writer.writerows(corrupted)

        _, results, _ = run_qa_checks(csv_path=temp_csv)
        failed_as_expected = not results.get(fix["expected_fail"], True)
        if failed_as_expected:
            print(f"  [PASS] {fix['name']} -> Rejeté par '{fix['expected_fail']}'.")
            passed_count += 1
        else:
            print(f"  [FAIL] {fix['name']} -> NON DÉTECTÉ par '{fix['expected_fail']}' !")

    if temp_csv.exists():
        temp_csv.unlink()

    for fix in md_fixtures:
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(fix["corrupt_md"])

        _, results, _ = run_qa_checks(md_path=temp_md)
        failed_as_expected = not results.get(fix["expected_fail"], True)
        if failed_as_expected:
            print(f"  [PASS] {fix['name']} -> Rejeté par '{fix['expected_fail']}'.")
            passed_count += 1
        else:
            print(f"  [FAIL] {fix['name']} -> NON DÉTECTÉ par '{fix['expected_fail']}' !")

    if temp_md.exists():
        temp_md.unlink()

    all_passed = (passed_count == total_count)
    return all_passed, passed_count, total_count

if __name__ == '__main__':
    print("=== DÉMARRAGE AUDIT QA OFFICIEL (25 CONTRÔLES MÉTIER) ===")
    passed, results, failures = run_qa_checks()

    for check_name, check_ok in results.items():
        status = "PASS" if check_ok else "FAIL"
        print(f"[{status}] {check_name}")
        if not check_ok:
            for fail_msg in failures[check_name]:
                print(f"       -> {fail_msg}")

    print("-" * 50)
    print(f"Bilan Dataset Réel : {sum(results.values())}/25 CONTRÔLES VALIDÉS.")

    neg_ok, neg_passed, neg_total = run_negative_tests()
    print("-" * 50)
    print(f"Bilan Tests Négatifs : {neg_passed}/{neg_total} CORRUPTIONS DÉTECTÉES ({'PASS' if neg_ok else 'FAIL'}).")

    total_ok = passed and neg_ok
    print(f"RÉSULTAT GLOBAL : {'CONFORME AUX STANDARDS DE VÉRITÉ' if total_ok else 'NON CONFORME'}")
    exit(0 if total_ok else 1)
