# Fichiers de la livraison et pipeline expliqué

Inventaire produit depuis la différence avec la version intégrée `51fe630`. Les signatures ci-dessous servent de repères de lecture ; les tests distinguent fonctions simulées et modèles réels.

## Exemple complet

1. Une question sur Agadir/février 2025 entre dans une tâche persistante. Qwen produit une intention, les dates/filtres sont ancrés, les droits sont appliqués.
2. Le spécialiste marchés calcule 80 000 contre 100 000 nuitées (−20 %) depuis Commercial. Une note croisant les domaines appelle aussi Finance et Performance ; un pic saisonnier peut déclencher le contrôle budgétaire.
3. Les diagnostics facultatifs BCG/Valeur–Volume/carte/scénario sont calculés, identifiés et conservés. Un scénario de −10 % sur 80 000 produit 72 000, explicitement hypothétique.
4. La recherche consulte les PDF déjà indexés et autorisés ; elle transmet les passages utiles avec pages/versions. E5 calcule les embeddings, Chroma recherche ; aucune réimportation systématique ni entraînement.
5. Qwen rédige. Le serveur ajoute les chiffres/citations exacts et vérifie la sortie. Une erreur produit un refus explicite, pas un rapport simulé.
6. Le rapport garde ses versions, diagnostics et propositions. Chromium produit la note ou le rapport, puis les vingt-cinq diapositives. Les manques restent visibles ; les données synthétiques sont marquées.
7. Une révision change une section et ses dépendances. Un ajout de KPI conserve les analyses antérieures lorsqu’il est demandé comme ajout. Une source ou permission modifiée est réévaluée à la consultation.

Installation = logiciels/poids ; génération des données = corpus fictif ; calcul = outils numériques ; indexation = vecteurs persistants ; inférence = modèles déjà entraînés ; évaluation = comparaison à des attendus. Aucun entraînement/fine-tuning n’est effectué.

## Inventaire

### [README.md](../../README.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [backend/app/analytics/anomalies.py](../../backend/app/analytics/anomalies.py)

Détecte les baisses annuelles et dédoublonne les alertes.
Entrées : données Commercial autorisées. Sorties : alertes et trace de vérification. Interactions : surveillance périodique et bouton actualiser.

Repères : `AlertService.__init__`, `AlertService.refresh`, `AlertService.list`.

### [backend/app/analytics/custom.py](../../backend/app/analytics/custom.py)

Contrôle la proposition et la confirmation des KPI personnalisés.
Entrées : deux termes structurés, opération, droits. Sorties : brouillon avec exemple ou définition active versionnée. Interactions : SQLite et AnalyticsService ; aucun code arbitraire.

Repères : `term_sum`, `CustomKpis.__init__`, `CustomKpis.validate`, `CustomKpis.metric`, `CustomKpis.list`, `CustomKpis.propose`, `CustomKpis.confirm`, `CustomKpis.attach_example`.

### [backend/app/analytics/diagnostics.py](../../backend/app/analytics/diagnostics.py)

Calcule BCG, Valeur–Volume, Butler, cartes et scénarios.
Entrées : périodes, filtres, seuils et droits. Sorties : résultat structuré avec hypothèses, unités et sources. Interactions : catalogues QVD internes et comparateurs.

Repères : `butler`, `bcg_point`, `Diagnostics.__init__`, `Diagnostics.international`, `Diagnostics.value_volume`, `Diagnostics.destination`, `Diagnostics.map`, `Diagnostics.scenario`.

### [backend/app/analytics/forecasting.py](../../backend/app/analytics/forecasting.py)

Compare deux références de projection sur un bloc chronologique.
Entrées : historique mensuel et horizon. Sorties : points projetés, erreurs et limites. Interactions : AnalyticsService ; horizon long signalé comme mécanique.

Repères : `next_month`, `forecast`.

### [backend/app/analytics/metrics.py](../../backend/app/analytics/metrics.py)

Définit les 46 indicateurs et leurs réducteurs autorisés.
Entrées : lignes QVD et définition. Sorties : valeur calculée, unité et formule. Interactions : AnalyticsService et catalogue API.

