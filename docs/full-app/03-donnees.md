# Les QVD et leur dictionnaire

> Actualisation du 16 novembre : cette page explique le socle d'intégration. Pour les ajouts courants (46 KPI, diagnostics, spécialistes, tâches et présentation), consulter la [matrice](01-couverture-cps.md), les [conventions](12-catalogue-et-conventions.md), le [corpus complémentaire](15-corpus-complementaire.md) et le [guide des fichiers](13-fichiers-et-pipeline.md). Les résultats exécutés sont dans le [bilan courant](14-validation-completion.md).

**Référence définitive du projet pédagogique depuis la décision du professeur du 14 novembre 2026.** Aucun QVD réel ne sera fourni ni attendu avant le rendu. La conformité de ce corpus ne vaut pas validation des fonctions encore manquantes : voir la [matrice](01-couverture-cps.md).

Les QVD générés sont de vrais fichiers binaires au format Qlik, et non des CSV renommés. `synthetic.generate()` utilise PyQvd pour les écrire et les relit immédiatement pour comparer l'ensemble des cellules. La génération n'appelle jamais le moteur analytique pour fabriquer ses résultats attendus.

## Corpus normal

Graine `20261111`. Historique janvier 2021–octobre 2026, 70 mois. Six destinations : Agadir, Marrakech, Fès, Tanger, Rabat et Casablanca. Cinq marchés : France, Espagne, Allemagne, Royaume-Uni et Maroc. Chaque table contient 2 100 lignes.

Grain commun : **un mois × une destination × un marché**. La clé `record_key` concatène ces dimensions. Le rapprochement entre domaines est un à un à ce grain. Une table ne doit pas être jointe à une autre sans contrôle ; le moteur agrège chaque source séparément et vérifie l'égalité des périmètres avant les ratios entre domaines.

| Fichier | Champs physiques | Signification / unité |
| --- | --- | --- |
| Les trois | `record_key`, `period`, `destination`, `market` | Clé unique ; premier jour du mois ISO ; libellés des dimensions. |
| `commercial.qvd` | `nights`, `arrivals`, `seats`, `bookings` | Nuitées, arrivées, sièges disponibles et réservations ; quantités mensuelles. |
| `finance.qvd` | `budget_mad`, `spent_mad`, `committed_mad` | Budget prévu, dépenses exécutées et engagements, en dirhams MAD. Affectation mensuelle par destination/marché propre à ce jeu fictif. |
| `performance.qvd` | `room_revenue_mad`, `room_nights_sold`, `room_nights_available`, `travel_receipts_mad`, `impressions`, `clicks` | Revenus des chambres et recettes voyages en MAD ; chambres-nuits occupées/disponibles ; volumes promotionnels. |

Ces définitions et le mapping sont ceux du corpus pédagogique définitif. Ils ne prétendent pas reconstituer le patrimoine réel de l'ONMT ; cette représentativité n'est pas une condition du rendu. Les mesures de capacité et budgets sont réparties par marché : une capacité totale de destination n'est pas recopiée sur chaque marché.

La saisonnalité est une fonction sinusoïdale, avec une croissance historique modérée. Les dépenses utilisent un générateur pseudo-aléatoire fixe. Les nuitées d'Agadir en février sont imposées à 100 000 en 2024 et 80 000 en 2025. Marrakech : 150 000 puis 165 000. La part France d'Agadir en février 2025 vaut 25 600. Ces références indépendantes sont écrites dans `expected.json`.

Les relations entre budgets et résultats sont construites artificiellement. Une association dans ce corpus n'est jamais une preuve économique ni un rendement causal d'une campagne.

## Règles exactes de génération

Le générateur `onmt-synthetic-v1` parcourt année, mois, destination, marché dans un ordre fixe. `i` est l'indice de destination (Agadir = 0, Marrakech = 1, …), `s` la part du marché : France 0,32, Espagne 0,20, Allemagne 0,18, Royaume-Uni 0,20, Maroc 0,10. `round` est l'arrondi Python à l'entier le plus proche, égalités vers l'entier pair.

