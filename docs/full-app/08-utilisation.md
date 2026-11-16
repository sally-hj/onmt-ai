# Démarrer, démontrer et modifier le projet

Toutes les commandes sont PowerShell depuis la racine du dépôt. Vérifier que le port 8000 est libre avant de lancer l'application complète. Un terminal occupé par un serveur doit rester ouvert.

Le corpus synthétique est la référence définitive du rendu. Aucune commande d'import de données ONMT ni réception d'un QVD réel n'est nécessaire pour finaliser ce périmètre. Les traitements locaux demeurent réels.

## Préparation

Sur un nouveau poste Windows avec Python 3.11 et Node.js, la préparation s'effectue une seule fois :

```powershell
cd C:\Users\OWNEER\onmt-ai
.\scripts\setup-local.ps1 -DownloadModelsAndTools
```

Le script installe `backend/requirements.txt`, Chromium et les paquets npm, prépare les outils locaux et préserve les trois QVD de référence s'ils existent déjà. Il refuse une référence partiellement présente. Les téléchargements initiaux nécessitent Internet ; l'application fonctionne ensuite avec les fichiers locaux. Le relevé `requirements-tested.lock.txt` décrit les dépendances transitives vérifiées. L'import du modèle dans Ollama puis la bibliothèque initiale sont détaillés dans le [README](../../README.md). Pour les démarrages suivants, utiliser directement les trois terminaux ci-dessous.

## Trois terminaux

Terminal 1 :

```powershell
cd C:\Users\OWNEER\onmt-ai
.\scripts\start-local-ollama.ps1
```

Terminal 2 — **script de l'application complète**, avec les analyses calculées depuis QVD :

```powershell
cd C:\Users\OWNEER\onmt-ai
.\scripts\start-full-app.ps1
```

Terminal 3 :

```powershell
cd C:\Users\OWNEER\onmt-ai\frontend
npm run dev
```

Ouvrir `http://127.0.0.1:5173`. Documentation API : `http://127.0.0.1:8000/docs`. Les appels API protégés nécessitent d'abord une connexion ; Swagger ne contourne pas les droits.

Comptes de développement sur corpus fictif :

| Identifiant | Mot de passe initial | Périmètre |
| --- | --- | --- |
| `direction` | `OnmtLocal!2026` | Les trois domaines et six destinations. |
| `regional` | `OnmtLocal!2026` | Commercial/Performance, Agadir/Marrakech, pas Finance. |

Pour un nouvel état local, `ONMT_LOCAL_PASSWORD` peut définir un autre mot de passe avant le premier démarrage. Les comptes existants ne sont pas écrasés par un redémarrage. Ce mécanisme de développement ne remplace pas la gestion de comptes d'une installation réelle.

`Ctrl+C` arrête chaque serveur lancé au premier plan. Se déconnecter supprime la session ; cela n'efface pas les rapports. Aucun Docker, déploiement ou service cloud n'est ajouté.

Si PowerShell refuse l'exécution des scripts, les lancer dans un processus temporaire :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-full-app.ps1
```

Cette commande n'enregistre pas une politique globale. Le même préfixe peut servir pour `start-local-ollama.ps1`.

## Démonstration guidée

1. Se connecter avec `direction`.
2. Demander : « Compare les nuitées à Agadir en février 2025 et février 2024. » Vérifier 80 000, 100 000 et −20 %, puis ouvrir les sources et la formule.
3. Relancer : « Et pour Marrakech ? » Vérifier 165 000, 150 000 et +10 %.

Une comparaison territoriale directe est aussi possible : « Compare les nuitées à Agadir et Marrakech en février 2025. » Le chat affiche les deux résultats ; le cas a été testé réellement avec le modèle et les QVD. Une comparaison par marché utilise le même moteur avec « par marché ».
4. Dans Documents, importer un PDF autorisé, donner son titre et sa langue. Pour montrer l'OCR, utiliser un vrai PDF scanné. Les fichiers fictifs créés lors des tests restent sous `local_data/full-app-results/`.
5. Rechercher une définition en la reformulant, puis vérifier document, page et version du passage. Les extractions OCR doivent être relues.
6. Revenir au chat : « Prépare un rapport pour la direction. » La génération sur CPU peut prendre plusieurs minutes ; un échec doit rester visible.
7. Demander : « Traduis la synthèse en arabe. » Vérifier la nouvelle version et faire relire la langue.
8. Ouvrir Rapports, prévisualiser le PDF et télécharger la version choisie.
9. Demander un nouveau calcul dans le rapport, par exemple « Mets à jour le rapport avec le budget pour la même destination et les mêmes périodes. » Le modèle doit sélectionner `update_report` et `budget`. Vérifier les nouvelles sources Finance et la version ; une interprétation ambiguë doit être clarifiée.
10. Ouvrir Alertes : le démarrage normal vérifie périodiquement les règles, avec dernière réussite et erreurs persistantes. L'actualisation manuelle reste possible. `ONMT_MONITOR_INTERVAL=0` désactive cette boucle ; elle s'arrête avec le backend.
11. Se déconnecter puis utiliser `regional`. Les ressources privées de `direction`, Finance et les territoires non autorisés doivent être refusés.

Le scénario de recalcul et les conversations de 60 tours sont testés avec un interpréteur simulé ; les essais réels sont séparés dans le [bilan courant](14-validation-completion.md). Les formulations libres ne sont pas toutes garanties. L'espace « Diagnostics & cartes » propose également BCG internationale/régionale, Valeur–Volume, Butler, carte et scénarios. Les rapports peuvent exporter une présentation PDF de 25 diapositives.

## Modifier les sources et les indicateurs

La [documentation des données](03-donnees.md) décrit une extension **facultative** vers d'autres QVD. Si elle est choisie ultérieurement, adapter `ONMT_QVD_ROOT`, `ONMT_SOURCES_CONFIG`, les unités, le grain et les attendus indépendants. Ce changement n'est pas une condition du rendu ; un autre schéma ne se réduit pas à remplacer un nom de fichier.

Le [guide analytique](04-analyses.md) décrit l'ajout d'un indicateur. Les nouvelles formules doivent être testées dans le code, jamais exécutées depuis du texte libre envoyé par le modèle.

## Tests

```powershell
cd C:\Users\OWNEER\onmt-ai
# Noyau et régressions ; aucun modèle IA requis pour ces cas.
.\.venv\Scripts\python.exe -m pytest -q -m 'not models and not local_ai and not full_models and not browser'