Repères : `Metric.describe`, `Metric.source_formula`, `metric_catalog`, `calculate`, `evaluate`.

### [backend/app/analytics/products.py](../../backend/app/analytics/products.py)

Conserve les diagnostics privés et refuse leur réemploi si sources/droits changent.
Entrées : diagnostic et propriétaire. Sorties : identifiant persistant ou refus. Interactions : SQLite, analyses, rapports et exports.

Repères : `Products.__init__`, `Products.save`, `Products.get`.

### [backend/app/analytics/quality.py](../../backend/app/analytics/quality.py)

Bloque les données invalides et les scores hors échelle.
Entrées : lignes et conventions de source. Sorties : liste d’erreurs. Interactions : Catalog avant calcul.

Repères : `inspect_rows`.

### [backend/app/analytics/router.py](../../backend/app/analytics/router.py)

Expose sources, KPI, analyses, diagnostics, alertes et état des services.
Entrées : requêtes HTTP validées et session. Sorties : JSON calculé ou erreur. Interactions : services analytiques et audit.

Repères : `propose`, `confirm`, `diagnostic`, `read_diagnostic`, `status`, `audit_verify`, `sources`, `metrics`, `analyse`, `analyses`, `read`, `alerts`, `refresh`.

### [backend/app/analytics/service.py](../../backend/app/analytics/service.py)

Lit les sources autorisées, agrège et conserve des analyses réutilisables.
Entrées : AnalysisRequest et droits. Sorties : AnalysisResult. Interactions : catalogue, métriques, projections et rapports.

Repères : `AnalyticsService.__init__`, `AnalyticsService.metrics`, `AnalyticsService.benchmark`, `AnalyticsService._metric`, `AnalyticsService._read`, `AnalyticsService._aggregate`, `AnalyticsService.run`, `AnalyticsService.authorize_snapshot`, `AnalyticsService.get_analysis`.

### [backend/app/conversation/agents.py](../../backend/app/conversation/agents.py)

Implémente les décisions et transmissions des spécialistes.
Entrées : demande, droits, résultats précédents. Sorties : analyses, décision de contrôle budgétaire, preuves et traces. Interactions : outils autorisés QVD/RAG/rapports ; pas de raisonnement interne publié.

Repères : `Specialists.__init__`, `Specialists.record`, `Specialists.request`, `Specialists.route`, `Specialists.territorial`, `Specialists.markets`, `Specialists.seasonality`, `Specialists.budget`, `Specialists.research`, `Specialists.verify`.

### [backend/app/conversation/context.py](../../backend/app/conversation/context.py)

Fusionne une relance avec la dernière demande, y compris suppression de filtres.
Entrées : Intent et contexte. Sorties : AnalysisRequest ou besoin de précision. Interactions : service de conversation.

Repères : `analysis_request`.

### [backend/app/conversation/graph.py](../../backend/app/conversation/graph.py)

Relie les spécialistes avec des chemins conditionnels bornés.
Entrées : tour structuré. Sorties : réponse contrôlée. Interactions : LangGraph et Specialists.

Repères : `build_graph`.

### [backend/app/conversation/intent.py](../../backend/app/conversation/intent.py)

Demande à Qwen une intention structurée.
Entrées : question, contexte et catalogue autorisé. Sorties : Intent validé puis ancré. Interactions : client Ollama, dates/dimensions et orchestration.

Repères : `IntentParser.__init__`, `IntentParser.parse`.

### [backend/app/conversation/router.py](../../backend/app/conversation/router.py)

Expose conversations et tâches avec propriété contrôlée.
Entrées : messages ou identifiants. Sorties : JSON de contexte, tâche ou réponse. Interactions : ConversationService et Jobs.

Repères : `submit`, `job`, `cancel`, `link`, `send`, `read`.

### [backend/app/conversation/service.py](../../backend/app/conversation/service.py)

Exécute le tour, conserve le contexte et réévalue les droits en relecture.
Entrées : message et session serveur. Sorties : réponse et nouvelle version de conversation. Interactions : calculs, KPI, diagnostics, rapports et présentation.

