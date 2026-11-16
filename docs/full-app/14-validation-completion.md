# Validation de la complétion locale — 16 novembre 2026

Le chantier part de `51fe630`, sur `feature/cps-completion`, avec un état initial propre. Les résultats ci-dessous concernent cette branche et ses modifications locales. Aucun push, fusion, déploiement, Docker ou CI/CD n'a été réalisé. Les [résultats antérieurs](09-resultats.md), dont 111 tests au 14 novembre et 188,84 secondes pour l'essai du 9 novembre, restent historiques.

## Environnement et corpus

Windows 10 Pro 64 bits, Python 3.11.9, Intel Core i7-7600U (deux cœurs/quatre threads), 16 Go de RAM. Inférence CPU avec Qwen2.5 3B GGUF Q4_K_M, alias `onmt-qwen25:3b`, Ollama local 0.40.15, contexte 4 096 et sortie bornée à 512 tokens par appel. Un seul modèle et une inférence à la fois. Les poids sont locaux ; aucun entraînement/fine-tuning n'est effectué.

Versions principales : PyQvd 2.4.0, LangGraph 1.2.20, Torch CPU 2.15.0, Transformers 5.22.1, Sentence Transformers 6.2.0, Chroma 1.5.9, Playwright 1.64.1, Vite 6.4.5. E5 multilingue local, 384 dimensions, révision `614241f622f53c4eeff9890bdc4f31cfecc418b3`. Tesseract local avec français/anglais/arabe ; Chromium local pour les PDF.

Les trois QVD de référence sont inchangés : 2 100 lignes chacun, 6 300 au total. Les quatre compléments ajoutent 5 460 lignes, soit 11 760 lignes physiques. Les deux vues logiques de l'extension ne doublent pas ses lignes. Les [règles, relations, unités et scénarios](15-corpus-complementaire.md) sont versionnés ; les attendus des calculs sont indépendants du générateur et des fonctions testées.

Empreintes SHA-256 recontrôlées :

```text
commercial  3d209b7e7d9169100d56df8f3efb239fc83d3f65d7a172ac53ed6a0726ee6fb3
finance     d47c722143b93648cc5b35044f13d03f53ea907e4448ee7902e27cf589d0e0fc
performance 44317305d562e77c0afcabdb992cc467c6ece1a90a3488d508c6eb01b28c17d4
```

## Contrôles exécutés

Les catégories se recouvrent ; leurs compteurs ne doivent pas être additionnés. Une assertion dans le dépôt n'est pas, à elle seule, une preuve d'exécution.

| Contrôle | Résultat et portée |
| --- | --- |
| Backend ordinaire | Passe finale : **168 passed, 14 deselected**, 69,58 s. Les cas OCR/E5/Ollama/navigateur opt-in sont exclus ; certains interpréteurs et rédacteurs sont explicitement simulés. Les passes précédentes (165 puis 167) ne sont pas additionnées. |
| Narration/rapports ciblés | **58 passed**, 15,01 s : chiffres/citations, causes et variations interdites, emplacements vides refusés, anciens manifestes conservés, contrainte de script arabe et noms propres. Faux client IA, pas une preuve d'inférence. |
| Recherche contextualisée | **9 passed**, 7,59 s dans `test_documents.py` : documents privés et hors période exclus avant classement, méthode générale conservée, distance insuffisante et contradictions signalées. Index contrôlé pour ce nouveau cas ; pas de prétention sémantique E5 dans ce compteur. |
| React | **10 passed**, trois fichiers, 39,50 s. API/données simulées ; filtres, focus, valeurs négatives et états vides notamment. |
| Compilation TypeScript/Vite | Réussie, 39 modules ; dernière compilation Vite 3,18 s. |
| Navigateur intégré | **1 passed**, 22,50 s après les derniers ajustements : véritable API/QVD/Chromium, connexion, analyses, six comparateurs, douze régions, carte Agadir filtrée, clavier, sources, alertes et largeur mobile. Aucun appel LLM revendiqué pour ce test. |
| Note et présentation natives FR/AR | **2 passed**, 35,23 s : vrais QVD et Chromium, notes de 15 pages, présentations de 25, diagnostics inclus, marqueur synthétique, valeurs, références, droits et débordements. Rédaction par gabarits explicitement configurée pour isoler l'export. |
| Bibliothèque réelle | L'essai E5/OCR/Chroma et nouveau processus a réussi ; sept documents idempotents, import privé préservé et passages régionaux autorisés. Preuve locale `library-real.json`. La commande de préparation courante a également conservé six documents et indexé la version 2 du dictionnaire des 46 KPI. |
| Dépendances | `pip check` sans dépendance cassée ; installation principale en `--dry-run --no-index` satisfaite dans la venv. Syntaxes Python et PowerShell et `git diff --check` contrôlées. Cela ne constitue pas une installation neuve sur un deuxième PC. |
| Audit local | Vérification CLI valide sur 144 événements lors du contrôle, sans ancre externe. Les tests exercent modification/troncature/ancre et ajout légitime. Pas de garantie WORM. |
| Ollama réellement arrêté | **1 passed**, 3,77 s : erreur 503 explicite et bibliothèque de rapports inchangée, sans gabarit de secours. Preuve `cps-completion-results/ollama-offline.json` ; l'ancien relevé historique est préservé. |

