import csv
import re
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_qa_checks():
    csv_file = BASE_DIR / 'data' / 'top30_leads_requalified.csv'
    markdown_file = BASE_DIR / 'data' / 'lead_intelligence_room.md'

    if not csv_file.exists():
        print(f"FAIL: Fichier {csv_file} introuvable.")
        return False

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        leads = list(reader)

    print(f"=== MONEY QA PROTOCOL CHECK ===")
    print(f"Fichier audité : {csv_file.name} ({len(leads)} lignes)")
    print("-" * 50)

    results = {}
    failures = {}

    # Contrôle 1 : Intégrité des URLs
    c1_failures = []
    for i, l in enumerate(leads, 1):
        site = l.get('website', '')
        notes = l.get('notes', '')
        if not site:
            c1_failures.append((i, l.get('brand_name'), "Site web manquant"))
        elif not site.startswith('https://') and 'site inaccessible' not in notes:
            c1_failures.append((i, l.get('brand_name'), f"Non HTTPS et sans note d'inaccessibilité ({site})"))
    results['Contrôle 1 (Intégrité des URLs)'] = len(c1_failures) == 0
    failures['Contrôle 1 (Intégrité des URLs)'] = c1_failures

    # Contrôle 2 : Preuve Légale
    c2_failures = []
    for i, l in enumerate(leads, 1):
        if l.get('verification_status') == 'VERIFIED':
            siren = l.get('siren', '')
            if not re.match(r'^\d{9}$', siren):
                c2_failures.append((i, l.get('brand_name'), f"SIREN invalide pour lead VERIFIED: '{siren}'"))
            if not l.get('evidence_url'):
                c2_failures.append((i, l.get('brand_name'), "Evidence URL manquante pour lead VERIFIED"))
    results['Contrôle 2 (Preuve Légale)'] = len(c2_failures) == 0
    failures['Contrôle 2 (Preuve Légale)'] = c2_failures

    # Contrôle 3 : Contrôle d'Effectif
    c3_failures = []
    for i, l in enumerate(leads, 1):
        status = l.get('verification_status')
        size = l.get('company_size', '')
        if 'salarié déclaré (Non employeur)' in size or '0 salarié' in size:
            if status != 'DISQUALIFIED':
                c3_failures.append((i, l.get('brand_name'), f"Tranche 0 salarié non disqualifiée (status={status})"))
        if status == 'VERIFIED' and 'avis' in l.get('company_size_source', '').lower():
            c3_failures.append((i, l.get('brand_name'), "Effectif dérivé des avis Google interdit"))
    results['Contrôle 3 (Contrôle d\'Effectif)'] = len(c3_failures) == 0
    failures['Contrôle 3 (Contrôle d\'Effectif)'] = c3_failures

    # Contrôle 4 : Non-Redondance
    c4_failures = []
    seen_domains = {}
    seen_phones = {}
    seen_sirens = {}
    for i, l in enumerate(leads, 1):
        site = l.get('website', '')
        if site:
            domain = urllib.parse.urlsplit(site).netloc.lower().replace('www.', '')
            if domain in seen_domains:
                c4_failures.append((i, l.get('brand_name'), f"Doublon de domaine ({domain}) déjà vu ligne {seen_domains[domain]}"))
            else:
                seen_domains[domain] = i
        phone = re.sub(r'\D', '', l.get('public_phone', ''))
        if phone:
            if phone in seen_phones:
                c4_failures.append((i, l.get('brand_name'), f"Doublon de téléphone ({phone}) déjà vu ligne {seen_phones[phone]}"))
            else:
                seen_phones[phone] = i
        siren = l.get('siren', '')
        if re.match(r'^\d{9}$', siren):
            if siren in seen_sirens:
                c4_failures.append((i, l.get('brand_name'), f"Doublon SIREN ({siren}) déjà vu ligne {seen_sirens[siren]}"))
            else:
                seen_sirens[siren] = i
    results['Contrôle 4 (Non-Redondance)'] = len(c4_failures) == 0
    failures['Contrôle 4 (Non-Redondance)'] = c4_failures

    # Contrôle 5 : Séparation des Scores
    c5_failures = []
    for i, l in enumerate(leads, 1):
        try:
            lg = int(l.get('lead_gen_score', -1))
            gw = int(l.get('ghostwriting_score', -1))
            conf = int(l.get('confidence_score', -1))
            if not (0 <= lg <= 100 and 0 <= gw <= 100 and 0 <= conf <= 100):
                c5_failures.append((i, l.get('brand_name'), f"Scores hors bornes 0-100: ({lg}, {gw}, {conf})"))
            if lg == 100 and gw == 100 and conf == 100:
                c5_failures.append((i, l.get('brand_name'), "Scores arbitraires à 100/100 par défaut"))
        except ValueError:
            c5_failures.append((i, l.get('brand_name'), "Scores non entiers"))
    results['Contrôle 5 (Séparation des Scores)'] = len(c5_failures) == 0
    failures['Contrôle 5 (Séparation des Scores)'] = c5_failures

    # Contrôle 6 : Cohérence Statut vs Confiance
    c6_failures = []
    for i, l in enumerate(leads, 1):
        status = l.get('verification_status')
        conf = int(l.get('confidence_score', 0))
        if status in ('REQUIRES REVIEW', 'PARTIALLY VERIFIED') and conf >= 75:
            c6_failures.append((i, l.get('brand_name'), f"Statut {status} incompatible avec score confiance >= 75 ({conf})"))
        if status == 'VERIFIED' and conf < 80:
            c6_failures.append((i, l.get('brand_name'), f"Statut VERIFIED requiert score confiance >= 80 ({conf})"))
    results['Contrôle 6 (Cohérence Statut vs Confiance)'] = len(c6_failures) == 0
    failures['Contrôle 6 (Cohérence Statut vs Confiance)'] = c6_failures

    # Contrôle 7 : Véracité du Décideur
    c7_failures = []
    for i, l in enumerate(leads, 1):
        dm = l.get('decision_maker', '')
        role = l.get('decision_maker_role', '')
        if not dm:
            c7_failures.append((i, l.get('brand_name'), "Champ decision_maker vide"))
        elif 'non identifié' in dm.lower() and role not in ('Inconnu', 'Non identifié'):
            c7_failures.append((i, l.get('brand_name'), f"Rôle incohérent pour dirigeant non identifié : {role}"))
    results['Contrôle 7 (Véracité du Décideur)'] = len(c7_failures) == 0
    failures['Contrôle 7 (Véracité du Décideur)'] = c7_failures

    # Contrôle 8 : Personnalisation du Message
    c8_failures = []
    if markdown_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        if 'Bonjour Non' in md_text or 'Bonjour ,' in md_text:
            c8_failures.append((0, "lead_intelligence_room.md", "Présence d'un message d'outreach corrompu ('Bonjour Non' ou 'Bonjour ,')"))
    else:
        c8_failures.append((0, "lead_intelligence_room.md", "Fichier de restitution introuvable"))
    results['Contrôle 8 (Personnalisation du Message)'] = len(c8_failures) == 0
    failures['Contrôle 8 (Personnalisation du Message)'] = c8_failures

    # Contrôle 9 : Conformité RGPD
    banned_columns = {'user_reviews', 'user_reviews_extended', 'owner', 'thumbnail', 'images', 'popular_times', 'plus_code', 'street_view_url', 'reviews_link', 'data_id', 'cid'}
    c9_failures = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        intersect = banned_columns.intersection(set(header))
        if intersect:
            c9_failures.append((1, "top30_leads_requalified.csv", f"Colonnes interdites RGPD détectées : {intersect}"))
    results['Contrôle 9 (Conformité RGPD)'] = len(c9_failures) == 0
    failures['Contrôle 9 (Conformité RGPD)'] = c9_failures

    # Contrôle 10 : Synchronisation Notion / Dataset
    c10_failures = []
    if markdown_file.exists():
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        verified_csv_sirens = [l['siren'] for l in leads if l.get('verification_status') == 'VERIFIED']
        for s in verified_csv_sirens:
            if s not in md_text:
                c10_failures.append((0, s, f"SIREN vérifié {s} absent de la synthèse markdown"))
    else:
        c10_failures.append((0, "lead_intelligence_room.md", "Fichier markdown manquant"))
    results['Contrôle 10 (Synchronisation Notion / Dataset)'] = len(c10_failures) == 0
    failures['Contrôle 10 (Synchronisation Notion / Dataset)'] = c10_failures

    # Affichage du rapport
    all_passed = True
    for control, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {control}")
        if not passed:
            all_passed = False
            for line_no, item_name, err in failures[control]:
                print(f"       -> Ligne {line_no:02d} [{item_name}] : {err}")

    print("-" * 50)
    print(f"Résultat final : {'TOUS LES CONTRÔLES SONT VALIDÉS (PASS)' if all_passed else 'ÉCHEC DE CERTAINS CONTRÔLES (FAIL)'}")
    return all_passed

if __name__ == '__main__':
    run_qa_checks()
