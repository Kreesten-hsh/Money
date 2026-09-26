import json

with open('/home/hasashi/Bureau/Money/data/top30_leads_qualified.json', 'r', encoding='utf-8') as f:
    leads = json.load(f)

md = []
md.append('# 🎯 Lead Intelligence Room — Agences Web France')
md.append('')
md.append('> **Campagne** : AI Lead Intelligence & Founder Ghostwriting  ')
md.append('> **Dernière mise à jour** : 26 Septembre 2026  ')
md.append('> **Statut** : Échantillon MVP Validé — Prêt pour Outreach Manuel  ')
md.append('> **Volume total qualifié** : 30 agences vérifiées (Score 100/100) | **Leads Prioritaires** : 5 agences cibles directes')
md.append('')
md.append('---')
md.append('')
md.append('## 01 — Campaign Overview')
md.append('')
md.append('Cette Lead Intelligence Room documente l\'échantillon initial de validation commerciale pour le lancement des deux offres B2B synergiques :')
md.append('1. **AI Lead Intelligence** : Détection et qualification chirurgicale de comptes cibles PME/B2B prêts pour de la refonte ou des services digitaux.')
md.append('2. **Founder LinkedIn Ghostwriting** : Transformation de l\'expertise et des retours d\'expérience des fondateurs d\'agences en contenu d\'autorité à fort taux de conversion.')
md.append('')
md.append('### Métriques Clés du Lot MVP')
md.append('- **Total entreprises brutes scrapées** : 340 agences sur 6 métropoles (Paris, Marseille, Lyon, Toulouse, Bordeaux, Nantes).')
md.append('- **Entreprises uniques filtrées** : 334 agences.')
md.append('- **Échantillon sélectionné** : 30 agences françaises (taux de complétude : 100% tél, 100% site web, notes Google >= 4.5/5).')
md.append('- **Objectif financier** : Validation de 2 à 3 pilotes payants (400 000 à 600 000 FCFA chacun) pour dépasser l\'objectif plancher de 1 000 000 FCFA avant le 31 décembre 2026.')
md.append('')
md.append('---')
md.append('')
md.append('## 02 — ICP & Criteria')
md.append('')
md.append('### Profil Client Idéal (ICP)')
md.append('- **Activité** : Agence de création de sites web, marketing digital, branding et SEO.')
md.append('- **Taille cible** : PME / Studios de 2 à 20 collaborateurs (trésorerie active, décideur accessible).')
md.append('- **Localisation** : France métropolitaine (priorité aux grandes métropoles économiques).')
md.append('- **Preuve sociale** : Minimum 15 avis Google certifiés avec une note moyenne supérieure ou égale à 4.5/5.')
md.append('- **Points de friction résolus** :')
md.append('  - *Leadgen* : Dépendance au bouche-à-oreille et cycles de vente irréguliers.')
md.append('  - *Ghostwriting* : Manque de temps du fondateur pour publier de manière consistante sur LinkedIn malgré une expertise pointue.')
md.append('')
md.append('---')
md.append('')
md.append('## 03 — Qualified Leads (Lot des 30)')
md.append('')
md.append('| # | Entreprise | Ville | Téléphone | Avis / Note | Site Web | Statut |')
md.append('|---|---|---|---|---|---|---|')

for i, l in enumerate(leads, 1):
    note = f"{float(l['review_rating']):.1f} ({l['review_count']} avis)"
    clean_title = l['title'].split('|')[0].strip()
    phone = l['phone'] if l['phone'] else 'N/A'
    md.append(f"| {i:02d} | **{clean_title}** | {l['city']} | `{phone}` | {note} | [Consulter]({l['website']}) | {l['status']} |")

md.append('')
md.append('---')
md.append('')
md.append('## 04 — Priority Leads (Fiches Décisionnelles Détaillées)')
md.append('')

