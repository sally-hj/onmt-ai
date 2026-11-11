# Salma — modèles locaux, OCR et révisions

Mise à jour du 9 novembre 2026 ; diagnostic commencé le 8 novembre. Ce guide complète et remplace les limites d’environnement du bilan initial du 4 novembre. Développement local uniquement ; aucun push, fusion, Docker ou déploiement ajouté.

## Diagnostic et choix

Branche contrôlée : `salma/reporting-rag`, dossier propre avant intervention. `AGENTS.md` et `docs/architecture.md` sont toujours vides. README, contrats, exemples et tests existants ont été relus. Les deux PDF fournis sont présents et lisibles localement : CPS de 24 pages, guide des tâches de 25 pages. Certaines extractions du CPS sont irrégulières. Les contrats du dépôt restent la référence commune.

Matériel constaté sous Windows 10 Pro : environ 16 Go de RAM, processeur Intel i7-7600U à 2 cœurs / 4 threads, Intel HD Graphics 620. Environ 4,2 Go de RAM étaient disponibles au diagnostic. C: présentait environ 43 Gio libres, sur une partition d’environ 238 Gio. Ces mesures remplacent les capacités supposées ; elles varient avec les autres applications.

| Composant | Choix et compromis |
| --- | --- |
| Rédaction | Qwen2.5 3B Instruct, fichier GGUF Q4_K_M officiel Qwen, importé sous `onmt-qwen25:3b`. 2 104 932 768 octets de poids. Modèle de développement sur CPU ; qualité et vitesse à distinguer de l’infrastructure lourde du CPS. |
| Embeddings | `intfloat/multilingual-e5-small`, Sentence Transformers sur CPU, 384 dimensions. Poids principaux d’environ 470 Mo. Préfixes `query:` et `passage:` ; modèle chargé hors ligne à l’exécution. |
| OCR | Tesseract 5.5.3 Windows, modèles `tessdata_fast` français, anglais et arabe, environ 6,6 Mo pour les trois langues. Gratuit, local et sans modèle de vision lourd. |
| Inférence | Ollama 0.40.15 autonome ; distribution téléchargée de 1,6 Go, seuls les fichiers CPU utiles sont extraits, environ 85 Mo. Une seule inférence à la fois, contexte 3072, deux threads CPU. |

Le téléchargement standard `ollama pull qwen3:1.7b` a échoué sur le serveur de fichiers du registre (connexions expirées). Un premier essai de Qwen3 1.7B Q8 a révélé trop de réponses refusées : chiffres inventés, variables non remplies et traduction tronquée. Le modèle préféré est devenu Qwen2.5 3B Instruct Q4. Ses poids sont téléchargés depuis le dépôt officiel Qwen sur Hugging Face puis importés localement. Les anciens poids sont conservés comme artefacts d’essai. Aucun modèle distant n’est appelé.