# Audit du corpus définitif : natif, reproductible, cohérent et calculs sur oracle manuel.
.\.venv\Scripts\python.exe -m pytest backend\tests\test_synthetic_reference.py -q

# OCR et recherche réels, sans le long scénario de rapport Salma.
$env:ONMT_TEST_LOCAL_AI = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_local_models.py -q -k 'not pipeline'
Remove-Item Env:ONMT_TEST_LOCAL_AI

# Parcours complet QVD, chat IA, document/OCR, rapport et PDF réels.
$env:ONMT_TEST_FULL_REAL = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_full_models.py -q -s
Remove-Item Env:ONMT_TEST_FULL_REAL

# Interface complète : API et Vite déjà démarrés sur les ports ci-dessus.
$env:ONMT_TEST_FULL_BROWSER = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_full_browser.py -q
Remove-Item Env:ONMT_TEST_FULL_BROWSER

# Erreur réelle sans Ollama : arrêter volontairement votre service avant ce test.
# Garder l'API complète active ; ne pas exécuter en parallèle avec les autres essais IA.
$env:ONMT_EXPECT_OLLAMA_OFFLINE = '1'
.\.venv\Scripts\python.exe -m pytest backend\tests\test_full_offline.py -q
Remove-Item Env:ONMT_EXPECT_OLLAMA_OFFLINE

Push-Location frontend
npm test
npm run build
Pop-Location
```

Le test navigateur de l'espace complet fait un vrai calcul QVD par API pour contrôler son affichage ; il ne revendique pas un appel LLM. Le scénario `test_full_models.py` fait les vrais appels au modèle. Les deux preuves se complètent.

## Dépannage

| Symptôme | Vérification utile |
| --- | --- |
| Écran de connexion avec backend introuvable | Démarrer le script complet, vérifier le port 8000 et le proxy Vite. Un backend Salma seul n'expose pas `/api/auth`. |
| Port déjà occupé | Arrêter avec Ctrl+C le serveur lancé dans votre autre terminal. Ne pas tuer un processus inconnu. |
| Ollama inaccessible | Démarrer `start-local-ollama.ps1`, puis consulter Sources & services. Aucun gabarit ne remplace automatiquement l'erreur. |
| Modèle absent | `local_data\tools\ollama\ollama.exe list` ; importer le Modelfile selon le guide local IA si nécessaire. |
| Sortie IA refusée / langue incorrecte | Reformuler avec un indicateur et des mois explicites ; consulter le code d'erreur. Ne pas désactiver les contrôles numériques pour forcer une réussite. |
| Source absente ou schéma incomplet | Régénérer les fichiers fictifs ou corriger la configuration ; consulter le catalogue. |
| Analyse périmée | Les QVD ou le mapping ont changé : recalculer. Les anciens chiffres ne doivent pas être présentés comme actuels. |
| Erreur DLL PyTorch | Utiliser `.venv\Scripts\python.exe`, les dépendances modèles et `core/runtime.py`. Ne pas copier arbitrairement des DLL dans Windows. |
| OCR absent | Vérifier Tesseract et `fra`, `eng`, `ara` ; la préparation est décrite dans le guide IA. |
| PDF indisponible | Installer Chromium via Playwright avec `PLAYWRIGHT_BROWSERS_PATH` pointant vers `local_data/browsers`. |
| Conflit de version | Recharger la conversation/ressource ; ne pas supprimer `base_version` pour écraser une modification concurrente. |

Les journaux locaux et les identifiants de requête aident à diagnostiquer. Les prompts et documents réels ne doivent pas être ajoutés aux traces synthétiques des tests.
