# Module Salma : documents, RAG et rapports

> **Évolution du 8 novembre 2026 :** le guide actuel est [salma-local-ai.md](salma-local-ai.md). Le présent document conserve le fonctionnement et le diagnostic initiaux du 4 novembre ; ses mentions « OCR absent », « Ollama non exécuté » et « DLL bloquée » décrivent cet état historique.

État vérifié le 4 novembre 2026, sur `salma/reporting-rag`. Ce module est un prototype local exécutable. Il ne constitue pas une validation de conformité à tout le CPS.

## Ce qui a été examiné

Au départ, le dépôt contenait le README, `docs/contracts.md` v0.1 et des emplacements Python vides. `AGENTS.md` et `docs/architecture.md` étaient vides. `examples/contracts/` ne contenait que `.gitkeep` : les neuf exemples JSON présents maintenant ont été ajoutés pour cette implémentation. Les modules de Hayat et Doha restent vides.

La modification préexistante de `backend/requirements.txt` a été conservée intégralement. Aucun changement de branche, commit, push, fusion ou déploiement n’a été effectué.

Documents accessibles et lus localement :

- `C:\Users\OWNEER\Downloads\ONMT_Developpement_Taches_Pipeline (1).pdf` : 25 pages textuelles, notamment S1–S4 p. 14–17, contrats p. 18 et sécurité p. 20.
- `C:\Users\OWNEER\Downloads\CPS (1).pdf` : 24 pages avec texte extractible ; extraction parfois irrégulière, donc les tableaux complexes doivent être relus dans le PDF. Rapports p. 14, confidentialité p. 14–15, architecture p. 15–17 et POC p. 19–20.

Ces documents sont des références de besoins. Les contrats JSON simplifiés du guide PDF ne remplacent pas `docs/contracts.md`. Les PDF ne sont pas ajoutés au corpus RAG, ni envoyés à un service externe. Leur extraction de travail reste sous `local_data/specs/`, hors Git.

## Lancer le parcours de démonstration sous PowerShell

Depuis la racine du dépôt, avec Python 3.11 et Node 22.12 ou une version compatible :

```powershell
Set-Location C:\Users\OWNEER\onmt-ai
python --version
node --version
npm --version
# À faire si .venv n’existe pas encore :
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-reporting.txt
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\local_data\browsers"
.\.venv\Scripts\python.exe -m playwright install chromium
Push-Location frontend
npm ci
Pop-Location
```

Le sous-ensemble `requirements-reporting.txt` suffit à la démo et aux tests hors vrais modèles. Il évite d’installer les dépendances métier des autres membres. `requirements-reporting-models.txt` ajoute les bibliothèques IA optionnelles. Le fichier `requirements-reporting-tested.lock.txt` est un relevé complet des paquets installés sur ce poste, **pas une certification de leur inférence** : l’import PyTorch est bloqué, voir ci-dessous. `frontend/package-lock.json` fixe la résolution npm.

Terminal 1, backend :

```powershell
Set-Location C:\Users\OWNEER\onmt-ai
$env:ONMT_DEMO = '1'
$env:ONMT_DEMO_EMBEDDINGS = '1'
$env:ONMT_OLLAMA_MODEL = ''
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Terminal 2, frontend :

```powershell
Set-Location C:\Users\OWNEER\onmt-ai\frontend
npm run dev
```

Ouvrir `http://127.0.0.1:5173`. L’API est documentée sur `http://127.0.0.1:8000/docs`. Vite relaie `/api` vers le backend : aucun rôle ni territoire n’est transmis par le navigateur comme preuve d’autorisation. Arrêter les serveurs avec Ctrl+C. Utiliser un seul worker pour ce prototype local.

Le bandeau de démo annonce l’identité simulée et les données synthétiques. Cliquer sur **Générer le rapport**, modifier une section avec **Résumer** ou **Détailler**, puis **Préparer le PDF** et **Télécharger le PDF**. La liste de gauche recharge la dernière version ; le sélecteur consulte l’historique. Une édition depuis une ancienne version échoue avec `version_conflict`.

