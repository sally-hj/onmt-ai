# Configurations, scripts et tests

## Configuration et dépendances

| Fichier | Contenu, utilisation et exemple |
| --- | --- |
| `config/sources.synthetic.json` | Mapping central des trois QVD : fichiers relatifs, domaines, noms physiques/logiques, unités, grain et relations. `Catalog` le lit au démarrage. Exemple : `overnight_stays` correspond à `nights`. |
| `examples/synthetic-reference.json` | Oracle manuel versionné : ancrages du corpus et six lignes indépendantes avec valeurs/unités attendues pour les seize KPI. Il n'est pas réécrit par le générateur ou le moteur analytique. |
| `config/dimension-aliases.json` | Synonymes linguistiques de destinations/marchés. `slots.py` les utilise pour vérifier que les filtres sont demandés, sans accorder d'autorisation. |
| `backend/requirements-full.txt` | Dépendances directes de l'intégration : inclut les modèles/rapports puis fixe PyQvd et LangGraph. Utilisé par pip, pas importé par Python. |
| `backend/requirements-full-tested.lock.txt` | Relevé des versions installées pendant la validation complète ; ne nécessite pas une explication ligne par ligne. N'inclut pas les poids de modèles ni Tesseract. |
| `backend/requirements-reporting-models.txt` | Dépendances Salma avec Sentence Transformers, torch, client Ollama et runtime Windows ; conservées. |
| `backend/requirements-reporting.txt` | Dépendances légères Salma/API/test/PDF, avec PDFium pour le rendu OCR ; conservées. |
| `backend/requirements-reporting-tested.lock.txt` | Ancien relevé de validation Salma ; il n'est pas présenté comme le relevé des nouveaux paquets QVD/LangGraph. |
| `backend/requirements.txt` | Proposition initiale commune, non verrouillée. Certaines bibliothèques listées ne sont pas nécessaires à l'implémentation locale, notamment PostgreSQL et pandas. |
| `examples/reporting.env.example` | Variables historiques de modèles/OCR/chemins sans secret ; documentation, pas chargement automatique. Les nouvelles variables d'intégration sont décrites dans le guide d'utilisation. |
| `examples/full-app.env.example` | Variables du mode intégré, des QVD et du stockage local. Ne contient aucun secret et n'est pas chargé automatiquement ; le script de démarrage prépare l'environnement. |
| `examples/contracts/*.json` | Objets synthétiques démontrant les contrats communs. Les tests Salma les utilisent ; l'application complète calcule ses analyses depuis les QVD. |
| `frontend/package.json` | Dépendances React/TypeScript/Vite et scripts `dev`, `test`, `build`. Aucun paquet d'animation n'a été ajouté. |
| `frontend/package-lock.json` | Résolution exacte des dépendances npm existantes ; ne contient pas le code applicatif. |
| `frontend/index.html` | Élément racine du navigateur et chargement de `src/app/main.tsx`. |
| `frontend/tsconfig.json` | Vérification stricte TypeScript et JSX ; exécutée pendant le build. |
| `frontend/vite.config.ts` | React, tests jsdom et proxy `/api` vers le backend local. `ONMT_API_TARGET` permet un autre port pour les tests. |
| `frontend/src/test-setup.ts` | Configure les assertions DOM des tests React. |
| `pytest.ini` | Répertoire des tests, chemin d'import backend et catégories opt-in : browser, models, local_ai, full_models. |
| `.gitignore` | Exclut données locales, index, modèles, environnements et résultats de compilation. Vérifier avant un commit de données. |
| `AGENTS.md` / `docs/architecture.md` | Emplacements initiaux vides au diagnostic. L'architecture réelle est documentée dans le présent dossier. |
| `README.md` / `docs/contracts.md` | Index de démarrage et contrats de référence. Les ajouts d'API intégrée sont documentés sans supprimer les champs des échanges Salma. |

## Scripts

| Fichier | Fonctions / entrées / résultat |
| --- | --- |
| `scripts/start-full-app.ps1` | Paramètre `Port=8000`. Définit le mode intégré, stockage distinct, vrais modèles/OCR et absence de tracing externe, puis lance Uvicorn sur localhost. Utilisé par le terminal de développement. |
| `scripts/start-local-ollama.ps1` | Démarre le service local au premier plan avec cloud désactivé et un modèle/inférence à la fois ; ne crée pas de second service si le port répond. |
| `scripts/start-reporting.ps1` | Ancien lancement du seul module Salma. Options Templates/DemoEmbeddings/DisableOCR ; ne constitue pas le lancement de l'application complète. |
| `scripts/prepare-local-ai.py` | `download()` vérifie une empreinte ; `prepare_ollama/prepare_ocr/prepare_embeddings/prepare_language_model()` préparent des composants officiels locaux ; `--components` sélectionne les téléchargements. Préparation explicite, sans envoi de documents. |
| `scripts/build-code-guide.py` | `module_name(path)` construit un nom de module ; `inventory()` lit AST/imports/signatures et écrit les quatre inventaires backend. Les dictionnaires ROLES/HELP contiennent les explications pédagogiques. Ne modifie pas le code métier. |
| `scripts/evaluate-local-languages.py` | `evaluate(languages)` appelle réellement Ollama sur une question de référence par langue, compare tous les paramètres attendus et écrit réussites/échecs/durées dans `local_data/full-app-results/languages.json`. C'est une petite évaluation, pas une certification linguistique. |

La génération QVD s'exécute comme module Python `app.data_access.synthetic` ; ses fonctions sont décrites dans l'inventaire des données. Les démos Salma sont décrites dans l'inventaire rapports.