priority_data = [
    {
        'num': '01',
        'name': 'LACKY',
        'city': 'Marseille (13011)',
        'site': 'https://www.lacky.fr/',
        'phone': '+33 4 91 91 47 05',
        'category': 'Concepteur de sites Web / Spécialiste Wix & SEO',
        'fit': '100/100',
        'conf': '95/100',
        'rating': '4.9/5 (66 avis Google)',
        'target_reason': 'Positionnement spécifique Wix Studio & SEO combiné à l\'intégration IA pour les TPE/PME.',
        'signal': 'Mise en avant explicite de l\'IA et du SEO sur leur page d\'accueil ; forte satisfaction client locale.',
        'decideur': 'Direction générale / Fondateur LACKY',
        'angle': 'Partenariat d\'apport d\'affaires (listes de prospects PME à équiper) + Ghostwriting LinkedIn orienté "Wix Studio vs WordPress pour les PME".',
        'msg': 'Bonjour, j\'ai remarqué votre positionnement hybride Wix Studio + IA sur Marseille. Vos 66 retours clients confirment une excellente adoption. Pour vos clients PME qui cherchent plus que de la simple visibilité technique : nous pré-qualifions des listes de prospects B2B ultra-contextualisées prêtes à closer. Seriez-vous ouvert à tester un échantillon de 10 leads vérifiés sans engagement ?'
    },
    {
        'num': '02',
        'name': '4Beez',
        'city': 'Paris (8ème)',
        'site': 'https://4beez.agency/',
        'phone': '+33 1 76 54 30 97',
        'category': 'Agence Digitale, Branding & Stratégies d\'Acquisition',
        'fit': '100/100',
        'conf': '95/100',
        'rating': '4.9/5 (99 avis Google)',
        'target_reason': 'Agence parisienne établie avec 99 avis clients, orientée branding et acquisition de leads.',
        'signal': 'Campagnes de recrutement en cours (contact@4beez-inc.com), forte vélocité commerciale.',
        'decideur': 'Direction associée / Pôle Growth 4Beez',
        'angle': 'Founder Ghostwriting pour valoriser la vision marque des dirigeants sur LinkedIn + flux de leads pour leurs offres d\'acquisition.',
        'msg': 'Bonjour, avec 99 retours clients élogieux sur votre pôle branding et acquisition, vos études de cas méritent une visibilité continue sur LinkedIn. Nous aidons les dirigeants d\'agences à transformer leurs succès clients en prises de parole stratégiques régulières, tout en fournissant des flux de comptes clés vérifiés. Discutons-en 10 minutes cette semaine.'
    },
    {
        'num': '03',
        'name': 'Youdemus',
        'city': 'Paris & Bordeaux',
        'site': 'https://www.youdemus.fr/',
        'phone': '+33 1 84 17 26 34',
        'category': 'Agence Web Éco-conception & Maintenance (Fondée en 2013)',
        'fit': '100/100',
        'conf': '95/100',
        'rating': '5.0/5 (63 avis Google)',
        'target_reason': 'Acteur solide avec 13 ans d\'ancienneté et un positionnement différenciant sur l\'éco-conception.',
        'signal': 'Double implantation Paris-Bordeaux, forte présence sur les enjeux RSE et maintenance logicielle.',
        'decideur': 'Direction générale Youdemus',
        'angle': 'Thought Leadership LinkedIn sur la réduction de l\'empreinte carbone numérique (attracteur B2B RSE) + ciblage d\'entreprises soumises aux audits RSE.',
        'msg': 'Bonjour, votre engagement sur l\'éco-conception web depuis 2013 est particulièrement visionnaire. Cet angle est aujourd\'hui un puissant levier d\'acquisition grands comptes sur LinkedIn. Nous structurons votre ghostwriting exécutif et détectons les entreprises qui préparent leur transition numérique responsable. Prenons contact pour échanger sur un format pilote.'
    },
    {
        'num': '04',
        'name': 'MASHVP',
        'city': 'Toulouse',
        'site': 'https://mashvp.com/',
        'phone': '+33 9 62 62 11 51',
        'category': 'Design Studio & Conception d\'Écrans Web',
        'fit': '100/100',
        'conf': '90/100',
        'rating': '4.9/5 (51 avis Google)',
        'target_reason': 'Studio créatif de premier plan avec identité de marque léchée et réputation nationale.',
        'signal': 'Portfolio très actif sur les produits digitaux et interfaces sur-mesure.',
        'decideur': 'Direction de création / Fondateur MASHVP',
        'angle': 'Ghostwriting axé sur le design systémique et le product design + détection de scaleups venant de lever des fonds.',
        'msg': 'Bonjour, la qualité de réalisation visuelle de vos projets récents à Toulouse se démarque nettement. Nous accompagnons des studios d\'élite en leur apportant des signaux faibles sur les startups B2B qui amorcent une refonte après un tour de table. Seriez-vous disponible pour un court appel exploratoire ?'
    },
    {
        'num': '05',
        'name': 'Web Tribe Studio',
        'city': 'Bordeaux',
        'site': 'https://webtribe-studio.com/',
        'phone': '+33 7 72 38 27 81',
        'category': 'Agence Marketing Numérique & Création de Sites',
        'fit': '100/100',
        'conf': '95/100',
        'rating': '5.0/5 (58 avis Google)',
        'target_reason': 'Accompagnement de bout en bout des TPE/PME régionales avec une satisfaction maximale (5.0/5).',
        'signal': 'Offres packagées très claires (vitrine, boutique en ligne, structuration de projet).',
        'decideur': 'Pascal Sagory / Direction Web Tribe',
        'angle': 'Apport de listes B2B locales dans le Sud-Ouest prêtes à engager une transition digitale.',
        'msg': 'Bonjour Pascal, votre accompagnement des PME régionales en Gironde bénéficie d\'une excellente réputation (58 avis 5/5). Afin d\'alimenter directement vos équipes en projets qualifiés sur les prochaines semaines, nous pouvons vous préparer 20 dossiers de PME locales en phase d\'investissement digital. Quand seriez-vous disponible pour un tour rapide ?'
    }
]

