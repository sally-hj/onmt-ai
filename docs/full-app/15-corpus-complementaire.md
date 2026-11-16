# Corpus synthétique complémentaire et diagnostics

Les règles des trois références Finance, Commercial et Performance restent dans [Données](03-donnees.md). Elles partagent 2 100 clés mensuelles chacune : janvier 2021 à octobre 2026, six villes et cinq marchés. Les trois fichiers existants ne sont jamais réécrits par `app.data_access.supplement`. Les compléments ne sont pas des observations officielles.

## Préparation et reproductibilité

Depuis la racine, après installation :

```powershell
$env:PYTHONPATH = "$PWD\backend"
.\.venv\Scripts\python.exe -m app.data_access.supplement
```

Le générateur relit les QVD natifs, calcule les lignes déterministes, écrit les nouveaux fichiers puis les relit. Si un complément existe avec un autre contenu, il refuse de l'écraser et demande un nouveau répertoire/version. Le manifeste `local_data/qvd-synthetic/supplement/manifest.json` conserve version `supplement-v2`, nombre de lignes, empreintes sémantiques et empreintes binaires des références. Même entrée et même version donnent les mêmes valeurs ; l'identité binaire de deux créations indépendantes n'est pas promise car l'en-tête QVD contient des métadonnées.

| QVD complémentaire | Lignes / relations | Règles et unités |
| --- | --- | --- |
| `extension.qvd` | 2 100 ; même `record_key`, mois, ville et marché que les trois références | Conversions = arrondi(4 % des clics) ; entrées événementielles = arrondi(12 % des arrivées) ; capacité = arrondi(20 % des arrivées) ; visites web = arrondi(2,5 × clics) ; engagements = arrondi(6 % des impressions). |
| Même extension, macroéconomie | Grandeurs allouées à chaque clé, jamais un total national répété par marché | PIB fictif = arrivées × 50 000 MAD ; valeur ajoutée tourisme = 8 % du PIB ; emplois tourisme = arrondi(8 % des arrivées), emplois totaux = arrondi(80 % des arrivées). Ce sont des équivalents alloués, pas des emplois effectivement recensés. |
| Même extension, marge attribuée | Accès logique `extension_finance`, réservé au domaine Finance | Marge fictive = arrondi(1,2 × dépenses). ROI = (marge − coût) / coût ; résultat proche de 20 %, déterminé par construction et sans preuve de causalité. Le mapping Performance n'expose pas cette colonne. |
| `competitiveness.qvd` | 2 100 ; mêmes clés, 14 piliers TTCI | Pilier j = arrondi à quatre décimales de 3 + 0,5 × ((indice ville + j) modulo 5) + 0,1 × sin(mois × π/6) + 0,02 × (année − 2021). Scores fictifs de 1 à 7, distincts des données financières. |
| `international.qvd` | 420 ; 70 mois × six comparateurs, marché Total | Arrivées = arrondi((100 000 + 40 000 × i) × (1 + 0,02 × (i + 1))^(année − 2021) × (1 + 0,18 × sin((mois − i) × π/6))). i parcourt Maroc, Tunisie, Espagne, Dubaï, Thaïlande, Rwanda de zéro à cinq. |
| `regional.qvd` | 840 ; 70 mois × douze régions, marché Total | Arrivées = arrondi((50 000 + 10 000 × i) × (1 + g)^(année − 2021) × (1 + 0,1 × sin(mois × π/6))). g alterne 10 %, 10 %, 2 %, 2 % ; part relative cible alterne 1,5 ; 0,5 ; 1,5 ; 0,5. |

Les grands montants entiers dépassant la capacité QVD signée sur 32 bits sont écrits en double exact dans ce corpus, sous 2^53. Les compléments internationaux/régionaux sont des catalogues partagés fictifs distincts ; ils n'élargissent pas l'accès aux QVD internes. Les douze noms régionaux viennent de l'[Association des Régions du Maroc](https://www.regions-maroc.ma/indicateurs-des-regions/). Aucune statistique de ce site n'est copiée.