Repères : `ConversationService.__init__`, `ConversationService._title`, `ConversationService._interpret`, `ConversationService._execute`, `ConversationService.send`, `ConversationService.authorize_response`, `ConversationService.link_context`.

### [backend/app/conversation/slots.py](../../backend/app/conversation/slots.py)

Ancre dates, dimensions et relances explicites.
Entrées : intention, texte et contexte. Sorties : paramètres contrôlés. Interactions : interprétation hybride ; ne calcule pas les KPI.

Repères : `normalized`, `explicit_periods`, `ground_intent`.

### [backend/app/core/audit.py](../../backend/app/core/audit.py)

Ajoute et vérifie des événements chaînés.
Entrées : acteur, action, ressource, versions. Sorties : empreinte et verdict d’intégrité. Interactions : audit des requêtes, outils et documents ; ancre externe facultative.

Repères : `AuditLog.__init__`, `AuditLog.digest`, `AuditLog.append`, `AuditLog.verify`.

### [backend/app/core/config.py](../../backend/app/core/config.py)

Lit les chemins et paramètres locaux.
Entrées : variables d’environnement. Sorties : Settings validés. Interactions : API, modèles, QVD, OCR et surveillance.

Repères : `Settings.__post_init__`, `Settings.uses_llm`.

### [backend/app/core/jobs.py](../../backend/app/core/jobs.py)

Gère la file de tâches, l’idempotence et l’annulation entre étapes.
Entrées : propriétaire, clé et traitement. Sorties : état persistant, étapes, résultat ou erreur. Interactions : routes conversation/rapports et worker unique.

Repères : `now`, `Jobs.__init__`, `Jobs._save`, `Jobs.get`, `Jobs.submit`, `Jobs.cancel`, `Jobs._run`, `Jobs.close`.

### [backend/app/core/llm_client.py](../../backend/app/core/llm_client.py)

Appelle le service Ollama local par HTTPX et contrôle ses réponses.
Entrées : schéma JSON, consignes et données. Sorties : texte réellement généré et mesures. Interactions : planification et rédaction ; erreurs explicites, aucun repli simulé.

Repères : `OllamaPlanner.__init__`, `OllamaPlanner.generate_json`, `OllamaPlanner.plan`.

### [backend/app/core/monitor.py](../../backend/app/core/monitor.py)

Vérifie périodiquement les sources lorsque l’API est active.
Entrées : intervalle et comptes autorisés. Sorties : alertes, dernière réussite ou erreur. Interactions : cycle de vie FastAPI et AlertService.

Repères : `Monitor.__init__`, `Monitor.status`, `Monitor.check`, `Monitor._run`, `Monitor.start`, `Monitor.stop`.

### [backend/app/core/security.py](../../backend/app/core/security.py)

Applique les politiques privées et de bibliothèque partagée.
Entrées : ressource et droits serveur. Sorties : autorisation ou refus. Interactions : documents et rapports ; migration conservatrice des imports anciens.

Repères : `require_module`, `can_read`, `authorize`, `private_policy`, `demo_access`.

### [backend/app/core/state.py](../../backend/app/core/state.py)

Conserve l’état applicatif local.
Entrées : analyses, contextes et états. Sorties : enregistrements SQLite. Interactions : authentification, conversation et outils.

Repères : `AppState.__init__`, `AppState.connect`, `AppState.save_analysis`, `AppState.analysis`, `AppState.list_analyses`, `AppState.conversation`, `AppState.save_conversation`.

### [backend/app/core/timing.py](../../backend/app/core/timing.py)

Mesure les étapes réellement exécutées.
Entrées : fonction décorée. Sorties : durée et état. Interactions : traces des tâches et mesures ; aucun pourcentage inventé.

Repères : `measured`.

### [backend/app/data_access/qvd_reader.py](../../backend/app/data_access/qvd_reader.py)

