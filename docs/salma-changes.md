# Explication des changements : vrais modèles locaux et OCR

La partie déjà existante gérait les contrats, les droits, les rapports par gabarits et le PDF. Cette évolution ajoute les modèles réellement exécutés et l’OCR, sans remplacer les analyses de Doha ni l’authentification de Hayat.

Le parcours est : PDF → extraction directe ou OCR → passages référencés → vecteurs E5 → recherche autorisée → prose Ollama → injection et contrôle des faits → version SQLite → PDF.

| Fichier | Explication simple du changement |
| --- | --- |
| `backend/app/core/runtime.py` | Nouveau : prépare la recherche des DLL C++ installées dans la venv avant de charger PyTorch. Il ne copie rien dans Windows. |
| `backend/app/core/config.py` | Ajoute les choix de rédaction, le délai et le contexte du modèle, l’activation OCR, les chemins Tesseract et les langues. Le seuil de recherche E5 est configurable. |
| `backend/app/core/llm_client.py` | Ajoute un vrai appel de rédaction JSON au modèle local, vérifie son origine locale et gère modèle absent, service arrêté, erreur, délai et sortie tronquée. Garde quelques mesures d’exécution, jamais le raisonnement privé du modèle. L’ancien planificateur est conservé pour compatibilité. |
| `backend/app/main.py` | Branche `NarrativeWriter` lorsque la rédaction Ollama est demandée. Le mode gabarits reste un choix explicite ; une erreur IA ne l’active pas automatiquement. |
| `backend/app/reports/ocr.py` | Nouveau : rend une page en image avec PDFium puis appelle Tesseract local. Conserve le texte, un score moyen de reconnaissance et les avertissements de relecture. |
| `backend/app/reports/documents.py` | Ajoute l’origine `text` ou `ocr`, la confiance OCR et la signature du traitement. Les anciens documents restent lisibles grâce aux valeurs par défaut. |
| `backend/app/reports/ingestion.py` | Utilise l’OCR sur les pages qui le nécessitent, y compris dans les PDF mixtes. Préserve les pages et indique les extractions douteuses. Un changement de traitement peut créer une nouvelle version. |
| `backend/app/reports/retrieval.py` | Charge réellement Sentence Transformers sur CPU avec le runtime réparé. L’identité d’index inclut la révision des poids. Une preuve OCR est signalée au lecteur. Le filtrage des droits reste avant la recherche. |
| `backend/app/reports/narrative.py` | Nouveau : demande une prose courte au modèle par fait et document. Le serveur ajoute les valeurs exactes et les références ; les nombres libres, références ajoutées et certaines affirmations interdites provoquent un refus. Le manifeste conserve la provenance de la rédaction. |
| `backend/app/reports/revisions.py` | Nouveau : comprend les opérations de style, reformulation, public cible, langue et consigne éditoriale. Une demande de nouveau calcul est signalée comme devant passer par Doha/Hayat. |
| `backend/app/reports/generation.py` | Conserve les gabarits et ajoute leur adaptation par section, pour garder la lecture et l’édition des anciens rapports. |
| `backend/app/reports/service.py` | Coordonne la vraie rédaction, enregistre sa provenance et les paramètres de chaque section. Les modifications conservent le contrôle de version et les droits ; les sections indépendantes sont préservées. |
| `backend/app/reports/validation.py` | Vérifie la liste des sections demandées et distingue la vérification d’un gabarit de celle d’une prose générée avec son manifeste. Contrôle toujours les références et le marquage synthétique. |
| `backend/app/reports/router.py` | Expose à l’interface le mode réellement configuré et l’état d’activation OCR. Les champs des contrats de rapports ne changent pas. |
| `backend/app/reports/templates/report.html` | Applique la langue et le sens de lecture à chaque section : une synthèse arabe peut coexister avec des sections françaises. |
| `backend/app/reports/demo.py` | Fixe explicitement l’ancien parcours sans IA afin qu’il ne change pas de comportement selon les variables du terminal. |
| `backend/app/reports/demo_real.py` | Nouveau : fabrique un PDF mixte fictif puis lance OCR, E5, Ollama, révision facultative et export réel. Aucun document officiel ni chiffre réel n’est inventé. |
| `backend/requirements-reporting.txt` | Déclare explicitement PDFium, utilisé pour le rendu OCR. |
| `backend/requirements-reporting-models.txt` | Ajoute le runtime C++ Windows local. Les modèles eux-mêmes restent des téléchargements séparés des paquets Python. |
| `backend/requirements-reporting-tested.lock.txt` | Actualise le relevé des paquets réellement installés dans la venv. |
| `backend/tests/conftest.py` | Isole les tests ordinaires des variables d’environnement de l’utilisateur : ils restent clairement sans vrais modèles. |
| `backend/tests/local_fixtures.py` | Nouveau : construit de faux scans de texte, avec un rendu correct des caractères arabes avant rasterisation. |
| `backend/tests/test_narrative.py` | Nouveau : teste les contrôles sur chiffres/citations, la conservation des faits, les révisions, les erreurs du service et l’absence de repli silencieux. Ces appels IA sont simulés. |
| `backend/tests/test_local_models.py` | Nouveau : contient les essais réels OCR multilingue, E5 sur paraphrases et chaîne complète avec Ollama/PDF. L’activation est explicite. |
| `backend/tests/test_browser.py` | Fixe les modes gabarits et OCR désactivé du parcours navigateur existant pour ne pas le confondre avec un essai réel IA. |
| `pytest.ini` | Identifie la catégorie `local_ai`, séparée des tests rapides et des essais E5 seuls. |
| `frontend/src/features/reports/ReportsPage.tsx` | Affiche le mode de rédaction, les possibilités OCR et les nouvelles actions de modification. Signale l’origine OCR d’une preuve. |
| `frontend/src/features/reports/types.ts` | Décrit les nouveaux renseignements documentaires et de configuration côté TypeScript, sans changer les champs des rapports partagés. |
| `frontend/src/features/reports/ReportsPage.test.tsx` | Vérifie l’envoi d’une traduction ciblée et l’affichage des modes IA/OCR, avec une API simulée. |
| `scripts/prepare-local-ai.py` | Nouveau : prépare explicitement les outils et modèles locaux avec contrôle d’espace, versions de poids fixées et empreintes des distributions. Il n’envoie aucun document. |
| `scripts/start-local-ollama.ps1` | Nouveau : démarre Ollama sur localhost, sans cloud, avec un seul modèle et une inférence à la fois. Ne remplace pas un service déjà présent. |
| `scripts/start-reporting.ps1` | Nouveau : lance le backend avec de vrais modèles/OCR et des analyses synthétiques. Des options permettent de choisir explicitement l’ancien mode sans modèle. |
| `examples/reporting.env.example` | Nouveau : décrit les variables à définir sans contenir de secret. Il n’est pas chargé automatiquement. |
| `docs/salma-local-ai.md` | Nouveau guide d’installation, de lancement, d’intégration et de limites. |
| `docs/salma-local-ai-results.md` | Résultats datés et distinction entre vrais composants, données synthétiques et intégration réelle non validée. |
| `docs/salma-reporting.md` | Signale que le diagnostic initial du 4 novembre est historique et renvoie au nouveau guide. |
| `docs/salma-test-results.md` | Conserve les anciens résultats et renvoie vers le relevé des nouveaux essais. |
| `README.md` | Ajoute le lien vers le parcours de vrais modèles locaux et rappelle que les analyses réelles restent à connecter. |

`docs/contracts.md`, les exemples JSON communs, le fournisseur métier de Doha et le module conversationnel de Hayat ne sont pas remplacés. `reports/storage.py` et le moteur `reports/export.py` existants restent utilisés pour la conservation et l’impression ; ils n’ont pas besoin d’un second stockage ni d’un second moteur PDF.

Pour comprendre le code, commencer par `main.py`, puis `service.py`, `narrative.py`, `ingestion.py`, `ocr.py` et `retrieval.py`. Les résultats d’essai, plutôt que la seule présence des fichiers, indiquent quelles capacités sont réellement démontrées.