Pour les comparateurs internationaux : nuitées = arrivées × (3 + i modulo 3), chambres vendues = arrondi(nuitées / 1,8), disponibles = arrondi(vendues / (0,6 + 0,025 × i)), sièges = 2 × arrivées, réservations = arrondi(0,7 × arrivées), recettes = nuitées × (700 + 50 × i) MAD, recettes chambres = vendues × (600 + 30 × i) MAD. PIB = arrivées × 50 000 MAD et valeur ajoutée = arrivées × 4 000 MAD. Tous les montants sont générés directement en MAD de scénario ; aucune conversion de monnaie réelle.

Pour les régions : nuitées = 3 × arrivées, vendues = arrondi(nuitées / 1,8), disponibles = 2 × vendues, sièges = 2 × arrivées, réservations = arrondi(0,7 × arrivées), recettes = nuitées × 700 MAD, recettes chambres = vendues × 600 MAD ; mêmes conventions PIB/valeur ajoutée que les comparateurs. Ces régions forment un scénario distinct ; elles ne sont pas une ventilation des six villes de référence et leurs totaux ne doivent pas être rapprochés.

## Axes, seuils et scénarios attendus

- BCG : x = arrivées de la destination / arrivées du plus grand concurrent ; y = croissance annuelle du **marché total** sur les mêmes mois. International : marché total = arrondi(arrivées × (2,5 + 0,15 × i)), concurrent = arrondi(arrivées / (0,7 + 0,15 × i)). Régions : marché total = arrondi(arrivées × (2 + 1 / part cible)), concurrent = arrondi(arrivées / part cible). Seuils par défaut : part relative 1 et croissance 5 %. Les quatre combinaisons régionales produisent les quatre quadrants. Une absence de référence/concurrent donne un résultat indéterminé.
- Valeur–Volume : x = somme des arrivées ; y = somme des recettes / somme des arrivées, en MAD par arrivée. Les seuils sont configurables ; ce découpage est descriptif et sensible au périmètre.
- Butler : au moins cinq années complètes consécutives ; dernières variations élevées, stables ou négatives donnent un stade **possible**, jamais certain. Historique insuffisant ou signal mixte : indéterminé. Confiance faible, aucune validation empirique du cycle de vie.
- Carte : coordonnées de six villes vérifiées par Wikidata P625, liens et attribution dans `config/geography.json`. Position réelle, valeur fictive ; surface des cercles proportionnelle à la valeur relative, filtre et info-bulle. Aucun fond réseau ou contour administratif inventé.
- Scénario : indicateur additif seulement ; hypothèse comprise entre −90 % et +100 %. Sur 80 000 nuitées, choc −10 % donne **72 000**. C'est une hypothèse arithmétique, pas une fréquentation observée ou une prédiction causale.
- Référence temporelle : Agadir février 2025 = **80 000**, février 2024 = **100 000**, variation **−20 %** ; Marrakech **165 000 / 150 000 = +10 %**. Les tests utilisent ces constantes indépendantes.

## Calculs indépendants et droits

Les seize attendus de base proviennent de `examples/synthetic-reference.json`. Les trente nouveaux attendus de `test_extended_analytics.py` sont des constantes manuelles sur un minijeu distinct : par exemple 25 arrivées, 100 nuitées et 20 000 MAD de recettes donnent **800 MAD par arrivée**. La recette de génération n'est pas appelée pour produire ces réponses attendues. Des séries plates ou périodiques construisent d'autres cas indépendants pour ISM, TCA/TCAM, Butler et les prévisions.

Une deuxième génération et la lecture native contrôlent la reproductibilité ; cela complète l'oracle métier sans le remplacer. Les tests vérifient aussi clés absentes, unités, divisions par zéro, scores non additifs, refus Finance, filtrage territorial et version des sources. Le corpus étant public et reproductible, les corrélations de sa recette peuvent révéler indirectement des valeurs ; les permissions démontrent les restrictions applicatives et ne promettent pas une confidentialité statistique industrielle.

Le [catalogue](12-catalogue-et-conventions.md) décrit chaque KPI ; la [matrice](01-couverture-cps.md) distingue ces conventions pédagogiques des exigences industrielles.