Lit les QVD natifs et réapplique les droits, même dans le cache.
Entrées : source, filtres et droits. Sorties : lignes autorisées et empreinte. Interactions : Catalog ; cache borné et contrôle de modification.

Repères : `source_version`, `normalize_month`, `QvdReader.__init__`, `QvdReader.path`, `QvdReader.read`.

### [backend/app/data_access/supplement.py](../../backend/app/data_access/supplement.py)

Ajoute les QVD complémentaires sans réécrire les trois références.
Entrées : QVD existants et règles déterministes. Sorties : compléments relus et manifestes. Interactions : configuration étendue, comparateurs et tests.

Repères : `regional_rows`, `native_rows`, `ensure_table`, `prepare`.

### [backend/app/main.py](../../backend/app/main.py)

Assemble les services et leur cycle de vie.
Entrées : Settings et composants. Sorties : application FastAPI. Interactions : démarre/arrête surveillance et tâches, protège les routes et journalise les requêtes.

Repères : `create_app`.

### [backend/app/reports/actions.py](../../backend/app/reports/actions.py)

Propose des vérifications opérationnelles liées aux constats.
Entrées : analyses calculées et langue. Sorties : propositions avec condition et référence. Interactions : rapport, interface et exports ; validation humaine requise.

Repères : `proposals`.

### [backend/app/reports/documents.py](../../backend/app/reports/documents.py)

Définit métadonnées, passages et preuves documentaires.
Entrées : données typées d’import. Sorties : documents et références versionnés. Interactions : ingestion, recherche et citations.

Repères : `reference`.

### [backend/app/reports/export.py](../../backend/app/reports/export.py)

Choisit le rendu standard ou la note structurée.
Entrées : instantané autorisé. Sorties : PDF. Interactions : Jinja2 et Chromium sans ressources réseau.

Repères : `PDFExporter.render`.

### [backend/app/reports/generation.py](../../backend/app/reports/generation.py)

Conserve textes contrôlés et gabarits explicites, avec audience internationale.
Entrées : demandes, faits et preuves. Sorties : sections de gabarit et libellés. Interactions : tests/mode explicite et insertion canonique des nombres.

Repères : `number`, `facts`, `render_fact`, `revision_style`, `generate_sections`, `generate_edited_sections`.

### [backend/app/reports/ingestion.py](../../backend/app/reports/ingestion.py)

Importe les PDF et conserve leur état d’indexation.
Entrées : PDF et métadonnées autorisés. Sorties : document, passages et vecteurs. Interactions : pdfplumber, Tesseract, E5, Chroma et SQLite.

Repères : `DocumentService.__init__`, `DocumentService.reindex`, `DocumentService.ingest_pdf`, `DocumentService._ingest`.

### [backend/app/reports/library.py](../../backend/app/reports/library.py)

Prépare et réindexe le corpus partagé de façon explicite et idempotente.
Entrées : corpus versionné et compte autorisé. Sorties : documents indexés ou inchangés. Interactions : registre SQLite ; les imports privés restent privés.

Repères : `prepare_library`.

### [backend/app/reports/narrative.py](../../backend/app/reports/narrative.py)

Fait rédiger la prose puis insère et vérifie les faits et citations.
Entrées : analyses, preuves, langue et audience. Sorties : section et manifeste de génération. Interactions : Qwen ; chiffres libres, incohérences et alphabets inattendus sont contrôlés.

Repères : `validate_arabic_script`, `ledger_for`, `validate_draft`, `render_draft`, `NarrativeWriter.__init__`, `NarrativeWriter.generate_section`, `verify_narrative`.

### [backend/app/reports/presentation.py](../../backend/app/reports/presentation.py)

Construit vingt-cinq diapositives distinctes depuis les résultats disponibles.
Entrées : instantané du rapport et diagnostics. Sorties : PDF de 25 pages. Interactions : Chromium ; manques explicites, abrégés signalés et débordements contrôlés.

Repères : `build_slides`, `PresentationExporter.render`.

### [backend/app/reports/retrieval.py](../../backend/app/reports/retrieval.py)

