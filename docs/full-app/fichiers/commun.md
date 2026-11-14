# Inventaire : commun

Signatures extraites du code ; descriptions pédagogiques maintenues dans `scripts/build-code-guide.py`. Les imports listés sont statiques : ils ne remplacent pas le parcours guidé des appels par injection.

## `backend/app/__init__.py`

Marque le répertoire comme package Python ; aucune logique métier autonome.

**Exemple :** Permet les imports des modules voisins.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

## `backend/app/core/__init__.py`

Marque le répertoire comme package Python ; aucune logique métier autonome.

**Exemple :** Permet les imports des modules voisins.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

## `backend/app/core/auth.py`

Gère comptes locaux, mots de passe scrypt, cookie opaque, expiration, limitation des connexions et routes login/me/logout.

**Exemple :** resolve(request) transforme le cookie vérifié en AccessContext serveur.

**Utilise :** `app.data_access.synthetic`, `app.schemas.common`

**Importé par :** `backend/app/main.py`

**Classe `Login`** : hérite de Contract.

Champs contrôlés : `username: str`; `password: str`.

**Classe `LocalAuth`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `login(body: Login, request: Request, response: Response)` | Vérifie le mot de passe local et crée une session opaque, avec limitation des tentatives. |
| `me(request: Request)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `logout(request: Request, response: Response)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `LocalAuth.__init__(self, state)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `LocalAuth.bootstrap(self)` | Crée les comptes locaux de développement absents ; ne remplace ni mot de passe ni droits d’un compte déjà présent. |
| `LocalAuth._digest(password, salt)` | Entrées : mot de passe et sel hexadécimal. Résultat : dérivé scrypt utilisé pour comparer les mots de passe sans les stocker en clair. |
| `LocalAuth.login(self, username, password, peer)` | Vérifie le mot de passe local et crée une session opaque, avec limitation des tentatives. |
| `LocalAuth.resolve(self, request)` | Transforme une session valide en AccessContext provenant de la base serveur ; sinon erreur 401. |

## `backend/app/core/config.py`

Centralise les paramètres et chemins, avec valeurs par défaut et variables d’environnement.

**Exemple :** ONMT_FULL_APP=1 sélectionne l’intégration ; ONMT_OCR=1 active le traitement des scans.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/conversation/slots.py`, `backend/app/main.py`, `backend/app/reports/demo.py`, `backend/app/reports/demo_real.py`

**Classe `Settings`**.

Champs contrôlés : `full_app: bool`; `sources_config: Path`; `qvd_root: Path`; `data_dir: Path`; `demo: bool`; `embedding_model: str`; `embedding_revision: str`; `demo_embeddings: bool`; `max_distance: float`; `ollama_model: str`; `generation_mode: str`; `ollama_timeout: float`; `ollama_context: int`; `ocr_enabled: bool`; `tesseract_path: str`; `tessdata_path: str`; `ocr_languages: str`; `ocr_timeout: int`; `max_pdf_bytes: int`; `max_pages: int`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `Settings.__post_init__(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Settings.uses_llm(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/core/errors.py`

Définit AppError, qui transporte code, message et statut HTTP ; forbidden évite de révéler une ressource interdite.

**Exemple :** Un accès Finance interdit produit forbidden/403.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/analytics/anomalies.py`, `backend/app/analytics/forecasting.py`, `backend/app/analytics/router.py`, `backend/app/analytics/service.py`, `backend/app/conversation/context.py`, `backend/app/conversation/intent.py`, `backend/app/conversation/router.py`, `backend/app/conversation/service.py`, `backend/app/core/auth.py`, `backend/app/core/llm_client.py`, `backend/app/core/security.py`, `backend/app/core/state.py`, `backend/app/data_access/catalog.py`, `backend/app/data_access/qvd_reader.py`, `backend/app/main.py`, `backend/app/reports/adapters.py`, `backend/app/reports/export.py`, `backend/app/reports/generation.py`, `backend/app/reports/ingestion.py`, `backend/app/reports/narrative.py`, `backend/app/reports/ocr.py`, `backend/app/reports/retrieval.py`, `backend/app/reports/revisions.py`, `backend/app/reports/router.py`, `backend/app/reports/service.py`, `backend/app/reports/storage.py`, `backend/app/reports/validation.py`

**Classe `AppError`** : hérite de Exception.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `forbidden()` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `AppError.__init__(self, code: str, message: str, status: int=400)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |

## `backend/app/core/llm_client.py`

Appelle Ollama localhost avec schéma JSON, vérifie le modèle local et gère délais, erreurs et sorties tronquées.

**Exemple :** generate_json(schema,system,payload) rend le texte JSON réel du modèle ou lève AppError.