| Domaine | Règle pédagogique |
| --- | --- |
| Commercial, total mensuel avant répartition | `round((100000 + 13000*i) * (1 + 0.04*(année-2024)) * (1 + 0.24*sin((mois-5)*pi/6)))`. Pic saisonnier en août, creux en février avant les scénarios imposés. |
| Commercial, par marché | Nuitées = `round(total*s)` ; arrivées = `round(nuitées/(3.2+0.1*i))` ; sièges = `round(arrivées*1.7)` ; réservations = `round(arrivées*0.8)`. Les arrondis peuvent produire un léger écart hors scénarios entre somme des marchés et total théorique. |
| Finance | Budget = `round((160000+10000*i)*s*(1+0.03*(année-2021)))` ; dépenses = `round(budget*(0.72+0.18*U))` avec `U` issu du générateur pseudo-aléatoire à graine fixe ; engagements = `round(budget*0.95)`. |
| Performance, chambres | Chambres-nuits vendues = `round(nuitées/1.8)` ; disponibles = maximum de ce nombre et `round((15000+1500*i)*s*jours_du_mois/10)`. Ainsi l'occupation ne dépasse pas 100 %, sans prétendre reproduire une vraie capacité hôtelière. |
| Performance, montants | Revenus chambres = chambres-nuits vendues × `(620+25*i)` MAD ; recettes voyages = nuitées × `(740+30*i)` MAD. |
| Performance, promotion | Impressions = `round(dépenses*4.5)` ; clics = `round(dépenses*0.12)`. Cette liaison fabriquée sert à vérifier cohérence et calculs, pas à prouver une efficacité économique. |

Les dépenses varient avec la graine ; elles influencent aussi impressions et clics. Commercial reste inchangé quand seule la graine change. La graine de référence est `20261111` ; une autre graine est marquée `pedagogical_variant` dans le manifeste, sans devenir automatiquement la nouvelle référence définitive. Toute évolution des règles ou de l'ordre de génération exige une version du générateur et une revue des références indépendantes ; on ne réécrit pas automatiquement les attendus avec le moteur testé.

## Scénarios et attendus indépendants

| Question / scénario | Résultat de référence |
| --- | --- |
| Nuitées Agadir, février 2025 / février 2024 | 80 000 / 100 000 ; variation −20 %. |
| Nuitées Marrakech, février 2025 / février 2024 | 165 000 / 150 000 ; variation +10 %. |
| Nuitées Agadir, marché France, février 2025 | 25 600. |
| Budget et engagements Agadir, février 2025 | 179 200 MAD et 170 240 MAD. |
| Alerte annuelle, seuil −15 % | Signal Agadir février 2025 à −20 %, sans cause déduite ni doublon à une deuxième actualisation. |
| Demande sans données, hors historique | Valeur nulle et avertissement ; aucune extrapolation présentée comme observation. |
| Profil régional vers Finance ou territoire interdit | Refus avant calcul et avant transmission au LLM. |
| QVD défectueux séparé | Doublons, date invalide, valeur absente/négative bloquent le calcul. |

`examples/synthetic-reference.json` est versionné et écrit à la main. Il contient ces ancrages et un **oracle distinct de six lignes** (deux marchés × trois domaines) pour les seize KPI. Sur cet oracle : 100 nuitées, 25 arrivées, budget 2 000 MAD, dépenses 1 000 MAD, revenus chambres 6 000 MAD, 40 chambres-nuits vendues / 100 disponibles. Les attendus sont donc DMS = 4, exécution budgétaire = 50 %, dépenses/nuitée = 10 MAD, occupation = 40 %, RevPAR = 60 MAD et prix moyen = 150 MAD. Les autres sommes et le taux de clic de 5 % sont également figés dans le fichier.