## Tests backend

Tous sont appelés par pytest. Leurs arguments sont des fixtures, c'est-à-dire des objets préparés pour le test. Une assertion vérifie une propriété ; sa présence n'est pas une preuve d'exécution. Les résultats datés sont dans le bilan séparé.

| Fichier | Contenu et scénario concret |
| --- | --- |
| `backend/tests/conftest.py` | `text_pdf(texts)` fabrique un PDF textuel synthétique ; fixtures `access`, `request_body`, `application`, `client` préparent l'API Salma isolée, sans vrais modèles. |
| `backend/tests/test_full_app.py` | Fixtures QVD synthétiques natifs et état temporaire. `comparison(destination,**updates)` construit une demande. `ScriptedParser.parse()` est un interpréteur simulé explicitement réservé aux tests. Vérifie réponses de référence indépendantes, accès, ratios, grains, dates, données défectueuses, absence, sources périmées, prévisions, session, relance, versions, recalcul, alertes et contexte rattaché. |
| `backend/tests/test_synthetic_reference.py` | Génère et relit réellement les QVD. `test_native_corpus_and_cross_domain_invariants` contrôle les trois domaines ; `test_reproducible_decoded_data_and_seed_effect` compare deux générations et une autre graine ; seize cas paramétrés contrôlent `AnalyticsService` sur l'oracle manuel ; `test_cross_domain_missing_key_blocks_ratio` refuse une relation incomplète. Aucun appel à l'IA n'est revendiqué dans ce fichier. |
| `backend/tests/test_full_models.py` | Un scénario opt-in avec vrais QVD, OCR, E5, Ollama et LangGraph. Importe un PDF mixte fictif, compare Agadir/Marrakech dans le chat, crée un rapport, traduit sa synthèse et exporte les PDF. Le wrapper de capture ne journalise que les réponses sur données fictives du test. |
| `backend/tests/test_full_offline.py` | API réellement démarrée, service Ollama volontairement arrêté : vérifie l'erreur 503 et l'absence de nouveau rapport de secours. Opt-in séparé pour éviter d'arrêter un service pendant les autres essais. |
| `backend/tests/test_full_browser.py` | API et Vite déjà démarrés ; vrai Chromium. Prépare un vrai calcul QVD par API, puis vérifie connexion, suggestions, résultat graphique, sources, alertes, mobile et clavier. Aucun appel LLM n'est revendiqué pour ce test d'écran. |
| `backend/tests/test_contracts.py` | Vérifie exemples JSON, champs stricts, périodes et règles de contrats. Protège la compatibilité des modules. |
| `backend/tests/test_documents.py` | Import texte, versions/doublons, citations, droits, recherche, réindexation et originaux. Utilise l'encodeur lexical de test quand les modèles ne sont pas activés. |
| `backend/tests/test_reporting.py` | Création, lecture, versions, dépendances, contrôle des sources, erreurs, droits et PDF des rapports Salma. |
| `backend/tests/test_narrative.py` | Faux client IA contrôlé : vérifie conservation des faits, sorties interdites, révisions, erreurs, absence de repli et échappement du protocole local. Ces tests ne prouvent pas la qualité du vrai modèle. |
| `backend/tests/test_llm.py` | Comportement du client historique et essai opt-in d'embeddings réels ; distingue réseau simulé et modèle local. |
| `backend/tests/test_local_models.py` | OCR FR/EN/AR et PDF mixte, paraphrases sémantiques E5, droits et chaîne Salma avec vrai modèle. Ces objets d'analyse restent les anciennes fixtures ; le nouveau test complet vérifie les calculs QVD. |
| `backend/tests/local_fixtures.py` | `scanned_pdf(pages)` rend le texte avec Chromium puis l'enregistre comme images dans un PDF ; permet de tester une vraie reconnaissance, y compris arabe. |
| `backend/tests/test_browser.py` | Ancienne régression navigateur Salma sous `?legacy=1`, avec gabarits et sources simulées explicitement. Le fixture `live_servers()` démarre et arrête ses propres processus. |

Pour lire une fonction de test, repérer d'abord ses préparations, puis l'appel métier et enfin la valeur attendue. Dans le test QVD, −20 % vient des constantes indépendantes 80 000 et 100 000, pas d'un deuxième appel à la fonction de variation.

## Tests React

| Fichier | Ce qu'il contrôle |
| --- | --- |
| `frontend/src/features/workspace/Workspace.test.tsx` | API simulée : conservation de saisie après erreur Ollama, identifiant/version d'une relance, restauration refusée et graphique issu d'un résultat fourni. Les entrées sont des objets synthétiques, pas une vraie IA. |
| `frontend/src/features/reports/ReportsPage.test.tsx` | Régression de l'ancien écran, requêtes et traduction ciblée avec API simulée. |

## Documentation et artefacts

Les anciens fichiers `docs/salma-*.md` restent l'historique et la documentation du sous-module. Le présent dossier explique l'intégration ; `01-couverture-cps.md` lie exigences, travaux et contrôles ; `09-resultats.md` indique ce qui a été réellement testé. Les quatre inventaires Python sont générés à partir du dépôt, les guides d'usage et interprétations CPS sont rédigés.

Sous `local_data/` restent les QVD, manifeste, références, SQLite, PDF, captures, réponses synthétiques de test, outils et poids. Aucun de ces gros fichiers ou états privés n'est inclus dans les commits. Les caches `__pycache__`, `.pytest_cache`, `node_modules`, `.venv` et les bibliothèques externes ne font pas partie du code à expliquer.