Recherche après filtrage des droits et du contexte.
Entrées : question, période, indicateurs et droits. Sorties : passages/pages/versions ou absence de preuve. Interactions : E5 produit les vecteurs ; Chroma classe les candidats.

Repères : `Embedder.encode`, `LocalSentenceEmbedder.__init__`, `LocalSentenceEmbedder.encode`, `DemoHashEmbedder.encode`, `ChromaIndex.__init__`, `ChromaIndex.collection`, `ChromaIndex.add`, `ChromaIndex.remove`, `ChromaIndex.query`, `Retriever.__init__`, `Retriever.search_evidence`, `Retriever.search_report`.

### [backend/app/reports/revisions.py](../../backend/app/reports/revisions.py)

Interprète les opérations éditoriales autorisées.
Entrées : instruction de révision. Sorties : opération bornée. Interactions : service de rapports ; audience internationale ajoutée.

Repères : `parse_revision`.

### [backend/app/reports/router.py](../../backend/app/reports/router.py)

Expose rapports, tâches, exports et bibliothèque.
Entrées : requêtes HTTP, PDF et session. Sorties : JSON ou fichier protégé. Interactions : services documentaires et file de tâches.

Repères : `get_access_context`, `report_job`, `config`, `create`, `listing`, `read`, `revise`, `export`, `download`, `deck`, `search`, `reindex`, `documents`, `passage`, `upload`, `original`.

### [backend/app/reports/service.py](../../backend/app/reports/service.py)

Crée, révise, protège et exporte les rapports.
Entrées : demandes et identifiants autorisés. Sorties : rapport versionné, PDF ou deck. Interactions : analyses/diagnostics, RAG, Qwen, validation et stockage.

Repères : `ReportService.__init__`, `ReportService._analyses`, `ReportService.create_report`, `ReportService.recalculate_report`, `ReportService._authorized`, `ReportService.get_report`, `ReportService.list_reports`, `ReportService.revise_report`, `ReportService.export_pdf`, `ReportService.download_pdf`, `ReportService.export_deck`.

### [backend/app/reports/storage.py](../../backend/app/reports/storage.py)

Conserve les versions et fichiers PDF en SQLite.
Entrées : documents, rapports et exports. Sorties : instantanés persistants. Interactions : ajout de colonnes/métadonnées sans suppression des données antérieures.

Repères : `Store.__init__`, `Store.connect`, `Store.documents`, `Store.document`, `Store.save_document`, `Store.document_pdf`, `Store.report`, `Store.report_ids`, `Store.save_report`, `Store.save_pdf`, `Store.pdf`, `Store.audit`.

### [backend/app/reports/strategic.py](../../backend/app/reports/strategic.py)

Met en page une note de quinze parties distinctes.
Entrées : rapport, analyses et diagnostics. Sorties : PDF de 15 pages. Interactions : gabarit A4 ; aucun KPI recalculé dans l’export.

Repères : `note_pages`, `render_strategic`.

### [backend/app/reports/templates/presentation.html](../../backend/app/reports/templates/presentation.html)

Met en page vingt-cinq diapositives de 320 × 180 mm : textes, graphiques, matrices avec repères/légendes et références.
Entrées : instantané autorisé du rapport. Sortie : HTML échappé rendu par Chromium en PDF. CSS fixe, support RTL et marquage synthétique ; aucun accès réseau ni calcul métier dans le gabarit.

### [backend/app/reports/templates/report.html](../../backend/app/reports/templates/report.html)

Met en page les quinze parties A4 de la note structurée : textes, tableaux et graphiques avec unités et provenance.
Entrées : instantané autorisé du rapport. Sortie : HTML échappé rendu par Chromium en PDF. CSS fixe, support RTL et marquage synthétique ; aucun accès réseau ni calcul métier dans le gabarit.

### [backend/app/reports/templates/strategic.html](../../backend/app/reports/templates/strategic.html)

Met en page les quinze parties A4 de la note structurée : textes, tableaux et graphiques avec unités et provenance.
Entrées : instantané autorisé du rapport. Sortie : HTML échappé rendu par Chromium en PDF. CSS fixe, support RTL et marquage synthétique ; aucun accès réseau ni calcul métier dans le gabarit.

