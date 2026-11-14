# Les fichiers de l'interface

## `frontend/src/app/main.tsx`

Point d'entrée React. `createRoot()` monte `Workspace` sous `StrictMode`. Le paramètre `?legacy=1` sélectionne l'ancienne `ReportsPage` et charge son CSS. L'appel vient de `frontend/index.html`. Exemple : ouvrir `/` affiche la connexion de l'application complète.

## `frontend/src/features/workspace/Workspace.tsx`

Composant principal, sans paramètre, appelé par `main.tsx`. Il utilise les composants ci-dessous, `workspaceApi`, les types communs et l'API de rapports existante.

| Fonction | Paramètres, résultat et exemple |
| --- | --- |
| `Icon({name,size})` | Rend un SVG local à partir d'un nom autorisé. Exemple : icône de conversation dans la navigation, sans service externe. |
| `Login({onLogin})` | Rend le formulaire ; `submit(event)` envoie identifiant/mot de passe à l'API puis rappelle `onLogin()`. Une erreur conserve la saisie. |
| `Workspace()` | Rend l'espace connecté ou la connexion. Ses états gardent utilisateur, page, sources, résultats, rapports, messages, brouillon et version du chat. |
| `load()` | Charge identité et ressources ; tente de restaurer le dernier chat autorisé du compte. Retour : promesse terminée après chargement, erreurs individuelles signalées. |
| `send(value=draft)` | Envoie une question avec conversation/version/langue. Met à jour messages et résultats seulement après réussite ; conserve le texte en cas d'erreur. |
| `createFor(analysis)` | Crée une synthèse depuis l'identifiant précis d'une carte d'analyse, ouvre Rapports et rattache le résultat au contexte. Cela évite d'utiliser accidentellement une autre analyse plus récente. |
| `linkContext(analysisId,reportId)` | Synchronise les références autorisées avec le serveur et conserve la nouvelle version du contexte. |
| `reportChanged(report)` | Met à jour la bibliothèque et déclenche la synchronisation après une révision/export. |
| `refresh()` | Relit les sources, recherche les alertes, recharge résultats encore valides et disponibilité des services. Aucun monitoring permanent. |
| `newConversation()` | Vide le contexte de l'écran et la référence locale du dernier chat, sans effacer les conversations conservées sur le serveur. |
| `Empty({icon,title,action,onClick})` | Rend un état vide avec une action réellement branchée. Exemple : commencer une analyse depuis une bibliothèque vide. |

Les fonctions passées à `onClick` ou `onSubmit` sont des adaptateurs d'événement ; elles n'effectuent aucun calcul KPI. Les permissions reçues servent à afficher le périmètre, jamais à définir les autorisations serveur.

## `frontend/src/features/workspace/api.ts`

Décrit `Source`, `Catalog`, `Alert`, `Status`, `Message`, `Turn` et `Conversation` : ce sont les formes TypeScript des réponses API. Importe les types partagés `AnalysisResult`, `ReportResult`, `AccessContext` et `Language`.

`request<T>(url, body?, method='GET')` appelle `fetch` avec les cookies de même origine, contrôle le statut et renvoie le JSON typé ou lève une erreur lisible. Utilisé par `Workspace`, et directement par Documents pour le catalogue.

Les méthodes de `workspaceApi` sont des petits adaptateurs : `me/login/logout` gèrent la session ; `catalog/status/alerts/analyses` lisent les écrans ; `send(message,cid,version,language)` envoie un tour ; `conversation(id)` restaure l'historique ; `link(cid,version,analysisId,reportId)` synchronise le contexte ; `refresh()` déclenche le contrôle des sources. Elles ne simulent pas leurs réponses.

## `frontend/src/features/workspace/AnalysisCard.tsx`

Appelé par la conversation et l'écran Analyses.

- `metricNames` associe les identifiants métier à des libellés lisibles.
- `formatNumber(value)` formate un nombre en français ; une valeur nulle affiche « Indisponible ».
- `DataChart({analysis})` transforme uniquement les valeurs/séries API en barres ou ligne SVG. Les titres des points donnent date, valeur, unité et statut prévu/observé. L'axe part de zéro pour ces mesures non négatives.
- `AnalysisCard({analysis,onReport?})` rend valeurs, variation calculée, graphique, détails de provenance et bouton de synthèse. Il appelle `onReport` avec le résultat choisi par son parent ; il ne recalcule pas la variation.

Exemple : `current=80000`, `previous=100000`, `change_pct=-20` produit deux barres et le constat −20 %, avec `commercial.qvd` dans les détails.

## `frontend/src/features/workspace/ReportPanel.tsx`

Entrées : `report`, `onChange(report)` et `onError(message)`. Appelé par l'espace Rapports. Utilise l'API Salma existante, les identifiants de sections et la version courante.

`run(label,operation)` encadre la promesse avec un état occupé et une erreur visible. Le formulaire de révision appelle `api.revise()` avec `base_version`; l'aperçu appelle `api.export()` puis affiche un iframe protégé. Le téléchargement appelle `api.download()`. Exemple : traduire `summary` en arabe crée une nouvelle version avant l'export.

## `frontend/src/features/workspace/DocumentsPanel.tsx`

Sans paramètre, appelé par Workspace. Charge les documents autorisés, conserve fichier/titre/langue/question et utilise `run(label,action)` pour gérer erreurs et chargements. L'import appelle `api.upload(file,title,language,documentId)` ; l'identifiant facultatif demande une nouvelle version. La recherche appelle `api.search(question)` et affiche les preuves avec page, version et origine OCR. Exemple : un scan donne « OCR : transcription à relire ».

## `frontend/src/features/workspace/workspace.css`

Styles de l'espace complet : palette, navigation, connexion, chat, cartes, graphiques, documents, rapports et mise en page mobile. Contient focus visibles, états de chargement et règle de réduction des animations. Ne contient pas de données de graphique et ne télécharge pas de police. Appelé par `Workspace.tsx`.

## Composants Salma conservés

| Fichier | Rôle, fonctions et place dans le parcours |
| --- | --- |
| `frontend/src/features/reports/types.ts` | Interfaces des contrats existants : périodes, analyses, sources, rapports, révisions, preuves et configuration. Importées par les deux interfaces et APIs ; pas de calcul ni requête. |
| `frontend/src/features/reports/api.ts` | `ApiError(detail)` garde le code d'erreur. `request<T>(path,init)` contrôle HTTP ; `json(body,method)` construit une requête JSON. `api.create/read/list/revise/export/search/upload/download` appellent les routes Salma. Le téléchargement vérifie la forme de la route PDF puis crée une URL Blob temporaire. |
| `frontend/src/features/reports/ReportsPage.tsx` | Ancienne interface autonome : `ReportsPage()` rend formulaire, lecture/version, révision et documents ; `run(label,action)` gère les erreurs, `selectReport(value)` choisit la version et `create(event)` appelle l'API. Conservée sous `?legacy=1` et dans les tests de régression. |
| `frontend/src/features/reports/reports.css` | Styles historiques de cette page. Chargés pour le parcours legacy ; ne redéfinissent pas la logique de données. |

Les tests React sont décrits dans l'inventaire des outils. Les fichiers de compilation sous `frontend/dist/` sont générés et exclus de Git : on les recrée avec `npm run build`.