Cet oracle n'est pas écrit par `generate()`, `calculate()` ou `_aggregate()`. Les distributions inégales entre marchés distinguent ratio des sommes et moyenne erronée de ratios. `expected.json` généré reste une aide de démonstration, pas l'unique preuve de correction.

## Fichiers générés hors Git

- `local_data/qvd-synthetic/*.qvd` : corpus normal.
- `manifest.json` : schéma v2, version du générateur, statut `pedagogical_final`, graine, périodes, dimensions, colonnes et nombres de lignes. `sha256` identifie les octets du QVD ; `semantic_sha256` identifie les colonnes/cellules décodées, indépendamment des métadonnées de création.
- `expected.json` : réponses de référence.
- `invalid/commercial-invalid.qvd` : doublon de clé/grain, valeur manquante, date invalide et nombre négatif. Ce fichier n'est pas chargé par la configuration normale.

La graine reproduit les **données**. Le conteneur QVD peut inclure des métadonnées de création ; il n'est pas promis que chaque fichier régénéré ait la même empreinte binaire.

Les tests effectuent deux générations de même graine et comparent toutes les cellules et empreintes sémantiques ; une autre graine doit modifier Finance et les mesures promotionnelles de Performance. Ils vérifient 2 100 clés uniques par table, mêmes clés/grains entre les trois domaines, 70 mois, unités, valeurs finies/non négatives, dépenses ≤ engagements ≤ budget, chambres occupées ≤ capacité et clics ≤ impressions.

## Extension facultative : configurer d'autres QVD

Cette section prépare une évolution future. Elle n'est ni une étape du rendu ni un prérequis de validation pédagogique.

`config/sources.synthetic.json` est le seul mapping physique : identifiants, fichiers relatifs à une racine autorisée, domaine, champs logiques → colonnes réelles, unités, grain et relations. Les fonctions métier utilisent les identifiants logiques, par exemple `overnight_stays`, et non un chemin personnel.

`config/dimension-aliases.json` centralise les synonymes de destinations et marchés dans les langues testées. Ce fichier sert à ancrer les filtres, pas à définir des droits. Ajouter les nouveaux libellés/synonymes réels dans cette configuration et redémarrer ; l'accès reste contrôlé par le compte serveur.

Si un autre corpus est choisi ultérieurement :

1. Créer une copie de cette configuration, sous `local_data/`, avec `synthetic: false` uniquement si les données sont effectivement réelles.
2. Définir `ONMT_QVD_ROOT` et `ONMT_SOURCES_CONFIG` avant le démarrage.
3. Adapter les noms de fichiers, domaines, colonnes et unités. La racine borne les chemins ; aucun chemin de fichier n'est accepté depuis le chat.
4. Vérifier son grain mensuel destination/marché et ses définitions. Un fichier à grain journalier, hôtelier ou campagne nécessite une adaptation explicite du connecteur et des agrégations ; changer son nom ne suffit pas.
5. Consulter le catalogue, les types découverts, champs absents et erreurs. Valider unicité des clés et concordance des relations. Les unités du noyau doivent être canoniques (`MAD`, `nuitees`, etc.) ; une conversion implicite n'est pas réalisée.
6. Définir et vérifier des attendus indépendants propres à ce nouveau corpus avant de l'utiliser.

La lecture prend en charge les dates ISO, les dates Python et les numéros de date Qlik depuis le 30 décembre 1899. PyQvd décode les valeurs duales ; la valeur de calcul peut différer du texte affiché dans Qlik. Les types et formats Qlik particuliers restent à vérifier sur les vrais fichiers, notamment les QVD chiffrés ou non pris en charge par le lecteur.

La version exposée d'une source combine son contenu et sa configuration métier. Un changement de QVD ou de mapping invalide les analyses antérieures. La configuration est chargée au démarrage : redémarrer après sa modification. Les fichiers QVD sont revérifiés à chaque opération ; leur remplacement pendant une lecture provoque une erreur plutôt qu'un résultat mélangé. Cette lecture complète est adaptée au petit corpus local ; ce n'est pas une synchronisation incrémentale de production.