La lecture visuelle d'échantillons français/arabe et mobile complète les assertions. Elle a révélé des libellés superposés dans la matrice Valeur–Volume du deck ; la correction utilise des repères numérotés avec légende séparée et a été réexportée/testée. Ce contrôle échantillonné n'est ni un audit graphique exhaustif ni une relecture linguistique humaine.

## Essais Ollama réellement exécutés

Les preuves locales se trouvent dans `local_data/cps-completion-results/`, exclu de Git. Les artefacts historiques dans d'autres dossiers n'ont pas été remplacés par ces résultats.

- Les essais initiaux ont échoué sur une prose inférant des visiteurs depuis les seules nuitées ; les contrôles ont refusé l'enregistrement. Un contexte plus court, des faits sélectionnés sur plusieurs KPI et une clôture limitée à vérification/limite corrigent cette génération sans supprimer les gardes.
- Le scénario à quatre KPI a réellement généré les six sections françaises et leurs documents OCR/E5, puis les PDF de 15 et 25 pages. L'essai combiné a ensuite échoué sur la révision arabe : **1 failed, 1 deselected**, 829,72 s. Preuve conservée `pipeline-real-ar-first-failure.json` ; ce n'est pas un succès global.
- L'essai arabe isolé a mis en évidence un mot chinois au milieu d'une phrase arabe. Le contrôle de script l'a refusé. Une contrainte de décodage arabe avec noms/sigles autorisés complète désormais ce contrôle. Le répertoire temporaire d'un diagnostic avait aussi été nettoyé par une autre session pytest ; la commande finale utilise un répertoire séparé dans `local_data/` pour préserver l'état durant les opérations longues.
- Après correction, le scénario complet a réussi : **1 passed, 1 deselected en 489,82 s**. `pipeline-real.json` indique `status: passed`, quatre KPI, six sections françaises, preuves texte/OCR, note de 15 pages, deck de 25 et révision arabe persistée. Son temps interne est 488,70 s ; la différence avec pytest est le coût du banc de tests. Aucun résultat simulé n'est substitué à un refus réel.
- Une relecture du brouillon a ensuite repéré un emplacement vide dans la section de limites. Le garde-fou le refuse désormais ; une véritable révision supplémentaire a réussi en **96,16 s**, avec synthèse arabe recalculée et nouveaux PDF de 15/25 pages : `final-report-real.json`, `note-real-revised.pdf`, `deck-real-revised.pdf`. Cela améliore le brouillon sans prétendre à une relecture linguistique humaine. Les anciennes versions de l'essai restent conservées.

Durées du scénario réussi, une exécution complète, modèles préparés et service déjà actif :