Sources techniques : [Qwen2.5 3B Instruct et ses poids GGUF](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF), [E5-small](https://huggingface.co/intfloat/multilingual-e5-small), [Ollama Windows](https://docs.ollama.com/windows), [Tesseract Windows](https://github.com/UB-Mannheim/tesseract/wiki). Le support multilingue annoncé par un modèle ne remplace pas une recette métier de la darija ou de la prose ministérielle.

## Réparation PyTorch dans la venv

Python 3.11.9 AMD64 64 bits ; torch 2.15.0 CPU, Transformers 5.22.1 et Sentence Transformers 6.2.0. L’erreur `WinError 126` sur `torch/lib/shm.dll` venait notamment de `VCRUNTIME140_1.dll`, dépendance directe identifiée par lecture du fichier PE et absente de System32.

Le paquet `msvc-runtime` a installé les DLL C++ dans `.venv/Scripts`. La venv Windows utilise le moteur Python de base : il faut aussi enregistrer ce dossier pour la recherche des DLL. `core/runtime.py` le fait avant l’import de torch et charge explicitement les bibliothèques présentes. Aucun fichier n’a été copié dans Windows ou une autre installation Python.

L’import torch/Sentence Transformers et le calcul réel d’un vecteur E5 ont réussi. Un `pip check` ne suffit pas à diagnostiquer les DLL : il ne vérifie que les dépendances déclarées des paquets.

## Installation reproductible PowerShell

Depuis la racine du dépôt :

```powershell
Set-Location C:\Users\OWNEER\onmt-ai
# Seulement si la venv n’existe pas :
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-reporting-models.txt
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\local_data\browsers"
.\.venv\Scripts\python.exe -m playwright install chromium
# Téléchargements explicites, sans document utilisateur et sans clé API :
.\.venv\Scripts\python.exe scripts\prepare-local-ai.py
Push-Location frontend
npm ci
Pop-Location
```

Le script vérifie une marge de 10 Gio, conserve les téléchargements sous `local_data/downloads`, vérifie les empreintes des distributions, extrait Ollama CPU et installe Tesseract dans un nouveau dossier local. L’installateur Tesseract peut enregistrer une entrée de désinstallation Windows ; il ne remplace aucune installation existante. Les trois modèles de langues OCR sont placés dans `local_data/tools/tesseract/tessdata`. Aucun OCR ne nécessite une clé API.

Les révisions des poids E5 et Qwen sont fixées dans le script et enregistrées avec les modèles. Les langues OCR proviennent du dépôt officiel et leur révision exacte est conservée dans `ONMT_REVISION.txt`. Une connexion Internet est nécessaire pour cette préparation explicite, pas pour l’inférence.

Terminal 1 — démarrer Ollama (laisser ouvert, Ctrl+C pour arrêter) :

```powershell
.\scripts\start-local-ollama.ps1
```

Terminal 2 — importer les poids déjà téléchargés, une fois :

```powershell
.\local_data\tools\ollama\ollama.exe create onmt-qwen25:3b -f local_data\models\qwen25-3b-gguf\Modelfile
.\local_data\tools\ollama\ollama.exe list
```

Le script de démarrage fixe `OLLAMA_NO_CLOUD=1`, le stockage des modèles dans le projet et l’écoute à `127.0.0.1:11434`. Il limite les modèles chargés et le parallélisme à un. Le service peut créer sa clé locale habituelle sous le profil Windows ; elle n’est jamais ajoutée au dépôt.

Terminal 2 — backend avec vrais modèles et OCR :

```powershell
.\scripts\start-reporting.ps1
```

Terminal 3 — interface :

```powershell
Set-Location C:\Users\OWNEER\onmt-ai\frontend
npm run dev
```

Ouvrir `http://127.0.0.1:5173`, API sur `http://127.0.0.1:8000/docs`. Le backend utilise ici une **identité et des analyses synthétiques**, mais de **vrais modèles IA locaux**. Le bandeau de démonstration ne signifie donc pas que le LLM est simulé.

Le fichier `examples/reporting.env.example` documente chaque variable sans secret ; il n’est pas chargé automatiquement. Le script PowerShell fournit une configuration directement utilisable.

Un mode sans IA reste disponible **uniquement par choix explicite**, affiché dans l’interface et marqué dans les avertissements :

```powershell
.\scripts\start-reporting.ps1 -Templates -DemoEmbeddings -DisableOCR
```

Il ne se déclenche jamais à la place d’une erreur Ollama. Fermer le service, supprimer un modèle ou retourner un JSON invalide provoque une erreur, sans rapport IA fictivement réussi.

## Documents, OCR et recherche

L’extraction directe pdfplumber reste prioritaire. Une page sans texte, ou une page contenant une image importante et très peu de texte, passe par OCR si ce mode est activé. Une page mixte contenant beaucoup de texte et une image textuelle secondaire peut nécessiter une relecture ou un traitement spécifique : la détection n’est pas exhaustive.

PDFium rend la page à 200 dpi, puis Tesseract est exécuté par processus local, sans shell, avec délai maximal. Les fichiers temporaires sont supprimés après l’appel. Les pages trop grandes sont refusées. Le texte, la page physique, la version, `extraction_method` et le score OCR moyen sont conservés par passage.

Toute preuve OCR impose une relecture. Les chiffres et tableaux reconnus ne deviennent jamais des KPI : seules les valeurs structurées de Doha alimentent les faits analytiques. Les scores OCR ne sont pas des probabilités de vérité. Écriture manuscrite, pages floues, colonnes, tableaux complexes et certaines mises en page arabes restent des limites à examiner.

Le découpage reste par page, sur des segments d’environ 600 caractères avec recouvrement et tentative de coupe sur un espace. La longueur est vérifiée avec le tokenizer E5. Les références pointent vers le passage exact, et les originaux PDF sont conservés dans SQLite.

Le choix d’un traitement OCR différent crée une nouvelle édition plutôt que de retourner silencieusement un ancien import textuel comme doublon. Le modèle d’embeddings et sa révision déterminent une collection Chroma séparée. Après changement, lancer :

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/documents/reindex
```

Le serveur filtre les versions autorisées avant la recherche, puis revérifie les passages retournés contre SQLite. Les résultats interdits ne participent pas au classement et ne parviennent pas au LLM.

Le seuil initial E5 a été ramené à `0.24` sur un petit jeu fictif : trois paraphrases positives et une question hors sujet. Il reste configurable par `ONMT_MAX_DISTANCE` et doit être recalibré sur le corpus réel. Ce petit jeu ne démontre pas la qualité générale du RAG.

## Vraie rédaction et contrôles

`reports/narrative.py` demande au modèle une prose courte par fait ou extrait, adaptée à la section, à la langue et au destinataire. Le modèle reçoit les rôles des mesures et les extraits documentaires autorisés ; les valeurs numériques sont remplacées par des emplacements serveur. Il n’a aucun outil de calcul, d’exécution ou d’accès à des sources supplémentaires.

Le JSON de sortie possède des champs obligatoires par preuve. Le serveur insère ensuite les chiffres, unités, périodes, filtres et citations exacts. Il refuse les références supplémentaires, les chiffres libres (y compris pleine largeur et exposants Unicode), les variables non remplies X/Y/Z, plusieurs nombres écrits en lettres, des attributions causales non démontrées et certaines contradictions de sens de variation. La prose arabe est contrôlée pour ne pas valider une traduction limitée au titre.

La rédaction utilise l’endpoint local `/api/generate` avec un cadrage ChatML Qwen explicite. Cela évite les erreurs de format `peg-native` observées sur les réponses complexes de `/api/chat` avec cette version du service. Les délimiteurs éventuels des extraits sont échappés dans le JSON utilisateur : ils ne peuvent pas ouvrir un nouveau rôle. Le client de rédaction est donc actuellement limité aux familles Qwen compatibles ChatML, et non à tout modèle Ollama arbitraire. Voir l’[API officielle de génération](https://docs.ollama.com/api/generate).

Les contrôles réduisent les inventions sur les éléments vérifiables ; ils ne prouvent pas que toute formulation libre est sémantiquement justifiée. La qualité rédactionnelle, la causalité implicite et les recommandations exigent toujours une relecture humaine. La présence d’une citation n’est pas une preuve suffisante d’une affirmation.

L'essai arabe a effectivement montré des erreurs de vocabulaire métier et des caractères étrangers dans un nom de ville, malgré des chiffres conservés. La traduction est une fonctionnalité de développement à relire, pas une version prête à publier. Voir le [bilan des essais](salma-local-ai-results.md) pour les limites observées.

Le modèle ne voit jamais un document comme instruction système. Les extraits, le titre et la consigne éditoriale restent dans le message de données. Les droits sont toujours décidés par Python. Une tentative d’injection peut influencer une prose, mais elle ne doit pas permettre d’ajouter un chiffre, une citation ou un accès non autorisé.

Une réponse mal formée ou non conforme peut être corrigée une fois par le modèle. Si elle reste invalide, aucune nouvelle version n’est enregistrée. Le délai Ollama et les réponses tronquées sont contrôlés. La génération reste synchrone ; l’écran attend la requête réelle, sans queue durable ni faux pourcentage d’avancement.

Le contexte est borné à huit faits et trois extraits par section. Les tableaux du PDF gardent les analyses complètes. Un modèle de développement n’est pas supposé traiter un corpus ou un historique illimité.

## Révisions et contrat commun

Les champs de `ReportRequest`, `ReportResult` et `ReportRevisionRequest` sont conservés. La sémantique du champ existant `instruction` est élargie explicitement, sans nouveau champ obligatoire :

| Instruction | Effet sur la section sélectionnée |
| --- | --- |
| `résumer`, `détailler` | Changer le niveau de détail. |
| `reformuler` | Nouvelle prose par le modèle sur les mêmes faits. |
| `adapter:direction`, `adapter:ministere`, `adapter:regional` | Adapter le destinataire. |
| `langue:fr`, `langue:ar`, `langue:ary`, `langue:en`, `langue:es` | Changer la langue. |
| `modifier:consigne éditoriale` | Reformulation ciblée, sans nouveau calcul ni nouvelle preuve. |

L’interface propose ces actions. La langue et le destinataire sont enregistrés **par section** ; traduire la synthèse ne traduit pas implicitement tout le rapport. Le PDF applique la direction RTL aux sections arabes et conserve les valeurs et identifiants numériques.

`base_version`, la transaction de sauvegarde et les règles de dépendance restent en vigueur. Les sections non concernées ne sont pas rédigées de nouveau par le LLM. Les anciens rapports à gabarits restent lisibles. Leurs révisions par modèle peuvent produire un rapport mixte ; l’historique de génération est conservé par section.

Une demande de nouveau calcul est signalée par `missing_data` avec une consigne de transmission à Doha via Hayat. Aucun module complet d’analyse ni mécanisme de dispatch conversationnel n’a été ajouté ici.

## Scénario reproductible sans données réelles

Après installation et démarrage d’Ollama :

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.reports.demo_real --sections summary --revise langue:ar
```

Le script fabrique un PDF mixte fictif, exécute extraction directe et OCR, calcule les embeddings E5, recherche les passages, rédige réellement avec Ollama, traduit la section sélectionnée puis exporte le PDF. Les analyses restent celles de `examples/contracts/`, avec `is_synthetic: true`.

Les fichiers sont sous `local_data/demo-real-ai/`. Pour davantage de sections, ajouter par exemple `--sections summary diagnostic comparison forecast recommendations limitations`. Sur ce CPU ancien, cela peut prendre plusieurs minutes ; aucun SLA CPS n’est revendiqué.

## Tests et interfaces d’équipe

```powershell
# Tests ordinaires, dont fournisseurs IA simulés :
.\.venv\Scripts\python.exe -m pytest -q
# Essais réels OCR, E5, Ollama, révisions et PDF :
$env:ONMT_TEST_LOCAL_AI = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_local_models.py -q
Remove-Item Env:ONMT_TEST_LOCAL_AI
# Essai E5 réel seul :
$env:ONMT_TEST_REAL_MODELS = '1'
.\.venv\Scripts\python.exe -m pytest -m models -q
Remove-Item Env:ONMT_TEST_REAL_MODELS
# Parcours navigateur existant, toujours identifié comme démo sans modèle :
$env:ONMT_TEST_BROWSER = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_browser.py -q
Remove-Item Env:ONMT_TEST_BROWSER
Push-Location frontend
npm run build
npm test
Pop-Location
```

Les résultats datés sont consignés dans `docs/salma-local-ai-results.md`. Les traces détaillées des essais réels ne concernent que le corpus synthétique et restent dans `local_data/real-ai-results`, hors Git. Le code applicatif ne journalise pas les prompts ou documents dans ces traces de test.

Les points d’intégration restent `AnalysisProvider.get_analysis(analysis_id, access_context)` pour Doha, et les méthodes de `ReportService` pour Hayat : création, lecture, révision, export et téléchargement. Hayat fournit un `AccessContext` issu d’une véritable identité serveur, via `create_app(access_resolver=..., provider=...)`. Aucun rôle choisi dans le navigateur ne devient une autorisation.

Restent à valider : analyses réelles et autorisations métier de Doha, parcours conversationnel de Hayat, classification commune, chiffrement, audit immuable, charge et performances, qualité du corpus réel et des recommandations, darija approfondie, PDF de charte officielle et deck de présentation. Les originaux, rapports, poids, index et clés restent hors Git.

Le modèle Qwen2.5 3B est fourni sous licence qwen-research ; ce choix est destiné au développement académique local. Il n’est pas présenté comme un modèle sous licence Apache ni comme une validation de la cible CPS.