L’attente affichée correspond à la requête HTTP en cours. Il n’y a ni queue de travaux durable, ni `job_id`, ni reprise automatique après arrêt du processus. Un rapport n’est enregistré qu’après génération et vérification réussies. `download_path` reste `null` avant un export réussi.

Pour créer un exemple sans interface, avec cinq modifications successives :

```powershell
Set-Location C:\Users\OWNEER\onmt-ai
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.reports.demo
```

Le JSON et le PDF synthétiques sont produits dans `local_data/demo-reporting/` en version 6. Aucun chiffre réel ONMT n’est utilisé.

Exemple API reproductible :

```powershell
$body = Get-Content examples\contracts\report_request.json -Raw -Encoding UTF8
$report = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/reports -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
$report.report_id
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/reports/$($report.report_id)/export"
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/reports/$($report.report_id)/pdf" -OutFile local_data\rapport-demo.pdf
```

## Rôle des fichiers et choix techniques

| Fichier | Rôle |
| --- | --- |
| `schemas/common.py`, `analysis.py`, `report.py` | Valider les contrats : dates, langues, champs, valeurs absentes, références et versions. Les entiers ne sont pas convertis en flottants, pour conserver les grands nombres. |
| `core/config.py`, `security.py`, `errors.py` | Configuration locale, contexte d’accès et politique testable, erreurs communes sans trace technique dans le navigateur. |
| `core/llm_client.py` | Adaptateur Ollama optionnel, sortie JSON bornée et validation des identifiants documentaires. |
| `reports/adapters.py` | Interface de Doha, fournisseur non connecté qui refuse, fournisseur synthétique uniquement en démo. |
| `reports/ingestion.py`, `documents.py` | Extraction pdfplumber, numéros physiques de pages, nettoyage prudent, passages, empreinte SHA-256, versions et droits. |
| `reports/retrieval.py` | Embeddings locaux, Chroma persistant, filtrage des documents autorisés, seuil de distance et références aux passages. |
| `reports/generation.py`, `validation.py` | Sections contrôlées dans cinq langues, trois audiences, injection directe des valeurs, unités et sources. Vérification avant sauvegarde. |
| `reports/storage.py` | SQLite transactionnel, originaux PDF, passages, versions, instantanés analytiques, exports et journal local. |
| `reports/service.py` | Fonctions que Hayat appellera, vérifications des droits, dépendances entre sections, comparaison atomique de version. |
| `reports/export.py`, `templates/report.html` | HTML/CSS échappé, tableaux, petits graphiques SVG, sources, avertissements, RTL et impression Chromium. |
| `reports/router.py`, `main.py` | Routes FastAPI et assemblage minimal du backend, sans implémenter le métier des autres membres. |
| `frontend/src/features/reports/` | Écran React, appels API, types TypeScript et tests d’interface. |
| `backend/tests/` | Contrats, permissions, fidélité, RAG, PDF et parcours navigateur. |

Le workflow est séquentiel : autoriser → récupérer les analyses → rechercher les preuves → rédiger → vérifier → conserver. LangGraph n’ajouterait pas ici de reprise ni de parallélisme utiles. Il pourra être intégré par Hayat au parcours conversationnel global.

### Documents et preuves

L’import nécessite `report_editor` et `document_editor`. Le serveur attribue la politique depuis le contexte authentifié : les droits ne sont pas choisis dans le formulaire. Le prototype utilise la classification `internal`, le module `reports`, les territoires du compte et le rôle `report_editor`. La modification d’un document est réservée à son propriétaire.

Chaque document conserve titre, langue, organisme, date déclarée, version, droits et original PDF. L’API accepte `publisher` et `issued_on` dans les métadonnées ; le formulaire minimal collecte le titre et la langue. Un même contenu/mêmes métadonnées retourne le document existant avec `duplicate: true`. Un contenu changé et son `document_id` créent une nouvelle version ; les anciens vecteurs sont supprimés, les anciennes références restent consultables. Un PDF identique avec d’autres métadonnées est refusé explicitement pour éviter une mise à jour implicite.