### [backend/app/reports/validation.py](../../backend/app/reports/validation.py)

Vérifie les sections, propositions et références.
Entrées : rapport et données de preuve. Sorties : validation ou refus. Interactions : fusionne les champs d’une même source/version, refuse les versions contradictoires.

Repères : `collect_sources`, `verify_report`.

### [backend/app/schemas/report.py](../../backend/app/schemas/report.py)

Étend les contrats de façon compatible.
Entrées : JSON de demande/résultat. Sorties : modèles Pydantic. Interactions : layout, question, diagnostics, audience internationale et propositions restent optionnels.

Repères : `ReportRequest.unique`, `ReportResult.references`.

### `backend/requirements-full.txt` — supprimé

Ancienne liste de dépendances remplacée par le point d’entrée `backend/requirements.txt` et son unique relevé de versions. Le contenu historique reste dans Git.

### `backend/requirements-reporting-models.txt` — supprimé

Ancienne liste de dépendances remplacée par le point d’entrée `backend/requirements.txt` et son unique relevé de versions. Le contenu historique reste dans Git.

### `backend/requirements-reporting-tested.lock.txt` — supprimé

Ancienne liste de dépendances remplacée par le point d’entrée `backend/requirements.txt` et son unique relevé de versions. Le contenu historique reste dans Git.

### `backend/requirements-reporting.txt` — supprimé

Ancienne liste de dépendances remplacée par le point d’entrée `backend/requirements.txt` et son unique relevé de versions. Le contenu historique reste dans Git.

### [backend/requirements-tested.lock.txt](../../backend/requirements-tested.lock.txt)

Décrit l’installation : dépendances directes commentées ou fermeture transitive des versions vérifiées. Les poids, le service Ollama, Tesseract et Chromium sont préparés séparément.

### [backend/requirements.txt](../../backend/requirements.txt)

Décrit l’installation : dépendances directes commentées ou fermeture transitive des versions vérifiées. Les poids, le service Ollama, Tesseract et Chromium sont préparés séparément.

### [backend/tests/test_cps_real.py](../../backend/tests/test_cps_real.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_documents.py](../../backend/tests/test_documents.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_extended_analytics.py](../../backend/tests/test_extended_analytics.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_full_browser.py](../../backend/tests/test_full_browser.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_full_offline.py](../../backend/tests/test_full_offline.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_local_operations.py](../../backend/tests/test_local_operations.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_narrative.py](../../backend/tests/test_narrative.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_presentations.py](../../backend/tests/test_presentations.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [backend/tests/test_synthetic_reference.py](../../backend/tests/test_synthetic_reference.py)

Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.

### [config/business-glossary.json](../../config/business-glossary.json)

Fixe les termes métier dans les cinq langues, les noms propres et sigles admis en arabe, et les confusions interdites entre nuitées, journées et arrivées.

### [config/dimension-aliases.json](../../config/dimension-aliases.json)

Configuration versionnée : champs, unités, domaines, conventions ou vocabulaire. Lue par les services concernés ; ne contient pas de résultats analytiques précalculés.

### [config/geography.json](../../config/geography.json)

Associe six villes à leurs coordonnées Wikidata vérifiées, liens et attribution CC0. Ne contient aucun contour administratif ou chiffre de fréquentation.

### [config/sources.extended.json](../../config/sources.extended.json)

Déclare six vues logiques sur cinq QVD internes : trois références, extension Performance, vue de marge Finance sur cette même extension et piliers de compétitivité. Garde les unités, relations et restrictions de domaine.

### [config/sources.international.json](../../config/sources.international.json)

Configuration versionnée : champs, unités, domaines, conventions ou vocabulaire. Lue par les services concernés ; ne contient pas de résultats analytiques précalculés.

### [config/sources.regional.json](../../config/sources.regional.json)

Configuration versionnée : champs, unités, domaines, conventions ou vocabulaire. Lue par les services concernés ; ne contient pas de résultats analytiques précalculés.

