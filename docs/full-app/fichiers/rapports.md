# Inventaire : rapports

Signatures extraites du code ; descriptions pédagogiques maintenues dans `scripts/build-code-guide.py`. Les imports listés sont statiques : ils ne remplacent pas le parcours guidé des appels par injection.

## `backend/app/reports/__init__.py`

Marque le répertoire comme package Python ; aucune logique métier autonome.

**Exemple :** Permet les imports des modules voisins.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

## `backend/app/reports/adapters.py`

Définit le protocole AnalysisProvider et les fournisseurs historiques non connecté ou à fixtures explicites.

**Exemple :** L’application complète injecte AnalyticsService à la place de SyntheticAnalysisProvider.

**Utilise :** `app.core.errors`, `app.core.security`, `app.schemas.analysis`, `app.schemas.common`

**Importé par :** `backend/app/main.py`

**Classe `AnalysisProvider`** : hérite de Protocol.

**Classe `UnconnectedAnalysisProvider`**.

**Classe `SyntheticAnalysisProvider`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `AnalysisProvider.get_analysis(self, analysis_id: str, access_context: AccessContext)` | Entrées : identifiant et accès. Résultat : analyse du propriétaire avec droits et version de source contrôlés. Retour typé : `AnalysisResult`. |
| `UnconnectedAnalysisProvider.get_analysis(self, analysis_id, access_context)` | Entrées : identifiant et accès. Résultat : analyse du propriétaire avec droits et version de source contrôlés. |
| `SyntheticAnalysisProvider.__init__(self, fixture_dir: Path)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `SyntheticAnalysisProvider.get_analysis(self, analysis_id, access_context)` | Entrées : identifiant et accès. Résultat : analyse du propriétaire avec droits et version de source contrôlés. |

## `backend/app/reports/demo.py`

Conserve le scénario historique Salma, explicitement à analyses/gabarits/embeddings de démonstration.

**Exemple :** Ce script ne démontre pas l’intégration QVD ni un vrai LLM.

**Utilise :** `app.core.config`, `app.core.security`, `app.main`, `app.schemas.report`

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `main()` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/reports/demo_real.py`

Crée un PDF mixte fictif et montre OCR/E5/Ollama/PDF sur les anciennes fixtures synthétiques Salma.

**Exemple :** synthetic_mixed_pdf() est aussi réutilisé par le test réel de la nouvelle intégration.

**Utilise :** `app.core.config`, `app.core.security`, `app.main`, `app.schemas.report`

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `synthetic_mixed_pdf()` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `main()` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/reports/documents.py`

Décrit métadonnées, passages, document versionné et preuves ; construit une référence exacte pour un passage.

**Exemple :** reference(doc,passage) inclut identifiant du passage, version et pages physiques.

**Utilise :** `app.core.security`, `app.schemas.common`

**Importé par :** `backend/app/reports/demo_real.py`, `backend/app/reports/ingestion.py`, `backend/app/reports/retrieval.py`, `backend/app/reports/router.py`, `backend/app/reports/service.py`

**Classe `DocumentMetadata`** : hérite de Contract.

Champs contrôlés : `title: str`; `language: Language`; `publisher: str`; `issued_on: str`.

**Classe `Passage`** : hérite de Contract.

Champs contrôlés : `chunk_id: str`; `document_id: str`; `version: int`; `page_start: int`; `page_end: int`; `text: str`; `language: Language`; `extraction_method: Literal['text', 'ocr']`; `ocr_confidence: float | None`.

**Classe `DocumentRecord`** : hérite de Contract.

Champs contrôlés : `document_id: str`; `version: int`; `sha256: str`; `metadata: DocumentMetadata`; `policy: ResourcePolicy`; `passages: list[Passage]`; `warnings: list[str]`; `processing_signature: str`.

**Classe `Evidence`** : hérite de Contract.

Champs contrôlés : `passage: Passage`; `source: SourceReference`; `distance: float`.

**Classe `EvidenceResult`** : hérite de Contract.

Champs contrôlés : `evidence: list[Evidence]`; `warnings: list[str]`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `reference(doc: DocumentRecord, passage: Passage)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. Retour typé : `SourceReference`. |

## `backend/app/reports/export.py`

Prépare les faits et graphiques, applique le template HTML puis rend le PDF avec Chromium sans requêtes réseau du document.

**Exemple :** render(payload) retourne les octets PDF ou une erreur explicite.

**Utilise :** `app.core.errors`, `app.schemas.analysis`

**Importé par :** `backend/app/main.py`

**Classe `PDFExporter`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `PDFExporter.render(self, payload)` | Entrée : instantané de rapport. Résultat : octets du PDF produit par Chromium. |

## `backend/app/reports/generation.py`

Définit les textes contrôlés multilingues, la table des faits et la génération par gabarits explicite.

**Exemple :** facts(analyses) extrait les valeurs déjà calculées ; render_fact restitue unité, période, filtres et sources.

