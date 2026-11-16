# Architecture locale

L'application fonctionne sur un poste Windows avec une API FastAPI à **un seul processus**,
un frontend React/Vite et un service Ollama. Les trois terminaux du README suffisent :
le scheduler et la file de tâches vivent dans l'API. Aucun service cloud, Docker ou CI/CD
n'est ajouté.

## Responsabilités

La conversation est persistante et versionnée. Qwen interprète la demande vers un
contrat structuré. Le serveur ancre les périodes et dimensions explicites, applique
les droits et orchestre les spécialistes LangGraph : territoire, marchés,
saisonnalité, budget/performance, recherche, restitution et vérification.

Les spécialistes utilisent des politiques et outils Python bornés. La saisonnalité
peut transmettre un pic au contrôle budgétaire ; celui-ci vérifie des périmètres de
même grain. Les résultats, outils et sources transmis sont tracés. Les nombres ne
sont pas calculés par le LLM et son raisonnement interne n'est pas publié.

Les demandes longues sont enregistrées dans une file SQLite, avec un worker, au
plus huit tâches actives/en attente, idempotence par utilisateur et étapes réelles.
L'annulation est coopérative entre étapes. Après redémarrage, une tâche interrompue
est signalée en échec ; elle n'est pas rejouée automatiquement au risque de créer
un rapport en double. Les ressources déjà créées restent consultables avec leurs droits.

## Stockage réellement utilisé

| Support | Contenu | Limite |
| --- | --- | --- |
| QVD sur disque | Tables Finance/Commercial/Performance et compléments synthétiques ; données de calcul natives. | Pas de copie des tables dans SQLite ni de conversion CSV. Le grain accepté reste mensuel/destination/marché. |
| `application.sqlite3` | Comptes et sessions hachées, analyses, contextes/messages, alertes, état de surveillance, tâches, définitions/versions de KPI et diagnostics privés. | Concurrence limitée au poste local ; pas une base distribuée pour cinquante utilisateurs. |
| `reporting.sqlite3` | Métadonnées et passages documentaires, politiques, originaux PDF en BLOB, rapports et versions, PDF et decks en BLOB, registre de bibliothèque, ancien audit. | Les originaux et exports ne sont pas de simples chemins de fichiers. Les anciennes versions sont conservées. |
| `audit.sqlite3` | Nouveaux événements UTC, acteur, requête, action, ressource, résultat, versions et chaîne SHA-256. | Détection d'altérations avec ancre fiable ; pas d'immutabilité face au contrôle total du stockage. L'ancien audit reste historique et non chaîné. |
| Chroma persistant | Vecteurs E5, textes indexés et identifiants de versions documentaires. | La collection dépend de l'identité/révision du modèle. Changer de modèle nécessite une réindexation. |
| Autres fichiers locaux | Poids E5/GGUF et Ollama, Tesseract/langues, Chromium, téléchargements, corpus source et artefacts de tests. | Les fichiers temporaires OCR sont nettoyés ; les gros fichiers générés restent exclus de Git. |

Le lecteur QVD garde un cache interne borné de tables décodées. Une empreinte du
fichier est vérifiée à chaque accès et avant/après lecture. Les filtres et droits sont
réappliqués à chaque demande, y compris sur un cache chaud. Les versions incorporent
le mapping et la nature synthétique. Un changement de mapping de configuration
demande un redémarrage ; un changement de contenu est détecté sans redémarrage.

Deux vues logiques peuvent sélectionner des champs distincts d'un même QVD : la
marge attribuée du complément est réservée à la vue Finance. Les définitions de KPI
personnalisés ne peuvent demander que les champs numériques et unités déclarés.
Les piliers normalisés, non additifs, ne peuvent pas être additionnés via cette DSL.

## Documents et génération

Un import autorisé extrait le texte ; les pages scannées passent par PDFium puis
Tesseract. Les passages conservent page, version, langue, origine et confiance OCR.
Les vecteurs sont calculés par E5 et conservés dans Chroma. L'indexation ne modifie
pas les poids d'E5 ou de Qwen : ce n'est pas un entraînement.

La recherche filtre les documents/versions autorisés **avant** leur classement. Les
documents privés restent privés. Seule la commande de préparation publie sa
bibliothèque fictive réservée, partagée entre les comptes autorisés du projet.
La recherche de rapport combine question/titre, indicateurs, filtres, périodes,
sections et langue. Les documents méthodologiques généraux restent admissibles.

Qwen reçoit un contexte borné de faits et passages. Le serveur insère les chiffres,
unités, périodes et citations, puis vérifie le résultat. Les propositions d'action
contrôlées indiquent leurs constats et restent à valider. Les chiffres OCR ne sont
pas promus en KPI ; une concomitance campagne/fréquentation n'est pas une causalité.

Chromium rend les rapports, notes et présentations sans accès réseau aux ressources
des documents. Les gabarits échappent les textes. Un débordement détecté des formats
fixes provoque un refus explicite, sans masquage du contenu. Les présentations
abrègent explicitement certains textes et renvoient au rapport complet.

## Choix de dépendances et sécurité

SQLite suffit à la persistance locale actuelle et évite une migration inutile des
données existantes. PostgreSQL/psycopg/SQLAlchemy/Alembic ne sont pas utilisés.
PyQvd fonctionne ici sans pandas ; les projections emploient du Python contrôlé,
sans statsmodels. Scikit-learn et NumPy sont notamment transitifs des modèles.
Le client Ollama passe par HTTPX : son SDK Python n'est pas nécessaire.

Les sessions, modules, territoires, propriétaires et versions sont vérifiés côté
serveur, y compris lors d'une relecture de conversation ou de tâche. Les anciens
imports sont conservés avec une politique privée. Les sources des diagnostics sont
revérifiées avant réemploi dans un rapport. Aucun `eval`, SQL libre ou outil de fichier
n'est confié au modèle.

Cette architecture ne démontre ni chiffrement industriel, ni SSO, ni WORM externe,
ni SLA/charge de production. Le corpus public et reproductible peut présenter des
corrélations permettant d'inférer certaines valeurs : les tests RBAC démontrent les
contrôles applicatifs, pas une confidentialité statistique industrielle. Une migration
ou infrastructure future devrait préserver les identifiants, versions, politiques et
preuves ; elle n'est pas une condition de finalisation des données synthétiques.