**Utilise :** `app.schemas.common`

**Importé par :** `backend/app/main.py`

**Classe `EditorialPlan`** : hérite de Contract.

Champs contrôlés : `style: Literal['concise', 'detailed']`; `evidence_ids: list[str]`.

**Classe `OllamaPlanner`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `OllamaPlanner.__init__(self, model: str, timeout=240, context=4096)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `OllamaPlanner.generate_json(self, schema, system, payload)` | Entrées : schéma, consigne et données. Résultat : JSON brut du modèle local ; aucune arithmétique ou commande libre. |
| `OllamaPlanner.plan(self, language, audience, instruction, evidence)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/core/runtime.py`

Prépare les DLL C++ de la venv Windows avant le chargement de PyTorch, sans modifier Windows.

**Exemple :** Le premier encodage E5 peut charger VCRUNTIME140_1.dll depuis .venv/Scripts.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/reports/retrieval.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `prepare_torch_runtime()` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/core/security.py`

Définit ResourcePolicy et les contrôles de rôles, modules, territoires et propriétaire utilisés par documents et rapports.

**Exemple :** Un utilisateur régional ne lit pas un rapport privé du compte direction.

**Utilise :** `app.schemas.common`

**Importé par :** `backend/app/reports/adapters.py`, `backend/app/reports/demo.py`, `backend/app/reports/demo_real.py`, `backend/app/reports/documents.py`, `backend/app/reports/ingestion.py`, `backend/app/reports/retrieval.py`, `backend/app/reports/router.py`, `backend/app/reports/service.py`

**Classe `ResourcePolicy`** : hérite de Contract.

Champs contrôlés : `owner_id: str`; `roles: list[str]`; `modules: list[str]`; `territories: list[str]`; `classification: str`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `require_module(access: AccessContext, edit: bool=False)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `can_read(policy: ResourcePolicy, access: AccessContext)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. Retour typé : `bool`. |
| `authorize(policy: ResourcePolicy, access: AccessContext, edit: bool=False)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `private_policy(access: AccessContext)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. Retour typé : `ResourcePolicy`. |
| `demo_access()` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. Retour typé : `AccessContext`. |

## `backend/app/core/state.py`

Persiste l’état applicatif local dans SQLite : analyses calculées, conversations versionnées, alertes, comptes et sessions. Ne copie pas les tables QVD.

**Exemple :** save_conversation(cid,owner,payload,base) refuse une version de base obsolète.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/main.py`

**Classe `AppState`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `AppState.__init__(self, directory: Path)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `AppState.connect(self)` | Ouvre une connexion SQLite avec transaction et fermeture garanties ; le bloc appelant reçoit la connexion. |
| `AppState.save_analysis(self, analysis, owner, request, scope)` | Entrées : résultat, propriétaire, demande initiale et périmètre autorisé. Conserve un instantané calculé, pas les lignes QVD. |
| `AppState.analysis(self, analysis_id, owner)` | Entrées : identifiant et propriétaire. Résultat : instantané de l’analyse autorisée ou None. |
| `AppState.list_analyses(self, owner)` | Entrée : propriétaire. Résultat : les cent derniers instantanés de ses analyses ; la fraîcheur est ensuite recontrôlée par le service. |
| `AppState.conversation(self, cid, owner)` | Entrées : identifiant et propriétaire. Résultat : historique/contexte/version enregistrés, ou None si la ressource ne lui appartient pas. |
| `AppState.save_conversation(self, cid, owner, payload, base)` | Entrées : identifiant, propriétaire, charge utile et version de base. Sauvegarde atomique ou conflit explicite. |

## `backend/app/main.py`

Assemble FastAPI, les services et leurs adaptateurs ; monte les routes et transforme les erreurs en réponses contrôlées.

**Exemple :** Démarrer start-full-app.ps1 construit le fournisseur QVD et l’authentification locale.

**Utilise :** `app.analytics.anomalies`, `app.analytics.router`, `app.analytics.service`, `app.conversation.intent`, `app.conversation.router`, `app.conversation.service`, `app.core.auth`, `app.core.config`, `app.core.errors`, `app.core.llm_client`, `app.core.state`, `app.data_access.catalog`, `app.reports.adapters`, `app.reports.export`, `app.reports.ingestion`, `app.reports.narrative`, `app.reports.retrieval`, `app.reports.router`, `app.reports.service`, `app.reports.storage`