| Étape | Appels / temps |
| --- | --- |
| Lecture QVD | 35 appels, 1,1315 s cumulée ; 0,0101–0,1587 s par appel. |
| Contrôles/calculs | 16 appels, 0,8169 s cumulée ; inclut des lectures imbriquées. |
| Interprétation Qwen | 1 appel, 35,4916 s. |
| Recherche documentaire | 2 appels, 0,8856 s cumulée, E5 déjà chargé par l'ingestion. |
| Génération/révision | 7 sections, 422,7677 s cumulée, corrections bornées incluses ; 12,2672–119,1376 s par section. |
| PDF 15 pages | 1,8761 s. |
| Présentation 25 pages | 1,6203 s. |

Les traces sont imbriquées et n'incluent pas chaque coût de préparation comme une catégorie isolée ; leur somme n'est pas le temps global. Les mesures répétées de chargement des modèles sont distinctes ci-dessous.

## Évaluation linguistique ciblée

`examples/evaluation/multilingual-development.json` et `multilingual-heldout.json` séparent exemples de développement et 60 cas tenus à part : douze par langue, intentions, relances, ambiguïtés, révisions et diagnostics. Arabe et darija utilisent ici l'écriture arabe ; la translittération latine n'est pas évaluée.

Le jeu tenu à part n'a pas été exécuté intégralement. Une campagne réelle initiale corrigée d'un problème d'encodage a donné **10/15 intentions correctes**. Une première correction des relances a donné **5/10**. Après correction de l'ancrage des relances courtes, **10/10 relances** ont réussi : `languages-real-corrected-followups.json`. Les fichiers avant correction sont conservés ; les essais dont l'Unicode avait été corrompu sont identifiés comme invalides et exclus du résultat linguistique.

Ces derniers dix appels vont de 12,35 à 209,19 s ; certains ont partagé la file Ollama avec un autre essai. Ils ne démontrent pas une latence isolée ni un SLA. Les mêmes cas rejoués après correction ne sont plus une évaluation aveugle indépendante. La qualité rédactionnelle arabe/darija, les formulations libres et les révisions complètes dans les cinq langues restent à relire et élargir. L'interface et les exports les marquent comme brouillons à relire.

## Mesures des outils natifs

`scripts/measure-local.py --repetitions 3`, preuve `performance-native.json`, a produit :

| Répétition / cache de décodage | Découverte des sources | Calcul croisé Finance/Commercial | Benchmark six destinations × treize KPI |
| --- | --- | --- | --- |
| 1, première lecture du processus | 1,2683 s | 0,0673 s | 0,0761 s |
| 2, chaud | 0,9097 s | 0,0493 s | 0,0493 s |
| 3, chaud | 0,6659 s | 0,0459 s | 0,0382 s |

Le cache disque Windows n'est pas vidé : « première lecture » désigne le cache Python de décodage, pas un démarrage matériel à froid. La découverte inclut la lecture/validation ; le calcul et les traces de la chaîne réelle détaillent aussi `lecture_qvd`, `calcul_controles`, `interpretation`, `recherche_documentaire`, `generation`, `export_pdf` et `export_presentation`. Certaines mesures sont imbriquées ; ne pas additionner toutes les lignes de trace.

Le calcul international seul respecte 10 secondes sur ce petit corpus et ce poste. Les appels IA CPU et la note complète ne démontrent pas les délais CPS, notamment la note sous une minute. Les essais fonctionnels longs ont partagé le PC avec des régressions : leurs durées ne sont pas des benchmarks isolés. Aucune preuve de charge à 50 utilisateurs n'est fournie.

`scripts/measure-models.py` a ensuite mesuré trois répétitions réelles, sans autre client d'inférence :

| Modèle / opération | Premier appel avec chargement | Répétition chaude 2 | Répétition chaude 3 |
| --- | --- | --- | --- |
| E5, encodage d'une requête de 384 dimensions | 20,0854 s | 0,0214 s | 0,0225 s |
| Qwen, interprétation de la même question avec catalogue autorisé | 144,9560 s | 23,9028 s | 25,1302 s |

