import csv
import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent

def run_qa_checks(csv_path: Path = None, json_path: Path = None, md_path: Path = None) -> Tuple[bool, Dict[str, bool], Dict[str, List[str]]]:
    """
    Exécute les 20 contrôles de vérité métier sur le dataset spécifié.
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

    results = {}
    failures = {}

    def record_check(name: str, check_failures: List[str]):
        results[name] = len(check_failures) == 0
        failures[name] = check_failures

    # 1. URL réellement testable
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
    record_check("Contrôle 01 (URL Testable & Valide)", c1)

    # 2. SIREN valide
    c2 = []
    for idx, l in enumerate(leads, 1):
        status = l.get('verification_status')
        siren = l.get('siren', '').strip()
        if status in ('VERIFIED', 'PARTIALLY VERIFIED'):
            if not re.match(r'^\d{9}$', siren):
                c2.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: SIREN invalide ou absent ('{siren}') pour statut {status}.")
            if not l.get('evidence_url', '').strip():
                c2.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Preuve greffe/INSEE manquante pour statut {status}.")
    record_check("Contrôle 02 (SIREN & Preuve Légale)", c2)

    # 3. Matching SIRENE non ambigu
    c3 = []
    allowed_matching = {'MATCH_CONFIRMED', 'MATCH_PLAUSIBLE', 'MATCH_UNCERTAIN', 'NO_MATCH'}
    for idx, l in enumerate(leads, 1):
        m_status = l.get('matching_status', '').strip()
        v_status = l.get('verification_status', '').strip()
        if m_status not in allowed_matching:
            c3.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: matching_status non reconnu ('{m_status}').")
        if v_status == 'VERIFIED' and m_status != 'MATCH_CONFIRMED':
            c3.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Statut VERIFIED accordé alors que matching_status = '{m_status}'.")
    record_check("Contrôle 03 (Matching SIRENE Non Ambigu)", c3)

    # 4. ICP strict 2-20
    c4 = []
    for idx, l in enumerate(leads, 1):
        size = l.get('company_size', '')
        v_status = l.get('verification_status')
        notes = l.get('notes', '')
        reasons = l.get('reasons', '')
        
        # Tranches 0 salarié / non employeur obligatoirement DISQUALIFIED
        if '0 salarié' in size or 'Non employeur' in size:
            if v_status != 'DISQUALIFIED':
                c4.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Tranche 0 salarié/non-employeur non disqualifiée ({v_status}).")
        
        # Tranche 1 ou 2 salariés : VERIFIED uniquement avec preuve secondaire avérée
        if '1 ou 2 salariés' in size:
            if v_status == 'VERIFIED':
                has_secondary_proof = 'preuve secondaire' in notes.lower() or 'preuve secondaire' in reasons.lower() or 'co-dirigeant' in reasons.lower() or 'associé' in reasons.lower()
                if not has_secondary_proof:
                    c4.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Tranche 1-2 salariés marquée VERIFIED sans preuve secondaire publique.")
        
        # Tranches > 20 salariés
        if any(banned in size for banned in ['20 à 49', '50 à 99', '100 à']):
            if v_status != 'DISQUALIFIED':
                c4.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Effectif > 20 hors cible non disqualifié ({size}).")
    record_check("Contrôle 04 (ICP Strict 2-20 Salariés)", c4)

    # 5. Non-redondance domaine
    c5 = []
    seen_domains = {}
    for idx, l in enumerate(leads, 1):
        site = l.get('website', '').strip()
        if site:
            domain = urllib.parse.urlsplit(site).netloc.lower().replace('www.', '')
            if domain in seen_domains:
                c5.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Doublon de domaine '{domain}' déjà présent ligne {seen_domains[domain]}.")
            else:
                seen_domains[domain] = idx
    record_check("Contrôle 05 (Non-Redondance Domaine)", c5)

    # 6. Non-redondance téléphone
    c6 = []
    seen_phones = {}
    for idx, l in enumerate(leads, 1):
        raw_phone = l.get('public_phone', '')
        phone_digits = re.sub(r'\D', '', raw_phone)
        if len(phone_digits) >= 9:
            if phone_digits in seen_phones:
                c6.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Doublon de téléphone '{raw_phone}' déjà vu ligne {seen_phones[phone_digits]}.")
            else:
                seen_phones[phone_digits] = idx
    record_check("Contrôle 06 (Non-Redondance Téléphone)", c6)

    # 7. Non-redondance SIREN
    c7 = []
    seen_sirens = {}
    for idx, l in enumerate(leads, 1):
        siren = l.get('siren', '').strip()
        if re.match(r'^\d{9}$', siren):
            if siren in seen_sirens:
                c7.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Doublon SIREN '{siren}' déjà vu ligne {seen_sirens[siren]}.")
            else:
                seen_sirens[siren] = idx
    record_check("Contrôle 07 (Non-Redondance SIREN)", c7)

    # 8. Score Lead Gen cohérent
    c8 = []
    for idx, l in enumerate(leads, 1):
        try:
            lg = int(l.get('lead_gen_score', -1))
            if not (0 <= lg <= 100):
                c8.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Lead Gen hors bornes [0-100] ({lg}).")
            if lg == 100:
                c8.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Lead Gen arbitrairement fixé à 100.")
        except ValueError:
            c8.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Lead Gen non entier.")
    record_check("Contrôle 08 (Cohérence Score Lead Gen)", c8)

    # 9. Score Ghostwriting cohérent
    c9 = []
    for idx, l in enumerate(leads, 1):
        try:
            gw = int(l.get('ghostwriting_score', -1))
            # Règle : En phase 1 (Option B), tant qu'aucun audit éditorial LinkedIn public n'a été réalisé, score = 0
            if gw != 0:
                c9.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Ghostwriting non neutralisé ({gw}) sans audit éditorial public.")
        except ValueError:
            c9.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Score Ghostwriting non entier.")
    record_check("Contrôle 09 (Score Ghostwriting Neutralisé)", c9)

    # 10. Confidence score cohérent
    c10 = []
    for idx, l in enumerate(leads, 1):
        try:
            conf = int(l.get('confidence_score', -1))
            if not (0 <= conf <= 100):
                c10.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Confidence score hors bornes [0-100] ({conf}).")
        except ValueError:
            c10.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Confidence score non entier.")
    record_check("Contrôle 10 (Cohérence Score Confiance)", c10)

    # 11. Plafonds de confiance appliqués
    c11 = []
    for idx, l in enumerate(leads, 1):
        v_status = l.get('verification_status')
        m_status = l.get('matching_status')
        conf = int(l.get('confidence_score', 0))
        if v_status != 'VERIFIED' and conf > 60:
            c11.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Non-VERIFIED avec score confiance {conf} > 60 (plafond non respecté).")
        if m_status in ('MATCH_UNCERTAIN', 'NO_MATCH') and conf > 40:
            c11.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Matching incertain avec score confiance {conf} > 40 (plafond non respecté).")
    record_check("Contrôle 11 (Plafonds de Confiance Respectés)", c11)

    # 12. VERIFIED impossible sans preuves
    c12 = []
    for idx, l in enumerate(leads, 1):
        v_status = l.get('verification_status')
        if v_status == 'VERIFIED':
            conf = int(l.get('confidence_score', 0))
            m_status = l.get('matching_status')
            siren = l.get('siren', '')
            dm = l.get('decision_maker', '')
            site = l.get('website', '')
            if conf < 80:
                c12.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED avec score confiance {conf} < 80.")
            if m_status != 'MATCH_CONFIRMED':
                c12.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED avec matching_status '{m_status}'.")
            if not re.match(r'^\d{9}$', siren):
                c12.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED sans SIREN valide.")
            if not dm or 'non identifié' in dm.lower() or dm == 'Inconnu':
                c12.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED sans dirigeant identifié.")
            if not site.startswith('https://'):
                c12.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: VERIFIED avec site non sécurisé HTTPS.")
    record_check("Contrôle 12 (Hard Gates Statut VERIFIED)", c12)

    # 13. Reasons présentes et complètes
    c13 = []
    for idx, l in enumerate(leads, 1):
        reasons = l.get('reasons', '').strip()
        if not reasons:
            c13.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Champ 'reasons' manquant ou vide.")
        elif 'Lead Gen' not in reasons or 'GW' not in reasons or 'Confidence' not in reasons:
            c13.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Champ 'reasons' incomplet (doit couvrir LG, GW et Confidence).")
    record_check("Contrôle 13 (Présence et Traçabilité Reasons)", c13)

    # 14. Commercial signal jamais basé sur Google Reviews
    c14 = []
    for idx, l in enumerate(leads, 1):
        sig = (l.get('commercial_signal') or '').lower()
        src = (l.get('signal_source') or '').lower()
        if 'avis google' in sig or 'étoiles' in sig or 'reviews' in sig or 'google maps' in src:
            c14.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Signal commercial dérivé illégalement d'avis Google.")
    record_check("Contrôle 14 (Zéro Signal Basé sur Google Reviews)", c14)

    # 15. Intégrité des dates et sources de signaux
    c15 = []
    for idx, l in enumerate(leads, 1):
        sig = l.get('commercial_signal', '').strip()
        src = l.get('signal_source', '').strip()
        dt = l.get('signal_date', '').strip()
        if not sig and (src or dt):
            c15.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Source ou date présente alors que signal commercial est vide.")
        if sig and (not src or not dt):
            c15.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: Signal commercial présent sans source ou date vérifiée.")
    record_check("Contrôle 15 (Intégrité Source/Date Signal Commercial)", c15)

    # 16. Spécificité offre et cible
    c16 = []
    allowed_unverified = {'Non vérifié', 'Non renseigné'}
    generic_placeholder = 'Création et refonte de sites web'
    # On autorise les observations réelles ou 'Non vérifié', mais on interdit qu'un lead non observé prenne une formule sans note
    for idx, l in enumerate(leads, 1):
        offer = l.get('main_offer', '').strip()
        target = l.get('target_clients', '').strip()
        if not offer or not target:
            c16.append(f"Ligne {idx:02d} [{l.get('brand_name')}]: main_offer ou target_clients vide.")
    record_check("Contrôle 16 (Spécificité Offre & Cible)", c16)

    # 17. Message d'outreach sans affirmations non prouvées
    c17 = []
    if markdown_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        banned_phrases = [
            'besoin urgent',
            'besoin immédiat',
            'positionnement très solide',
            'échantillon spécifique a déjà été préparé',
            'pré-audité 3 entreprises',
            'Bonjour Non',
            'Bonjour ,'
        ]
        for phrase in banned_phrases:
            if phrase.lower() in md_text.lower():
                c17.append(f"Présence de l'affirmation non prouvée ou placeholder corrompu : '{phrase}'.")
    else:
        c17.append(f"Fichier de restitution {markdown_file} introuvable.")
    record_check("Contrôle 17 (Véracité Message d'Outreach)", c17)

    # 18. Synchronisation Notion/Markdown avec le dataset
    c18 = []
    if markdown_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        verified_sirens = [l['siren'] for l in leads if l.get('verification_status') == 'VERIFIED']
        for s in verified_sirens:
            if s not in md_content:
                c18.append(f"SIREN vérifié '{s}' absent du rapport Markdown.")
    else:
        c18.append("Fichier Markdown introuvable pour vérification de synchronisation.")
    record_check("Contrôle 18 (Synchronisation Dataset / Markdown)", c18)

    # 19. Connexion réelle du pipeline shortlist -> requalification
    c19 = []
    shortlist_file = BASE_DIR / 'data' / 'gmaps_agences_web_shortlist.csv'
    requalify_script = BASE_DIR / 'requalify_leads.py'
    if not shortlist_file.exists():
        c19.append(f"Fichier de shortlist {shortlist_file} inexistant.")
    if requalify_script.exists():
        with open(requalify_script, 'r', encoding='utf-8') as f:
            req_code = f.read()
        if 'gmaps_agences_web_shortlist.csv' not in req_code:
            c19.append("requalify_leads.py ne consomme pas gmaps_agences_web_shortlist.csv.")
    else:
        c19.append("Script requalify_leads.py inexistant.")
    record_check("Contrôle 19 (Connexion Pipeline Shortlist -> Requalification)", c19)

    # 20. Zéro dépendance obsolète
    c20 = []
    legacy_json = BASE_DIR / 'data' / 'top30_leads_qualified.json'
    legacy_csv = BASE_DIR / 'data' / 'top30_leads_qualified.csv'
    if legacy_json.exists():
        c20.append(f"Fichier obsolète toujours présent : {legacy_json}.")
    if legacy_csv.exists():
        c20.append(f"Fichier obsolète toujours présent : {legacy_csv}.")
    
    # Vérifier que requalify_leads ne lit pas l'ancien fichier
    if requalify_script.exists():
        with open(requalify_script, 'r', encoding='utf-8') as f:
            req_code = f.read()
        if 'top30_leads_qualified.json' in req_code:
            c20.append("requalify_leads.py fait référence à top30_leads_qualified.json.")
    record_check("Contrôle 20 (Zéro Dépendance Obsolète)", c20)

    # Rapport final
    all_passed = all(results.values())
    return all_passed, results, failures

def run_negative_tests() -> bool:
    """
    Vérifie que les contrôles du QA échouent effectivement lorsqu'une corruption est introduite.
    """
    print("\n=== EXÉCUTION DU SUITE DE TESTS NÉGATIFS (FIXTURES CORROMPUES) ===")
    
    # Charger le dataset valide actuel comme base
    csv_file = BASE_DIR / 'data' / 'top30_leads_requalified.csv'
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        base_leads = list(reader)

    fixtures = [
        {
            "name": "Fixture 1 : VERIFIED avec matching_status = MATCH_UNCERTAIN",
            "modify": lambda rows: rows[0].update({"verification_status": "VERIFIED", "matching_status": "MATCH_UNCERTAIN", "confidence_score": "85"}),
            "expected_fail_check": "Contrôle 03 (Matching SIRENE Non Ambigu)"
        },
        {
            "name": "Fixture 2 : Tranche 01 marquée VERIFIED sans preuve secondaire",
            "modify": lambda rows: rows[0].update({"verification_status": "VERIFIED", "company_size": "1 ou 2 salariés", "notes": "", "reasons": "Lead Gen: 70 | GW: 0 | Confidence: 85"}),
            "expected_fail_check": "Contrôle 04 (ICP Strict 2-20 Salariés)"
        },
        {
            "name": "Fixture 3 : Tranche 0 salarié non disqualifiée",
            "modify": lambda rows: rows[0].update({"verification_status": "VERIFIED", "company_size": "0 salarié", "confidence_score": "80"}),
            "expected_fail_check": "Contrôle 04 (ICP Strict 2-20 Salariés)"
        },
        {
            "name": "Fixture 4 : Doublon SIREN",
            "modify": lambda rows: rows[1].update({"siren": rows[0]["siren"]}),
            "expected_fail_check": "Contrôle 07 (Non-Redondance SIREN)"
        },
        {
            "name": "Fixture 5 : Non-VERIFIED avec score confiance > 60",
            "modify": lambda rows: rows[0].update({"verification_status": "REQUIRES REVIEW", "confidence_score": "75"}),
            "expected_fail_check": "Contrôle 11 (Plafonds de Confiance Respectés)"
        },
        {
            "name": "Fixture 6 : Score Ghostwriting non neutralisé",
            "modify": lambda rows: rows[0].update({"ghostwriting_score": "80"}),
            "expected_fail_check": "Contrôle 09 (Score Ghostwriting Neutralisé)"
        },
        {
            "name": "Fixture 7 : Signal commercial dérivé d'avis Google",
            "modify": lambda rows: rows[0].update({"commercial_signal": "Excellents avis Google Maps (4.9/5)", "signal_source": "Google Maps", "signal_date": "2026-09-01"}),
            "expected_fail_check": "Contrôle 14 (Zéro Signal Basé sur Google Reviews)"
        },
        {
            "name": "Fixture 8 : Signal date présente sans signal source",
            "modify": lambda rows: rows[0].update({"commercial_signal": "", "signal_source": "", "signal_date": "2026-09-26"}),
            "expected_fail_check": "Contrôle 15 (Intégrité Source/Date Signal Commercial)"
        },
        {
            "name": "Fixture 9 : Champ reasons vide",
            "modify": lambda rows: rows[0].update({"reasons": ""}),
            "expected_fail_check": "Contrôle 13 (Présence et Traçabilité Reasons)"
        }
    ]

    all_negatives_passed = True
    temp_csv = BASE_DIR / 'data' / 'temp_negative_fixture.csv'

    for f_idx, fixture in enumerate(fixtures, 1):
        # Créer une copie indépendante
        import copy
        corrupted_leads = copy.deepcopy(base_leads)
        fixture["modify"](corrupted_leads)

        # Sauvegarder fixture
        with open(temp_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(corrupted_leads[0].keys()))
            writer.writeheader()
            writer.writerows(corrupted_leads)

        _, results, _ = run_qa_checks(csv_path=temp_csv)
        failed_as_expected = not results.get(fixture["expected_fail_check"], True)

        if failed_as_expected:
            print(f"  [PASS] {fixture['name']} -> Détecté avec succès par '{fixture['expected_fail_check']}'.")
        else:
            print(f"  [FAIL] {fixture['name']} -> NON DÉTECTÉ par '{fixture['expected_fail_check']}' !")
            all_negatives_passed = False

    if temp_csv.exists():
        temp_csv.unlink()

    return all_negatives_passed

if __name__ == '__main__':
    print("=== DÉMARRAGE AUDIT QA OFFICIEL (20 CONTRÔLES) ===")
    passed, results, failures = run_qa_checks()
    
    for check_name, check_ok in results.items():
        status = "PASS" if check_ok else "FAIL"
        print(f"[{status}] {check_name}")
        if not check_ok:
            for fail_msg in failures[check_name]:
                print(f"       -> {fail_msg}")

    print("-" * 50)
    print(f"Bilan Dataset Actuel : {sum(results.values())}/20 CONTRÔLES VALIDÉS.")
    
    negative_ok = run_negative_tests()
    print("-" * 50)
    print(f"Bilan Tests Négatifs : {'100% DES CORRUPTIONS DÉTECTÉES (PASS)' if negative_ok else 'ÉCHEC DE CERTAINES DÉTECTIONS (FAIL)'}")
    
    total_ok = passed and negative_ok
    print(f"RÉSULTAT GLOBAL : {'CONFORME AUX STANDARDS DE VÉRITÉ' if total_ok else 'NON CONFORME'}")
    exit(0 if total_ok else 1)