for p in priority_data:
    md.append(f"### {p['num']} — {p['name']} ({p['city']})")
    md.append(f"- **Catégorie** : {p['category']}")
    md.append(f"- **Site Web** : [{p['site']}]({p['site']}) | **Téléphone** : `{p['phone']}`")
    md.append(f"- **Fit Score** : {p['fit']} | **Indice de Confiance** : {p['conf']}")
    md.append(f"- **Preuve Sociale** : {p['rating']}")
    md.append(f"- **Raison du ciblage** : {p['target_reason']}")
    md.append(f"- **Signal commercial identifié** : {p['signal']}")
    md.append(f"- **Interlocuteur cible** : {p['decideur']}")
    md.append(f"- **Angle stratégique recommandé** : {p['angle']}")
    md.append("- **Message d'outreach personnalisé** :")
    md.append(f"> \"{p['msg']}\"")
    md.append('')

md.append('---')
md.append('')
md.append('## 05 — Outreach Queue')
md.append('')
md.append('### Protocole d\'Exécution Manuel (Zero Spam)')
md.append('1. **Canal 1 (Prioritaire)** : Message privé ou InMail LinkedIn ciblé vers le fondateur/associé.')
md.append('2. **Canal 2 (Complémentaire)** : Appel téléphonique de courtoisie direct via le numéro officiel pour valider l\'ouverture à recevoir un échantillon gratuit de 3 à 5 leads.')
md.append('3. **Cadencement** : 5 contacts par jour sur 6 jours (total 30 leads traités sans risque de saturation ni perte de contrôle).')
md.append('4. **Règle d\'or** : Livrer la valeur d\'abord (échantillon de 3 fiches prêtes à l\'emploi) avant toute demande d\'engagement financier.')
md.append('')
md.append('---')
md.append('')
md.append('## 06 — Market Signals')
md.append('')
md.append('Les analyses Firecrawl et les extractions terrain confirment :')
md.append('- **Tension sur l\'acquisition client** : La majorité des agences s\'appuient sur des formulaires passifs et le réseau direct.')
md.append('- **Montée en puissance des arguments IA & Éco-conception** : Ces deux leviers offrent un terreau idéal pour du Founder Ghostwriting crédible et différenciant.')
md.append('- **Disponibilité des coordonnées** : 100% des décideurs ou standards de direction sont joignables directement par téléphone avec une géolocalisation vérifiée.')
md.append('')
md.append('---')
md.append('')
md.append('## 07 — Sources & Evidence')
md.append('')
md.append('- **Moteur de découverte primaire** : Google Maps Scraper (Conteneur local Docker, 340 extractions brutes).')
md.append('- **Validation technique des sites** : Scrapes profonds Firecrawl (analyse DOM, métadonnées, extraction d\'emails et propositions de valeur).')
md.append('- **Dédoublonnage & Nettoyage** : Scripts Python automatisés de conformité RGPD et d\'intégrité des numéros de téléphone.')
md.append('- **Fichiers sources locaux** :')
md.append('  - Données brutes : `data/gmaps_agences_web_raw.csv`')
md.append('  - Dataset qualifié : `data/top30_leads_qualified.csv` et `data/top30_leads_qualified.json`')
md.append('')
md.append('---')
md.append('')
md.append('## 08 — Delivery History & Prochaines Étapes')
md.append('')
md.append('- **26 Septembre 2026** : Scrape initial, filtration du Top 30 et création de la Lead Intelligence Room Notion.')
md.append('- **Prochaine étape** : Déclenchement des prises de contact manuelles sur les 5 leads prioritaires avec proposition du pilote gratuit/payant.')

full_content = '\n'.join(md)

with open('/home/hasashi/Bureau/Money/data/lead_intelligence_room.md', 'w', encoding='utf-8') as f:
    f.write(full_content)

print(f"File created successfully. Total characters: {len(full_content)}")