### [config/ttci2019.json](../../config/ttci2019.json)

Déclare les quatre groupes de quatorze piliers et la référence WEF 2019. Indique explicitement les adaptations synthétiques et la différence avec le TTDI actuel.

### [docs/architecture.md](../../docs/architecture.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/contracts.md](../../docs/contracts.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/01-couverture-cps.md](../../docs/full-app/01-couverture-cps.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/02-vue-ensemble.md](../../docs/full-app/02-vue-ensemble.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/03-donnees.md](../../docs/full-app/03-donnees.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/04-analyses.md](../../docs/full-app/04-analyses.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/05-conversation.md](../../docs/full-app/05-conversation.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/06-rapports.md](../../docs/full-app/06-rapports.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/07-interface.md](../../docs/full-app/07-interface.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/08-utilisation.md](../../docs/full-app/08-utilisation.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/09-resultats.md](../../docs/full-app/09-resultats.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/10-perimetre-pedagogique.md](../../docs/full-app/10-perimetre-pedagogique.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/11-completion-cps.md](../../docs/full-app/11-completion-cps.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/12-catalogue-et-conventions.md](../../docs/full-app/12-catalogue-et-conventions.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/14-validation-completion.md](../../docs/full-app/14-validation-completion.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/15-corpus-complementaire.md](../../docs/full-app/15-corpus-complementaire.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/README.md](../../docs/full-app/README.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/full-app/fichiers/outils-tests.md](../../docs/full-app/fichiers/outils-tests.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/salma-changes.md](../../docs/salma-changes.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/salma-local-ai.md](../../docs/salma-local-ai.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [docs/salma-reporting.md](../../docs/salma-reporting.md)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [examples/evaluation/multilingual-development.json](../../examples/evaluation/multilingual-development.json)

Corpus versionné : données documentaires fictives ou cas linguistiques avec attentes. Ces fichiers servent à préparer/évaluer ; ils ne remplacent pas l’inférence ni les calculs du fonctionnement normal.

### [examples/evaluation/multilingual-heldout.json](../../examples/evaluation/multilingual-heldout.json)

Corpus versionné : données documentaires fictives ou cas linguistiques avec attentes. Ces fichiers servent à préparer/évaluer ; ils ne remplacent pas l’inférence ni les calculs du fonctionnement normal.

### [examples/library/corpus.json](../../examples/library/corpus.json)

Corpus versionné : données documentaires fictives ou cas linguistiques avec attentes. Ces fichiers servent à préparer/évaluer ; ils ne remplacent pas l’inférence ni les calculs du fonctionnement normal.

### [frontend/src/features/reports/types.ts](../../frontend/src/features/reports/types.ts)

Étend les types avec audience internationale, question, format quinze pages, identifiants de diagnostics et propositions ; les propriétés antérieures restent compatibles.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/AnalysisCard.tsx](../../frontend/src/features/workspace/AnalysisCard.tsx)

Réutilise le graphique interactif dans chaque analyse tout en conservant formule, unités, sources et avertissement synthétique.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/DiagnosticPanel.tsx](../../frontend/src/features/workspace/DiagnosticPanel.tsx)

Permet de choisir outil, dates, territoire et seuls seuils pertinents. Affiche matrices, benchmark à treize colonnes sélectionnables, carte filtrable et scénario ; les calculs viennent de l’API. Les graphiques restent défilables et accessibles au clavier sur petit écran.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/DocumentsPanel.tsx](../../frontend/src/features/workspace/DocumentsPanel.tsx)

Affiche les métadonnées, le caractère privé/partagé, les passages et l’état d’indexation ; conserve le parcours d’import et de recherche autorisé.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/InteractiveChart.test.tsx](../../frontend/src/features/workspace/InteractiveChart.test.tsx)

Contrôle filtres, focus, valeurs négatives et résultat vide avec des données de test. Ce sont des interactions React, sans serveur ni modèle réel.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/InteractiveChart.tsx](../../frontend/src/features/workspace/InteractiveChart.tsx)