Les passages gardent leur page physique et environ 600 caractères, avec recouvrement de 60 caractères. Les lignes de bord très répétées sont retirées. Les tableaux complexes, colonnes et numéros imprimés différents des pages physiques ne sont pas interprétés automatiquement. Une relecture de l’extraction reste nécessaire.

Un PDF sans texte est refusé comme probablement scanné : **OCR non implémenté**. Un PDF mixte est accepté avec les pages sans texte signalées. Limites : 20 Mio et 200 pages. Il n’y a pas de moteur antivirus ni d’isolation forte des parseurs dans ce prototype.

Le backend établit la liste des versions documentaires autorisées **avant** la requête Chroma. Il filtre encore les résultats contre le registre SQLite, qui reste la référence. Les textes sont repris de ce registre, jamais d’une métadonnée d’index arbitraire. Un `source_id` documentaire est le `chunk_id` : document, version, page et passage sont retrouvables sans modifier le contrat commun. Le passage et l’original peuvent être consultés par routes protégées.

Aucun passage trouvé ou sous le seuil donne `documentary_evidence_absent` ou `documentary_evidence_insufficient`. La distance cosinus n’est pas une probabilité de vérité. Le seuil initial `0.35` doit être calibré sur un jeu documentaire réel ; la qualité sémantique et le rappel ne sont pas validés sur corpus ONMT.

### Rédaction et modifications

Les analyses sont des instantanés du fournisseur de Doha. Salma ne lit pas les QVD et ne recalcule ni total, ni variation, ni prévision. `change_pct` utilise `%`, les autres valeurs gardent l’unité fournie ; `previous` garde la période de comparaison. `null` s’affiche comme indisponible. Les observations, prévisions, intervalles fournis et hypothèses sont distingués. Une analyse sans sources ne produit pas de constat numérique et déclenche un avertissement.

La rédaction actuelle utilise des phrases et sections contrôlées. Elle adapte les en-têtes, les limites et l’introduction à la langue et au destinataire. Les identifiants métier, unités et citations originales ne sont pas traduits automatiquement. Les recommandations prudentes renvoient à un constat source et demandent une vérification métier ; aucun lien causal ou scénario chiffré n’est inventé.

Ollama, s’il est activé, choisit uniquement `concise` / `detailed` et des passages déjà autorisés. Son texte libre n’est pas publié comme assertion économique. Le contexte documentaire est un objet JSON de données non fiables dans le message utilisateur, distinct du message système. Les identifiants retournés doivent appartenir aux passages fournis. Même une injection documentaire réussissant à influencer ce choix ne peut ajouter un chiffre ni une nouvelle référence. Cela ne remplace pas une évaluation adversariale complète.

Les modifications acceptées sont explicitement bornées : **résumer** et **détailler**. Un changement de marché, de période, d’analyse ou de langue d’un rapport existant n’est pas implémenté par `ReportRevisionRequest` v0.1 ; il nécessite une nouvelle demande ou un contrat élargi. Voir les propositions de contrat ci-dessous. Il n’y a pas de remplacement silencieux par une donnée fictive si un fournisseur réel ou Ollama échoue.

Les dépendances sont enregistrées dans le service : diagnostic/comparaison/prévisions → synthèse, recommandations, limites ; recommandations/limites → synthèse. Les sections concernées sont reconstruites sur les mêmes preuves, leurs numéros de version internes sont mis à jour, les autres restent identiques. SQLite vérifie `base_version` dans une transaction `BEGIN IMMEDIATE` : deux modifications concurrentes ne peuvent pas écraser la même version.

### Conservation et accès

Tout est stocké sous `local_data/reporting/` par défaut, exclu de Git :

- `reporting.sqlite3` : originaux PDF en BLOB, métadonnées et passages, chaque version de rapport, analyses/preuves d’origine, version interne des sections, PDF associés et événements locaux.
- `chroma/` : index persistant séparé par identité du modèle et révision.
- `local_data/browsers/` : Chromium ; `local_data/models/` : modèles éventuellement préparés localement.

