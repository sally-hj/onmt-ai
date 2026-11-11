# Résultats de vérification du module Salma

> Bilan historique du 4 novembre. Les nouveaux essais de vrais modèles et OCR sont consignés dans [salma-local-ai-results.md](salma-local-ai-results.md).

Exécution du 4 novembre 2026, Windows, branche `salma/reporting-rag`.

| Vérification | Résultat constaté |
| --- | --- |
| Backend complet avec `ONMT_TEST_BROWSER=1`, `python -m pytest -q` | **58 tests réussis, 1 ignoré**, 26,37 s à la dernière exécution. |
| React, `npm test` | **3 tests réussis** avec Vitest 5.1.0 et API simulée. |
| TypeScript et bundle, `npm run build` | Réussite avec Vite 6.4.5. |
| Dépendances npm, `npm audit` | **0 vulnérabilité signalée** au moment du contrôle. |
| Résolution Python, `python -m pip check` | `No broken requirements found.` |
| Whitespace, `git diff --check` | Aucune erreur. |
| Import réel Sentence Transformers / PyTorch | **Échec**, `WinError 126` sur `torch/lib/shm.dll` ou une dépendance, confirmé hors bac à sable. |
| Inférence réelle d’un modèle Sentence Transformers | **Non validée** ; test `models` ignoré faute de prérequis et de modèle local. |
| Inférence réelle Ollama | **Non exécutée** ; commande `ollama` non détectée. Transport HTTP simulé dans les tests du client. |
| Modules réels de Hayat et Doha | **Non connectés, intégration non validée**. |

## Ce que les tests couvrent

Les neuf exemples JSON ajoutés sont validés contre leurs schémas Pydantic. Les tests rejettent les dates inversées, paramètres de comparaison/prévision incomplets, pages invalides, citations inconnues, analyses manquantes et contexte d’autorisation déclaré dans une demande de rapport.

Les rapports sont testés dans cinq langues et pour trois audiences. Les valeurs, unités, filtres et périodes sont conservés ; `%` est réservé à la variation. Un entier supérieur à la précision exacte d’un `number` JavaScript reste un entier côté Python et du texte exact dans le rapport. `null` ne devient pas zéro. Une analyse sans source ne produit pas de chiffre présenté comme observation. Une référence ambiguë vers plusieurs versions est refusée. Une erreur réelle du fournisseur ne déclenche aucun résultat synthétique de secours.

Les essais documentaires utilisent de vrais PDF textuels synthétiques, pdfplumber et un vrai index ChromaDB persistant, avec **embeddings lexicaux simulés explicitement**. Ils couvrent pages, doublons, remplacement d’une édition, suppression des anciens vecteurs, réindexation, conservation de l’original, PDF sans texte, PDF mixte, fichier endommagé, taille excessive, absence de preuves et seuil de recherche. Ces essais ne mesurent pas la qualité d’un modèle sémantique multilingue.

Les contrôles d’accès couvrent les listes vides, modules et territoires, propriété des rapports, documents interdits, lecture, modification, export et téléchargement. Les documents interdits sont exclus avant la recherche et avant l’appel du planificateur. Les droits documentaires sont réévalués lors de la lecture d’un rapport existant. Hors démo, les en-têtes navigateur ne remplacent pas l’authentification serveur.

Le test du client Ollama vérifie la séparation message système / données documentaires, la validation des citations et le refus d’un modèle distant avant l’envoi du contexte. Il utilise `httpx.MockTransport` : il ne prouve ni exécution du service, ni résistance générale d’un LLM aux injections.

Le versionnement est vérifié sur cinq modifications successives, la conservation de l’historique après redémarrage, les sections indépendantes et les dépendances. Deux modifications concurrentes produisent une réussite et un `version_conflict` ; aucune version n’écrase l’autre.

Les PDF sont générés avec **Chromium réel**, puis relus par **pdfplumber réel**, en français et arabe. Les tests vérifient contenu, nombres, unités, références, texte arabe extractible, absence de page vide, tableau long de 100 points, échappement HTML et séparation des exports par version. Les aperçus PDF ont également été examinés visuellement ; cela ne remplace pas une recette complète de toutes les langues et mises en page.

Le parcours Playwright lance **de vrais serveurs temporaires FastAPI et Vite**, ouvre l’interface et réalise création → révision → préparation et téléchargement PDF → import PDF → recherche d’un passage → consultation d’une ancienne version → refus de révision obsolète. Les analyses restent synthétiques et aucun vrai modèle IA n’est utilisé. Les processus sont arrêtés après le test.

## Artefacts locaux reproductibles

Les fichiers ci-dessous sont sous `local_data/`, donc exclus de Git :

- `demo-reporting/rapport-synthetique.pdf` et `.json` : version 6 issue du script `python -m app.reports.demo`.
- `test-artifacts/rapport-demo.pdf` : PDF téléchargé par le navigateur lors du test de bout en bout.
- `test-artifacts/rapport-interface.png` : capture du parcours, incluant le refus attendu de version obsolète.
- `test-artifacts/rapport-arabe.pdf` et aperçus PNG : inspection locale du rendu arabe.

Les commandes exactes de reproduction et de lancement figurent dans [salma-reporting.md](salma-reporting.md). Les modèles, index, secrets, originaux et rapports locaux restent hors Git.

Les tests réussis démontrent ce périmètre de prototype et ces cas synthétiques. Ils ne valident pas les calculs QVD réels, la prose économique libre, la qualité linguistique complète, les performances CPS, l’authentification réelle, le chiffrement ou la conformité du déploiement.