Ajoute filtre temporel, sélection observations/prévisions, info-bulles au survol/focus, courbes et valeurs négatives. Le tableau donne aussi toutes les valeurs et les bornes ; aucun KPI n’est recalculé.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/ReportPanel.tsx](../../frontend/src/features/workspace/ReportPanel.tsx)

Exécute révisions et exports comme tâches, affiche leur étape et permet l’annulation entre étapes. Ajoute propositions sourcées et téléchargement de la présentation PDF de vingt-cinq diapositives.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/Workspace.test.tsx](../../frontend/src/features/workspace/Workspace.test.tsx)

Adapte les assertions à la progression des tâches et conserve les cas de saisie préservée, contexte, restauration refusée et graphique. Les appels API sont simulés explicitement.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/Workspace.tsx](../../frontend/src/features/workspace/Workspace.tsx)

Ajoute la navigation Diagnostics & cartes, les traces des spécialistes, les confirmations de KPI, les étapes/annulations des tâches et la surveillance des alertes. Charge chaque ressource dès sa réponse pour qu’un service lent ne masque pas les analyses disponibles.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/api.ts](../../frontend/src/features/workspace/api.ts)

Soumet les conversations et opérations de rapport comme tâches persistantes, interroge leur état et transmet la progression. Conserve une tâche conversationnelle en attente pour éviter les doublons ; efface cette référence à la déconnexion.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [frontend/src/features/workspace/workspace.css](../../frontend/src/features/workspace/workspace.css)

Ajoute styles des graphiques interactifs, tables défilables et formulaire de diagnostic en deux colonnes sur grand écran, une sur mobile.
Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.

### [pytest.ini](../../pytest.ini)

Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.

### [scripts/build-completion-guide.py](../../scripts/build-completion-guide.py)

Produit le catalogue depuis les définitions et constantes manuelles des tests, puis cet inventaire depuis le diff et les descriptions. N’appelle pas le calcul métier pour fabriquer ses attendus.

### [scripts/evaluate-cps-languages.py](../../scripts/evaluate-cps-languages.py)

Appelle réellement Ollama sur les cas tenus à part, compare l’intention aux attentes versionnées et conserve langue, tâche, durée et erreurs. Les options sélectionnent les cas et le fichier de résultats.

### [scripts/lock-requirements.py](../../scripts/lock-requirements.py)

Décrit l’installation : dépendances directes commentées ou fermeture transitive des versions vérifiées. Les poids, le service Ollama, Tesseract et Chromium sont préparés séparément.

### [scripts/measure-local.py](../../scripts/measure-local.py)

Mesure trois répétitions des outils natifs, enregistre matériel, versions, volumes et état Git. Distingue première lecture et cache chaud ; ne simule aucune inférence ni SLA.

### [scripts/measure-models.py](../../scripts/measure-models.py)

Mesure réellement E5 puis Qwen trois fois, au premier chargement et à chaud. Décharge explicitement Qwen avant sa première mesure, vérifie dimensions/intentions et conserve les durées natives ; ne constitue pas une évaluation aveugle.

### [scripts/prepare-local-ai.py](../../scripts/prepare-local-ai.py)

Prépare séparément service Ollama, poids Qwen/E5 et Tesseract. Épingle les ressources et évite de retélécharger les langues OCR déjà vérifiées ; ne copie aucune DLL dans Windows.

### [scripts/setup-local.ps1](../../scripts/setup-local.ps1)

Installe Python/Chromium/npm, prépare facultativement outils et bibliothèque. Génère la référence seulement si les trois QVD sont absents, refuse une référence partielle et préserve une configuration personnalisée.

### [scripts/start-full-app.ps1](../../scripts/start-full-app.ps1)

Démarre l’API locale avec vrais modèles/OCR, mapping étendu par défaut et surveillance toutes les soixante secondes, tout en respectant les variables de sources déjà configurées.

### [scripts/start-local-ollama.ps1](../../scripts/start-local-ollama.ps1)

Démarre le service d’inférence local, avec un seul modèle et une seule inférence à la fois ; fixe le contexte CPU et garde le cloud désactivé.

