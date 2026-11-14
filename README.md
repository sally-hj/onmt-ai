# ONMT AI — Intelligent Tourism Analytics Assistant

Projet académique en cours de développement.

**Décision du professeur, 14 novembre 2026 : les QVD synthétiques sont les données
de référence définitives du projet pédagogique.** Aucun dataset réel n'est attendu
pour finaliser le rendu. Configurer d'autres QVD reste une extension facultative.
Cet accord porte sur les données ; il ne dispense pas des fonctions encore manquantes.

**Application locale intégrée :** [démarrage et démonstration](docs/full-app/08-utilisation.md),
[guide pédagogique](docs/full-app/README.md), [couverture CPS](docs/full-app/01-couverture-cps.md).
Le parcours principal relie désormais des QVD synthétiques natifs, les calculs de Doha,
la conversation de Hayat et les rapports de Salma. Les données sont fictives ; les limites
et preuves d'exécution figurent dans le [bilan des tests](docs/full-app/09-resultats.md).
La [matrice actualisée](docs/full-app/01-couverture-cps.md) distingue acquis pédagogiques,
fonctions à terminer et exigences industrielles. Le [reste à développer](docs/full-app/10-perimetre-pedagogique.md)
conserve les écarts fonctionnels, indépendamment du choix des données.

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
- SQLite pour l'état applicatif local, sans recopier les tables QVD

### Conversation et orchestration

- Ollama
- LangGraph

### Données et analyses

- PyQvd
- Agrégations et prévisions de référence en Python
- NumPy et bibliothèques de modèles pour les composants qui les utilisent

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

Les dépendances intégrées sont fixées dans `backend/requirements-full.txt` ;
`backend/requirements-full-tested.lock.txt` décrit l'environnement validé.
`backend/requirements.txt` conserve la proposition initiale : certains outils listés
(PostgreSQL, pandas, statsmodels) ne sont pas utilisés par l'application actuelle.

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
- feature/full-onmt-app : intégration locale des trois modules.

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

Utiliser les données synthétiques comme référence définitive du projet pédagogique.
Le [dictionnaire](docs/full-app/03-donnees.md) décrit la génération et les relations.
L'[oracle manuel](examples/synthetic-reference.json) contient les résultats attendus
indépendants du moteur de calcul.

Les résultats fictifs doivent être explicitement identifiés.
Une donnée absente ne doit jamais être remplacée par une invention.

## 9. Développement parallèle

Les modules peuvent être développés indépendamment en respectant
les contrats communs.

Lorsque les autres modules ne sont pas encore disponibles,
utiliser des adaptateurs de test et des résultats synthétiques.

Les trois modules sont intégrés sur les QVD synthétiques natifs. Les preuves d'exécution
des calculs et modèles locaux sont distinguées des tests à clients simulés.

## 10. État actuel et lancement

L'application complète se lance avec `scripts/start-full-app.ps1`, Ollama dans un
autre terminal et `npm run dev` dans `frontend`. Elle propose une connexion locale,
un chat principal, des calculs QVD, des graphiques, des documents et des rapports PDF.
Les comptes et les commandes exactes sont dans le guide de démarrage ci-dessus.

Les commandes Salma ci-dessous décrivent le sous-module historique et son mode
de démonstration à fixtures isolées. Elles ne remplacent pas le démarrage intégré.

Voir [docs/salma-reporting.md](docs/salma-reporting.md) pour les commandes PowerShell,
les résultats des tests, les points d’intégration et les limites des modèles locaux.

La mise à jour des modèles locaux, de l’OCR et des révisions est décrite dans
[docs/salma-local-ai.md](docs/salma-local-ai.md). Ce guide historique précède l'intégration :
le fournisseur de Doha calcule maintenant depuis les QVD synthétiques de référence,
qui ne doivent pas être remplacés avant le rendu.

## 11. Périmètre actuel

Développement de l’application uniquement.

Le volet données est conforme au choix pédagogique confirmé. La couverture fonctionnelle
reste partielle : les KPI supplémentaires, fonctions analytiques avancées, longues
conversations et rapports élaborés restent à développer ou explicitement arbitrer.

Les choix de déploiement seront définis séparément selon
les consignes du professeur.
