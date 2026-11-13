# Les QVD et leur dictionnaire

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

Ces définitions sont celles du développement. Elles ne prétendent pas reconstituer les modèles métiers réels de l'ONMT. Le classement des champs dans les trois domaines est configurable ; le CPS et les fichiers réels devront déterminer le mapping définitif.

La saisonnalité est une fonction sinusoïdale, avec une croissance historique modérée. Les dépenses utilisent un générateur pseudo-aléatoire fixe. Les nuitées d'Agadir en février sont imposées à 100 000 en 2024 et 80 000 en 2025. Marrakech : 150 000 puis 165 000. La part France d'Agadir en février 2025 vaut 25 600. Ces références indépendantes sont écrites dans `expected.json`.

Les relations entre budgets et résultats sont construites artificiellement. Une association dans ce corpus n'est jamais une preuve économique ni un rendement causal d'une campagne.

## Fichiers générés hors Git

- `local_data/qvd-synthetic/*.qvd` : corpus normal.
- `manifest.json` : graine, périodes, dimensions, nombres de lignes et empreintes des fichiers.
- `expected.json` : réponses de référence.
- `invalid/commercial-invalid.qvd` : doublon de clé/grain, valeur manquante, date invalide et nombre négatif. Ce fichier n'est pas chargé par la configuration normale.

La graine reproduit les **données**. Le conteneur QVD peut inclure des métadonnées de création ; il n'est pas promis que chaque fichier régénéré ait la même empreinte binaire.

## Configuration et remplacement par les vraies sources

`config/sources.synthetic.json` est le seul mapping physique : identifiants, fichiers relatifs à une racine autorisée, domaine, champs logiques → colonnes réelles, unités, grain et relations. Les fonctions métier utilisent les identifiants logiques, par exemple `overnight_stays`, et non un chemin personnel.

`config/dimension-aliases.json` centralise les synonymes de destinations et marchés dans les langues testées. Ce fichier sert à ancrer les filtres, pas à définir des droits. Ajouter les nouveaux libellés/synonymes réels dans cette configuration et redémarrer ; l'accès reste contrôlé par le compte serveur.

Pour utiliser les sources réelles :

1. Créer une copie de cette configuration, sous `local_data/`, avec `synthetic: false` uniquement si les données sont effectivement réelles.
2. Définir `ONMT_QVD_ROOT` et `ONMT_SOURCES_CONFIG` avant le démarrage.
3. Adapter les noms de fichiers, domaines, colonnes et unités. La racine borne les chemins ; aucun chemin de fichier n'est accepté depuis le chat.
4. Faire valider le grain mensuel destination/marché et les définitions par le responsable métier. Un fichier à grain journalier, hôtelier ou campagne nécessite une adaptation explicite du connecteur et des agrégations ; changer son nom ne suffit pas.
5. Consulter le catalogue, les types découverts, champs absents et erreurs. Valider unicité des clés et concordance des relations. Les unités du noyau doivent être canoniques (`MAD`, `nuitees`, etc.) ; une conversion implicite n'est pas réalisée.
6. Vérifier quelques résultats de référence indépendants sur le vrai patrimoine avant d'activer la génération.

La lecture prend en charge les dates ISO, les dates Python et les numéros de date Qlik depuis le 30 décembre 1899. PyQvd décode les valeurs duales ; la valeur de calcul peut différer du texte affiché dans Qlik. Les types et formats Qlik particuliers restent à vérifier sur les vrais fichiers, notamment les QVD chiffrés ou non pris en charge par le lecteur.

La version exposée d'une source combine son contenu et sa configuration métier. Un changement de QVD ou de mapping invalide les analyses antérieures. La configuration est chargée au démarrage : redémarrer après sa modification. Les fichiers QVD sont revérifiés à chaque opération ; leur remplacement pendant une lecture provoque une erreur plutôt qu'un résultat mélangé. Cette lecture complète est adaptée au petit corpus local ; ce n'est pas une synchronisation incrémentale de production.