**Importé par :** `backend/app/reports/demo.py`, `backend/app/reports/demo_real.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `create_app(settings=None, provider=None, access_resolver=None, embedder=None, exporter=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/schemas/__init__.py`

Marque le répertoire comme package Python ; aucune logique métier autonome.

**Exemple :** Permet les imports des modules voisins.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

## `backend/app/schemas/analysis.py`

Définit demande/résultat d’analyse et points observés/prévus, avec règles de comparaison, horizon et intervalles.

**Exemple :** AnalysisRequest compare exige comparison_period ; AnalysisResult conserve formule et is_synthetic.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/analytics/forecasting.py`, `backend/app/analytics/router.py`, `backend/app/analytics/service.py`, `backend/app/conversation/context.py`, `backend/app/reports/adapters.py`, `backend/app/reports/export.py`, `backend/app/reports/service.py`

**Classe `AnalysisRequest`** : hérite de Contract.

Champs contrôlés : `request_id: str`; `operation: Literal['value', 'compare', 'forecast']`; `metric_id: str`; `period: Period`; `comparison_period: Period | None`; `filters: dict`; `language: Language`; `forecast_horizon: int | None`; `forecast_frequency: Literal['month', 'quarter', 'year'] | None`.

**Classe `SeriesPoint`** : hérite de Contract.

Champs contrôlés : `date: date`; `value: Number | None`; `kind: Literal['observed', 'forecast']`; `lower: Number | None`; `upper: Number | None`.

**Classe `AnalysisResult`** : hérite de Contract.

Champs contrôlés : `request_id: str`; `analysis_id: str`; `metric_id: str`; `status: Literal['ok', 'partial', 'unavailable']`; `period: Period`; `comparison_period: Period | None`; `filters: dict`; `unit: str`; `values: dict[str, Number | None]`; `series: list[SeriesPoint]`; `formula: str`; `sources: list[SourceReference]`; `warnings: list[str]`; `is_synthetic: bool`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `AnalysisRequest.operation_fields(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `SeriesPoint.bounds(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `AnalysisResult.unavailable_warning(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/schemas/common.py`

Définit les contrats communs stricts, langues, périodes, sources, identité et erreurs.

**Exemple :** Period refuse une date de fin antérieure au début.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/analytics/service.py`, `backend/app/conversation/intent.py`, `backend/app/conversation/router.py`, `backend/app/core/auth.py`, `backend/app/core/llm_client.py`, `backend/app/core/security.py`, `backend/app/reports/adapters.py`, `backend/app/reports/documents.py`, `backend/app/reports/narrative.py`, `backend/app/reports/router.py`, `backend/app/schemas/analysis.py`, `backend/app/schemas/report.py`

**Classe `Contract`** : hérite de BaseModel.

**Classe `Period`** : hérite de Contract.

Champs contrôlés : `start: date`; `end: date`.

**Classe `SourceReference`** : hérite de Contract.

Champs contrôlés : `source_id: str`; `source_type: Literal['qvd', 'document', 'external']`; `name: str`; `version: str`; `fields: list[str]`; `pages: list[int]`.

**Classe `AccessContext`** : hérite de Contract.

Champs contrôlés : `user_id: str`; `roles: list[str]`; `allowed_modules: list[str]`; `allowed_territories: list[str]`.

**Classe `ErrorResponse`** : hérite de Contract.

Champs contrôlés : `request_id: str`; `code: str`; `message: str`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `Period.ordered(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `SourceReference.pages_valid(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/schemas/report.py`

Définit demandes, sections, résultats et modifications de rapport avec version de base.

**Exemple :** ReportRevisionRequest porte report_id, base_version, section_id et instruction.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/conversation/service.py`, `backend/app/reports/demo.py`, `backend/app/reports/demo_real.py`, `backend/app/reports/generation.py`, `backend/app/reports/narrative.py`, `backend/app/reports/router.py`, `backend/app/reports/service.py`

**Classe `ReportRequest`** : hérite de Contract.

Champs contrôlés : `request_id: str`; `analysis_ids: list[str]`; `title: str`; `language: Language`; `audience: Literal['direction', 'ministere', 'regional']`; `sections: list[SectionId]`.

**Classe `ReportSection`** : hérite de Contract.

Champs contrôlés : `section_id: SectionId`; `title: str`; `content: str`; `source_ids: list[str]`.

**Classe `ReportResult`** : hérite de Contract.

Champs contrôlés : `request_id: str`; `report_id: str`; `version: int`; `status: Literal['pending', 'running', 'completed', 'failed']`; `sections: list[ReportSection]`; `sources: list[SourceReference]`; `download_path: str | None`; `warnings: list[str]`; `is_synthetic: bool`.

**Classe `ReportRevisionRequest`** : hérite de Contract.

Champs contrôlés : `request_id: str`; `report_id: str`; `base_version: int`; `section_id: SectionId`; `instruction: str`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `ReportRequest.unique(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ReportResult.references(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