**Utilise :** `app.core.errors`, `app.schemas.report`

**Importé par :** `backend/app/reports/export.py`, `backend/app/reports/narrative.py`, `backend/app/reports/service.py`, `backend/app/reports/validation.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `number(value, unavailable)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `facts(analyses)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `render_fact(row, t)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `revision_style(instruction)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `generate_sections(request, analyses, evidence, styles=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `generate_edited_sections(request, analyses, evidence, styles=None, section_settings=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/reports/ingestion.py`

Contrôle et importe un PDF, traite texte/scans, découpe en passages, indexe et conserve les versions et originaux.

**Exemple :** ingest_pdf(content,metadata,access,document_id) renvoie document et booléen de doublon.

**Utilise :** `app.core.errors`, `app.core.security`

**Importé par :** `backend/app/main.py`

**Classe `DocumentService`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `DocumentService.__init__(self, store, index, settings)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `DocumentService.reindex(self, access_context)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `DocumentService.ingest_pdf(self, content: bytes, metadata: DocumentMetadata, access_context, document_id=None)` | Entrées : PDF, métadonnées, accès et identifiant éventuel. Résultat : document versionné et indicateur de doublon. |
| `DocumentService._ingest(self, content, metadata, access, document_id)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/reports/narrative.py`

Fait rédiger une prose locale, injecte les faits exacts et contrôle les éléments vérifiables et erreurs linguistiques identifiées.

**Exemple :** generate_section(request,id,analyses,evidence,options) retourne section et manifeste de génération.

**Utilise :** `app.core.errors`, `app.schemas.common`, `app.schemas.report`

**Importé par :** `backend/app/main.py`, `backend/app/reports/validation.py`

**Classe `NarrativeDraft`** : hérite de Contract.

Champs contrôlés : `body: str`.

**Classe `EditorialDraft`** : hérite de Contract.

Champs contrôlés : `introductions: dict[str, str]`; `closing: str`.

**Classe `NarrativeWriter`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `ledger_for(section_id, analyses, evidence)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `validate_draft(draft, ledger)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `render_draft(section_id, draft, ledger, language, audience, analyses)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `verify_narrative(result, request, analyses, evidence, manifests)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `NarrativeWriter.__init__(self, client)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `NarrativeWriter.generate_section(self, request, section_id, analyses, evidence, options=None)` | Entrées : rapport, section, analyses, preuves et options. Résultat : ReportSection et manifeste contenant la prose contrôlée. |

## `backend/app/reports/ocr.py`

Rend une page et exécute Tesseract local avec langues, limite de pixels, délai et avertissements de relecture.

**Exemple :** extract_page(pdf_bytes,index) retourne texte, confiance moyenne et avertissements.

**Utilise :** `app.core.errors`

**Importé par :** `backend/app/reports/ingestion.py`

**Classe `LocalOCR`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `LocalOCR.__init__(self, settings)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `LocalOCR.extract_page(self, content: bytes, page_index: int)` | Entrées : octets PDF et index de page. Résultat : texte OCR, score moyen et avertissements. |

## `backend/app/reports/retrieval.py`

Définit encodeurs réel/de test, collection Chroma par modèle et recherche sur documents autorisés.

**Exemple :** search_evidence(question,access,limit) retourne des passages citables et des avertissements.

**Utilise :** `app.core.errors`, `app.core.runtime`, `app.core.security`

**Importé par :** `backend/app/main.py`

**Classe `Embedder`** : hérite de Protocol.

Champs contrôlés : `identity: str`.

**Classe `LocalSentenceEmbedder`**.

**Classe `DemoHashEmbedder`**.

**Classe `ChromaIndex`**.

**Classe `Retriever`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `Embedder.encode(self, texts: list[str], query: bool=False)` | Entrées : textes et indicateur question/passage. Résultat : vecteurs normalisés ; encodeur réel ou test explicitement distinct. Retour typé : `list[list[float]]`. |
| `LocalSentenceEmbedder.__init__(self, model_path: str, revision: str)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `LocalSentenceEmbedder.encode(self, texts, query=False)` | Entrées : textes et indicateur question/passage. Résultat : vecteurs normalisés ; encodeur réel ou test explicitement distinct. |
| `DemoHashEmbedder.encode(self, texts, query=False)` | Entrées : textes et indicateur question/passage. Résultat : vecteurs normalisés ; encodeur réel ou test explicitement distinct. |
| `ChromaIndex.__init__(self, directory, embedder)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `ChromaIndex.collection(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ChromaIndex.add(self, doc: DocumentRecord)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ChromaIndex.remove(self, doc: DocumentRecord)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ChromaIndex.query(self, question, allowed_versions, limit)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Retriever.__init__(self, store, index, max_distance=0.35)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `Retriever.search_evidence(self, question, access_context, limit=5)` | Recherche parmi les versions et documents permis ; retourne EvidenceResult avec références vérifiables. |

## `backend/app/reports/revisions.py`

Convertit une consigne éditoriale connue en paramètres de section ; refuse les demandes inconnues ou nouveaux calculs isolés.

**Exemple :** parse_revision("langue:ar") donne la langue de section ; un nouveau KPI doit passer par Doha.

**Utilise :** `app.core.errors`

**Importé par :** `backend/app/reports/service.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `parse_revision(instruction)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/reports/router.py`

Expose les routes protégées Salma : rapports, documents, preuves, versions et PDF.

**Exemple :** get_access_context(request) utilise le résolveur serveur ; la démo historique est un mode distinct.

**Utilise :** `app.core.errors`, `app.core.security`, `app.schemas.common`, `app.schemas.report`

**Importé par :** `backend/app/analytics/router.py`, `backend/app/conversation/router.py`, `backend/app/main.py`

**Classe `SearchRequest`** : hérite de Contract.

Champs contrôlés : `question: str`; `limit: int`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `get_access_context(request: Request)` | Point de branchement de l'authentification serveur de Hayat. Retour typé : `AccessContext`. |
| `config(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `create(body: ReportRequest, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `listing(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `read(report_id: str, request: Request, access: Access, version: int \| None=Query(default=None, gt=0))` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `revise(report_id: str, section_id: str, body: ReportRevisionRequest, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `export(report_id: str, request: Request, access: Access, version: int \| None=Query(default=None, gt=0))` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `download(report_id: str, request: Request, access: Access, version: int \| None=Query(default=None, gt=0), inline: bool=False)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `search(body: SearchRequest, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `reindex(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `documents(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `passage(chunk_id: str, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `upload(request: Request, access: Access, file: Annotated[UploadFile, File()], metadata: Annotated[str, Form()], document_id: Annotated[str \| None, Form()]=None)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `original(document_id: str, request: Request, access: Access, version: int \| None=Query(default=None, gt=0))` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |

## `backend/app/reports/service.py`

Orchestre création, lecture autorisée, révision, recalcul depuis de nouvelles analyses, export et téléchargement.

**Exemple :** recalculate_report(id,analysis_ids,base,access) conserve l’identifiant et crée la version suivante.

**Utilise :** `app.core.errors`, `app.core.security`, `app.schemas.analysis`, `app.schemas.report`

**Importé par :** `backend/app/main.py`

**Classe `ReportService`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `ReportService.__init__(self, store, provider, retriever, planner=None, writer=None)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `ReportService._analyses(self, ids, access)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ReportService.create_report(self, request: ReportRequest, access_context, *, report_id=None, base_version=None, section_settings=None)` | Charge les analyses autorisées, cherche les preuves, rédige/contrôle et conserve un ReportResult versionné. Retour typé : `ReportResult`. |
| `ReportService.recalculate_report(self, report_id, analysis_ids, base_version, access, title=None)` | Utilise de nouveaux identifiants d’analyse déjà calculés ; conserve le rapport et crée une version. |
| `ReportService._authorized(self, report_id, access, version=None, edit=False, allow_stale=False)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ReportService.get_report(self, report_id, access_context, version=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ReportService.list_reports(self, access_context)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ReportService.revise_report(self, request, access_context)` | Applique une opération éditoriale aux sections concernées ; refuse base_version obsolète. |
| `ReportService.export_pdf(self, report_id, access_context, exporter, version=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ReportService.download_pdf(self, report_id, access_context, version=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/reports/storage.py`

Conserve documents, originaux, rapports, versions, PDF et audit applicatif dans SQLite local.

**Exemple :** save_report(payload,base_version) utilise une transaction pour éviter l’écrasement concurrent.

**Utilise :** `app.core.errors`

**Importé par :** `backend/app/main.py`

**Classe `Store`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `Store.__init__(self, directory: Path)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `Store.connect(self)` | Ouvre une connexion SQLite avec transaction et fermeture garanties ; le bloc appelant reçoit la connexion. |
| `Store.documents(self, current=True)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.document(self, doc_id, version=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.save_document(self, payload, original_pdf)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.document_pdf(self, doc_id, version)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.report(self, report_id, version=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.report_ids(self)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.save_report(self, payload, base_version=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.save_pdf(self, report_id, version, content)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.pdf(self, report_id, version)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `Store.audit(self, user_id, request_id, action, resource_id)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/reports/validation.py`

Vérifie sections, sources, chiffres et marqueur synthétique d’un rapport avant conservation.

**Exemple :** verify_report(...) compare la sortie à son manifeste ou au gabarit explicitement utilisé.

**Utilise :** `app.core.errors`

**Importé par :** `backend/app/reports/service.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `collect_sources(analyses, evidence)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `verify_report(result, request, analyses, evidence, styles, narratives=None, section_settings=None)` | La rédaction contrôlée est reconstruite depuis les valeurs typées pour bloquer toute altération. |