`ONMT_DATA_DIR` permet un autre emplacement. Les versions sont conservées sans purge automatique pendant le prototype ; aucun calendrier réglementaire de rétention n’est revendiqué. Les fichiers ne sont pas chiffrés par l’application. L’accès direct au disque doit être limité par Windows. Une migration vers PostgreSQL et un stockage chiffré devra être décidée avant usage réel.

Les rapports sont privés à leur propriétaire. Toute création, lecture, liste, modification, export et tout téléchargement vérifient les droits. Les droits des analyses sont redemandés au fournisseur de Doha à chaque accès ; les droits de la version documentaire citée et de sa version courante sont revérifiés. La politique effective du rapport est donc au moins aussi restrictive que ses dépendances, sans inventer une classification commune aux trois modules. Une ressource inexistante et une ressource interdite retournent le même refus générique.

Les listes vides n’accordent aucun droit. En dehors de `ONMT_DEMO=1`, le backend refuse les accès tant qu’aucun résolveur d’identité serveur n’est connecté. Les en-têtes navigateur tels que `X-Roles` ne sont pas utilisés comme authentification. La démo n’est pas une authentification sécurisée.

L’export utilise un template contrôlé avec échappement Jinja, JavaScript désactivé, CSP et blocage des requêtes réseau du document. Les SVG sont produits uniquement depuis les séries numériques. Les graphiques longs sont découpés en panneaux ; toutes les valeurs restent dans les tableaux. L’arabe et la darija utilisent RTL, les nombres et identifiants techniques restent LTR. Aucun logo ou modèle de charte officielle ONMT n’a été fourni.

Le journal local conserve date UTC, identité, opération, `request_id` et ressource pour import, création, modification, export et téléchargement. Il ne journalise pas tous les refus ni toutes les recherches. Il n’est pas immuable et ne satisfait pas à lui seul l’audit du CPS.

## Brancher de vrais embeddings et Ollama

### État constaté sur ce poste

Python 3.11.9, Node 22.12.0, npm 11.6.0. Backend testé : FastAPI 0.162.0, Pydantic 2.14.2, ChromaDB 1.5.9, pdfplumber 0.11.10, Jinja2 3.1.6, Playwright 1.64.1, pytest 9.2.0. Versions npm exactes dans le lockfile.

Sentence Transformers 6.2.0, Transformers 5.22.1 et PyTorch 2.15.0 ont été installés dans `.venv`. `pip check` passe, mais **l’import de PyTorch échoue avec `WinError 126` sur `torch/lib/shm.dll` ou une dépendance**. L’échec persiste hors bac à sable. `vcruntime140_1.dll` n’a pas été trouvé dans System32 : un runtime MSVC manquant/incomplet est une piste, sans diagnostic définitif. Aucun runtime système n’a été installé automatiquement.

Pour débloquer : réparer/installer le runtime x64 depuis [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170), rouvrir PowerShell et vérifier :

```powershell
.\.venv\Scripts\python.exe -c "import torch; import sentence_transformers; print(torch.__version__)"
```

