# ONMT AI — Intelligent Tourism Analytics Assistant

Projet académique en cours de développement.

L’objectif est de créer une application conversationnelle permettant
d’interroger des données touristiques, de produire des analyses fiables
et de générer des rapports sourcés pour aider à la décision.

## 1. Fonctionnalités prévues

- Lecture native des fichiers QVD de Qlik Sense.
- Compréhension des questions en langage naturel.
- Gestion du contexte des conversations.
- Calcul des indicateurs touristiques et comparaisons.
- Prévisions et détection d’anomalies.
- Recherche documentaire avec RAG.
- Génération et modification de rapports sourcés.
- Export PDF.
- Contrôle des accès aux données et aux rapports.

Ces fonctionnalités constituent la cible du projet.
Leur présence dans ce README ne signifie pas qu’elles sont déjà réalisées.

## 2. Répartition de l’équipe

| Membre | Responsabilités                                                      |
| ------ | -------------------------------------------------------------------- |
| Hayat  | Accès QVD, compréhension des questions, conversation et coordination |
| Doha   | Qualité des données, indicateurs, analyses, prévisions et anomalies  |
| Salma  | Préparation documentaire, RAG, génération de rapports et export PDF  |

Chaque membre développe également les routes backend, les écrans
et les tests associés à son module.

## 3. Technologies proposées

### Backend commun

- Python
- FastAPI
- Pydantic
- PostgreSQL et SQLAlchemy

### Conversation et orchestration

- Ollama
- LangGraph

### Données et analyses

- PyQvd
- pandas et NumPy
- scikit-learn
- statsmodels

### Recherche documentaire et rapports

- pdfplumber
- Sentence Transformers
- ChromaDB
- Jinja2
- Playwright

### Frontend

- React
- TypeScript

### Tests

- pytest
- pytest-asyncio

Les dépendances Python sont déclarées dans backend/requirements.txt.
Les versions exactes seront figées après validation de l’environnement.

## 4. Organisation du dépôt

- backend/app/main.py : point d’entrée de l’application FastAPI.
- backend/app/core/ : configuration, sécurité et composants communs.
- backend/app/schemas/ : contrats Pydantic partagés.
- backend/app/data_access/ : lecteur QVD et catalogue des sources.
- backend/app/conversation/ : module de Hayat.
- backend/app/analytics/ : module de Doha.
- backend/app/reports/ : module de Salma.
- backend/tests/ : tests unitaires, d’intégration et de contrats.
- frontend/src/ : interface utilisateur.
- docs/ : architecture et contrats d’échange.
- examples/contracts/ : exemples JSON synthétiques.
- local_data/ : données locales exclues de Git.

## 5. Pipeline général

1. L’utilisateur pose une question.
2. Le backend vérifie son identité et ses permissions.
3. Hayat transforme la question en demande structurée.
4. Doha récupère les données autorisées et réalise les calculs.
5. Hayat affiche les résultats et leurs sources.
6. Si un rapport est demandé, Salma récupère les analyses autorisées.
7. Salma recherche les documents pertinents, rédige et vérifie le rapport.
8. Le rapport est proposé à la consultation et à l’export PDF.

## 6. Contrats d’échange

Le document docs/contracts.md définit les échanges communs :

- AnalysisRequest
- AnalysisResult
- SourceReference
- ReportRequest
- ReportResult
- ReportRevisionRequest
- ErrorResponse
- AccessContext

Toute modification incompatible doit être discutée avec les membres
concernées et accompagnée d’une mise à jour des exemples et des tests.

## 7. Organisation Git

- main : base commune et fonctionnalités intégrées.
- setup/project-foundation : préparation initiale du projet.
- hayat/conversation : travail de Hayat.
- doha/analytics : travail de Doha.
- salma/reporting-rag : travail de Salma.

Les branches individuelles sont créées après la fusion de la base commune.

Chaque membre travaille sur sa branche et propose ses changements
par une Pull Request vers main.

## 8. Données et confidentialité

Ne pas ajouter au dépôt :

- Les fichiers QVD réels ou confidentiels.
- Les documents internes non autorisés.
- Les rapports sensibles.
- Les clés API et mots de passe.
- Les fichiers .env.
- Les modèles téléchargés et les index locaux.

Utiliser des données synthétiques pour les exemples partagés.

Les résultats fictifs doivent être explicitement identifiés.
Une donnée absente ne doit jamais être remplacée par une invention.

## 9. Développement parallèle

Les modules peuvent être développés indépendamment en respectant
les contrats communs.

Lorsque les autres modules ne sont pas encore disponibles,
utiliser des adaptateurs de test et des résultats synthétiques.

L’intégration réelle devra être testée une fois les modules connectés.

## 10. État actuel et lancement

Le dépôt contient actuellement la structure initiale,
les contrats proposés et la liste des dépendances.

Les fichiers de code vides sont des emplacements à implémenter.
Le module de Salma est désormais exécutable localement : API, interface React,
documents, index Chroma, rapports versionnés et PDF. Les modules de Hayat et Doha
restent à connecter. Le mode démo utilise des analyses synthétiques explicites.

Voir [docs/salma-reporting.md](docs/salma-reporting.md) pour les commandes PowerShell,
les résultats des tests, les points d’intégration et les limites des modèles locaux.

La mise à jour des modèles locaux, de l’OCR et des révisions est décrite dans
[docs/salma-local-ai.md](docs/salma-local-ai.md). Elle conserve les analyses synthétiques
tant que le fournisseur réel de Doha n’est pas connecté.

## 11. Périmètre actuel

Développement de l’application uniquement.

Les choix de déploiement seront définis séparément selon
les consignes du professeur.