Les trois intentions ont été contrôlées contre les dates, territoire et KPI attendus. Qwen a été explicitement déchargé avant le premier appel ; celui-ci comprend 8,24 s de chargement des poids, 109,28 s de traitement du prompt et 26,72 s de génération côté moteur. Les appels chauds réutilisent notamment le préfixe du prompt. Le cache disque Windows n'est pas vidé. E5 inclut ses imports et son premier chargement, puis encode la même requête. Ce sont des mesures de performance ciblées, sans classement linguistique général ni garantie de recherche complète à ce débit. Preuve : `performance-models-real.json`.

## Installation, suppressions et commandes

`backend/requirements.txt` est l'unique entrée des dépendances directes. `requirements-tested.lock.txt` relève 136 versions nécessaires avec transitives dans la venv Windows, sans outils/poids externes. Les listes `requirements-full.txt`, `requirements-full-tested.lock.txt`, `requirements-reporting.txt`, `requirements-reporting-models.txt` et `requirements-reporting-tested.lock.txt` ont été supprimées après mise à jour des références.

Le SDK Python Ollama, `pytesseract` et `pytest-asyncio` n'avaient pas d'usage exécuté et ont été retirés de la déclaration/venv ; le service Ollama, Qwen et l'OCR Tesseract restent utilisés. Le premier est appelé via HTTPX, le second via subprocess. PostgreSQL/psycopg/SQLAlchemy/Alembic et statsmodels ne sont pas nécessaires à cette architecture ; NumPy et scikit-learn restent nécessaires indirectement aux modèles. L'architecture de stockage et ses limites sont [documentées](../architecture.md).

Préparation unique : `scripts/setup-local.ps1 -DownloadModelsAndTools`, import du Modelfile puis préparation explicite de la bibliothèque. Démarrages suivants : **trois terminaux**, Ollama, API et Vite, selon le [README](../../README.md). Les jobs et la surveillance restent dans l'API.

Commandes de validation depuis la racine :

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m 'not models and not local_ai and not full_models and not browser'
$env:ONMT_TEST_COMPLETION_REAL = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_cps_real.py -q --basetemp=local_data/cps-completion-results/pytest-real
$env:ONMT_TEST_PRESENTATION = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_presentations.py -q
$env:ONMT_TEST_FULL_BROWSER = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_full_browser.py -q
Remove-Item Env:ONMT_TEST_COMPLETION_REAL,Env:ONMT_TEST_PRESENTATION,Env:ONMT_TEST_FULL_BROWSER
Push-Location frontend
npm test
npm run build
Pop-Location
```

Ne pas lancer plusieurs clients d'inférence ensemble pour mesurer leur latence. Les serveurs locaux doivent être actifs pour le test navigateur. Les données, PDF, réponses de test, vecteurs, états et poids restent sous `local_data/` ignoré ; le [guide des fichiers](13-fichiers-et-pipeline.md) explique les modifications versionnées et le pipeline complet.

## Écarts maintenus

Voir la [matrice finale](01-couverture-cps.md) et le [travail restant](10-perimetre-pedagogique.md) : relecture humaine et évaluation linguistique élargie, 50+ tours entièrement interprétés par Ollama, prévision économique validée, voix/streaming/routage multi-modèles, accessibilité/charge exhaustives, SSO/chiffrement/WORM, SLA et exploitation industrielle. L'accord sur les données synthétiques ne supprime pas ces exigences.

## Commits locaux

- `fcb99de` — catalogue étendu, diagnostics et données complémentaires.
- `22eedd6` — spécialistes, bibliothèque persistante, tâches, audit et surveillance.
- `ebde72b` — scores, contrôles des KPI et rédaction bornée compatible avec les anciens manifestes.
- `aef281c` — interface, graphiques, diagnostics et progression des tâches.
- `ae148e0` — installation unifiée et corpus documentaire/linguistique versionnés.
- `3915821` — décodage arabe, absence d'emplacements vides, légendes PDF et preuves des essais réels.

Les commits de stabilisation, installation et documentation complètent cette liste dans `git log --oneline 51fe630..HEAD`. Aucun changement n'est poussé ou fusionné.

Les trois serveurs lancés pour la vérification sont arrêtés à la fin des essais. Leur PID et leur commande ont été vérifiés avant arrêt. Pour utiliser l'application, relancer les trois terminaux du README.