Si l’import échoue encore, choisir une distribution PyTorch adaptée au poste avec le [sélecteur officiel PyTorch](https://pytorch.org/get-started/locally/), dans `.venv`, puis vérifier la compatibilité indiquée par [Sentence Transformers](https://www.sbert.net/docs/installation.html). Le succès de `pip install` ne valide pas les DLL d’exécution.

Préparer ensuite un modèle local autorisé, par exemple E5 multilingue, sous `local_data/models/`. Le téléchargement d’un modèle est une opération distincte et explicite ; aucun téléchargement n’est déclenché par une recherche ou un import de document. Le modèle est chargé avec `local_files_only=True`, `trust_remote_code=False`, préfixes `query:` et `passage:` et vecteurs normalisés. Voir [l’API SentenceTransformer](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html).

```powershell
$env:ONMT_DEMO = '1'  # Conserve les analyses synthétiques, même avec de vrais embeddings.
$env:ONMT_DEMO_EMBEDDINGS = '0'
$env:ONMT_EMBEDDING_MODEL = "$PWD\local_data\models\multilingual-e5-small"
$env:ONMT_EMBEDDING_REVISION = 'indiquer-la-revision-exacte-du-modele'
# Redémarrer le backend, puis reconstruire les vecteurs des documents autorisés :
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/documents/reindex
```

Changer le modèle ou ses fichiers exige de changer la révision et de réindexer. Les collections Chroma sont séparées par modèle/révision ; une ancienne collection n’est jamais interrogée avec les nouveaux vecteurs. Un passage dépassant la limite du tokenizer est refusé explicitement, plutôt que tronqué silencieusement. La démo lexicale (`ONMT_DEMO_EMBEDDINGS=1`) est interdite hors mode démo.

Ollama n’était pas détecté dans `PATH`, et aucun modèle Ollama n’a été exécuté. Le client Python installé ne fournit pas le service. Installer le [service Windows Ollama](https://ollama.com/download/windows), choisir et télécharger explicitement un modèle local compatible, puis lancer le service avec les fonctions cloud désactivées. Les téléchargements et l’inférence ne sont pas la même opération.

```powershell
# Dans le terminal du service, après avoir quitté toute ancienne instance Ollama :
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_MODELS = "$PWD\local_data\models\ollama"
ollama serve
# Dans un autre terminal, après acquisition explicite du modèle local choisi :
ollama list
$env:ONMT_OLLAMA_MODEL = 'qwen3:4b'
# Redémarrer le backend dans ce terminal pour prendre cette configuration.
```

`qwen3:4b` est le candidat du guide, pas une qualité ou une performance validée ici. Le code ne lance ni `pull`, ni API payante, ni modèle cloud. Il refuse les noms cloud et contrôle `/api/show` avant de transmettre les extraits : présence d’informations de modèle local GGUF, absence de `remote_host` et `remote_model`. Il n’appelle que `127.0.0.1:11434`, sans proxy système, et demande le déchargement après la requête. Le service local reste un composant de confiance à administrer. La [FAQ Ollama](https://docs.ollama.com/faq) décrit la désactivation du cloud ; les sorties structurées suivent la [documentation officielle](https://docs.ollama.com/capabilities/structured-outputs).

## Interfaces pour Hayat et Doha

Doha doit fournir un objet conforme à `AnalysisProvider` :

```python
def get_analysis(analysis_id: str, access_context: AccessContext) -> AnalysisResult:
    # Vérifier les droits métier, y compris tous les périmètres des sources.
    # Retourner le résultat typé ou lever AppError ; ne jamais créer une fixture en secours.
    ...
```

Le contrôle d’autorisation appartient aussi au fournisseur, car `AnalysisResult` v0.1 ne contient ni politique d’accès, ni classification. Le fournisseur doit rester disponible pour réautoriser la lecture des rapports historiques. Le module Salma garde ses instantanés pour la fidélité des versions ; il n’utilise pas le nouveau chiffre du fournisseur pour changer rétroactivement une ancienne version.

Hayat construit `AccessContext` depuis une session authentifiée, jamais depuis le corps JSON. Le point de montage est :

```python
app = create_app(
    settings=Settings(demo=False, demo_embeddings=False),
    provider=doha_provider,
    access_resolver=resolve_authenticated_session,  # Request -> AccessContext, synchrone
)
```

Les fonctions internes sont exposées sur `app.state.reports` :

```python
create_report(request: ReportRequest, access_context) -> ReportResult
get_report(report_id, access_context, version=None) -> ReportResult
revise_report(request: ReportRevisionRequest, access_context) -> ReportResult
export_pdf(report_id, access_context, exporter, version=None) -> ReportResult
download_pdf(report_id, access_context, version=None) -> bytes
# Recherche documentaire directe, sans analyse obligatoire :
app.state.retriever.search_evidence(question, access_context, limit=5)
```

Les identités de démonstration sont confinées à `demo_access()` et au branchement explicite de démo. Les fournisseurs réels n’ont aucune dépendance à ces fixtures.

| Route | Usage |
| --- | --- |
| `POST /api/reports` | Génération synchrone, `ReportRequest` → `ReportResult`. |
| `GET /api/reports` | Rapports courants autorisés. |
| `GET /api/reports/{id}?version=N` | Version autorisée ; version courante par défaut. |
| `PATCH /api/reports/{id}/sections/{section_id}` | `ReportRevisionRequest`, chemin/corps cohérents, contrôle de `base_version`. |
| `POST /api/reports/{id}/export?version=N` | Génération ou réutilisation du PDF d’une version. |
| `GET /api/reports/{id}/pdf?version=N` | Téléchargement protégé. |
| `GET /api/reports/config` | Configuration visible à un utilisateur autorisé. |
| `POST /api/documents` | Multipart `file`, `metadata` JSON, `document_id` facultatif pour remplacement. |
| `GET /api/documents` | Métadonnées des documents courants autorisés. |
| `POST /api/documents/search` | `{question, limit}` → preuves référencées et avertissements. |
| `POST /api/documents/reindex` | Réencoder les documents courants dont le compte est propriétaire et autorisé. |
| `GET /api/documents/passages/{chunk_id}` | Retrouver le passage exact et sa page. |
| `GET /api/documents/{id}/pdf?version=N` | Original PDF après contrôles de droits historiques et courants. |

Échecs : `invalid_request` 422, `forbidden` 401 sans identité / 403 accès refusé ou ressource masquée, `missing_data` 404/422/503 selon le composant absent, `version_conflict` 409, `tool_failed` 500/503. Les erreurs applicatives respectent `ErrorResponse`. Un fournisseur réel doit respecter les mêmes règles de non-divulgation.

## Vérifications et résultats

Tests exécutés sur Windows avec le vrai moteur SQLite, ChromaDB, Chromium et pdfplumber ; les analyses de Doha sont des fixtures synthétiques. Le détail final se trouve dans [salma-test-results.md](salma-test-results.md).

```powershell
Set-Location C:\Users\OWNEER\onmt-ai
.\.venv\Scripts\python.exe -m pytest -q
Push-Location frontend
npm run build
npm test
npm audit
Pop-Location
# Vrais serveurs locaux et Chromium, sans modèles IA :
$env:ONMT_TEST_BROWSER = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_browser.py -q
Remove-Item Env:ONMT_TEST_BROWSER
# Après réparation des DLL et préparation d’un modèle local seulement :
$env:ONMT_TEST_REAL_MODELS = '1'
.\.venv\Scripts\python.exe -m pytest -m models -q
Remove-Item Env:ONMT_TEST_REAL_MODELS
```

Les tests d’interface Vitest utilisent une API simulée et le test Ollama un transport HTTP simulé ; ils ne prouvent pas une exécution de modèle. Le test navigateur démarre de vrais serveurs temporaires sur des ports libres et les arrête ensuite. Il conserve uniquement des artefacts synthétiques dans `local_data/test-artifacts/`.

Le test réel de Sentence Transformers est ignoré par défaut et n’a pas été validé sur ce poste. L’intégration avec les modules réels de Hayat et Doha n’est pas validée. La présence de chaînes arabes et des aperçus visuels lisibles ne constitue pas une évaluation linguistique complète de l’arabe ou de la darija.

## Limites et couverture CPS restante

| Besoin | Couverture actuelle et reste à faire |
| --- | --- |
| Préparation documentaire / RAG | Parcours local implémenté ; OCR, extraction des tableaux complexes, corpus ONMT autorisé et évaluation sémantique multilingue restent à réaliser. Vrais embeddings bloqués par les DLL du poste. |
| Rapports, CPS p. 14, exigences 17–18 | Sections et traçabilité opérationnelles. La prose économique libre, diagnostic sur cinq ans, benchmark multi-pays et recommandations stratégiques expertes demandent données réelles et validation métier. |
| Audiences, exigence 19 | Trois introductions adaptées et cinq langues de gabarits ; profondeur professionnelle, format OMT et qualité linguistique à évaluer. |
| Itération, exigence 20 | Versions, dépendances, cinq révisions de style testées. Ajout d’un marché/KPI, traduction d’une section et mélange de langues à préciser dans le contrat puis implémenter. |
| PDF, exigence 21 | PDF avec tableaux, graphiques statiques, sources et RTL. Charte officielle, deck 25 slides, pagination à 12/15 pages et graphiques avancés restent à réaliser. |
| Droits, exigences 23–24 | Contrôles applicatifs testables et réautorisation des dépendances. Authentification réelle, classification automatique commune, partage fin, chiffrement et migration PostgreSQL restent à intégrer. |
| Audit, exigence 25 | Journal local partiel ; journal exhaustif immuable, conservation et validation DSI hors capacité démontrée. |
| Refus, exigence 26 | Absences, références invalides et accès refusés testés ; aucune garantie générale d’absence d’hallucinations. |
| POC, CPS p. 19–20 | Parcours synthétique interface → API → rapport → révision → PDF validé. Parcours chat réel, trois domaines QVD, ROI, China Ready, connectivité, alertes et scénario POC complet non validés. |
| Performance et autres modules | Aucun SLA, charge 50 utilisateurs, inférence réelle, QVD ou prévision réelle revendiqués. Fonctions de Hayat/Doha et infrastructure/déploiement restent dans leurs périmètres respectifs. |

Le stockage sans chiffrement et le mode démo sont destinés aux données synthétiques de développement. Aucune conformité d’hébergement souverain ni juridique n’est déduite du fonctionnement local.

## Contrats : propositions séparées, à discuter avec l’équipe

Les champs de `docs/contracts.md` n’ont pas été modifiés. Les structures documentaires, `styles`, `section_versions`, instantanés et politiques sont internes au module. Les routes d’import/export et l’enveloppe de recherche documentaire sont des ajouts propres à Salma.

Pour une prochaine version commune :

1. Ajouter une politique et une classification de ressource résolues côté serveur pour les analyses, documents et rapports. Impact : accord de Doha/Hayat, migration des données et nouveaux tests d’autorisation.
2. Définir `ReportRevisionRequest` avec opérations typées pour changer les `analysis_ids`, la langue ou le périmètre, et les règles de dépendance/translations par section. Impact : nouveaux champs explicites, types React, exemples et tests ; aucun recalcul dans Salma.
3. Définir un `ReportDocument` interne/partagé pour langue, audience, date des données, formule, preuves et graphiques structurés par section. `ReportResult` v0.1 ne transporte actuellement que des chaînes de contenu et références.
4. Si des travaux durables deviennent nécessaires : contrat `Job`, queue persistante, reprise, annulation et autorisation. Un état `pending` sans traitement durable ne suffit pas.
5. Fixer une politique de rétention, de partage et le stockage PostgreSQL avec l’équipe. SQLite est une décision réversible pour débloquer le prototype local.

Ces propositions ne sont pas des modifications approuvées du contrat commun.

## Présenter et publier le travail

Pour la présentation : montrer d’abord les deux analyses fictives et leurs unités, générer le rapport, suivre une référence, modifier une section, consulter une ancienne version et télécharger le PDF. Montrer ensuite un document interdit et le refus d’accès dans les tests. Expliquer séparément le modèle d’embeddings, le moteur de calcul de Doha et la rédaction contrôlée.

Avant publication, relire votre modification préexistante de `requirements.txt` et décider de l’inclure ou de la garder séparée. Les commandes suivantes ajoutent uniquement les fichiers du module ; aucune commande n’est exécutée automatiquement :

```powershell
git branch --show-current
git diff --check
git status --short
git diff -- backend/requirements.txt
git add README.md docs/salma-reporting.md docs/salma-test-results.md pytest.ini
git add backend/app/core/config.py backend/app/core/errors.py backend/app/core/llm_client.py backend/app/core/security.py backend/app/main.py
git add backend/app/schemas backend/app/reports backend/tests
git add backend/requirements-reporting.txt backend/requirements-reporting-models.txt backend/requirements-reporting-tested.lock.txt
git add examples/contracts frontend
git diff --cached --stat
git diff --cached
git commit -m "feat(reports): add local sourced reporting and document retrieval"
git push -u origin salma/reporting-rag
```

Créer ensuite une Pull Request pour relecture par Hayat et Doha. Les modèles, index, originaux et rapports locaux doivent rester absents du diff Git.
