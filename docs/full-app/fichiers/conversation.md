# Inventaire : conversation

Signatures extraites du code ; descriptions pédagogiques maintenues dans `scripts/build-code-guide.py`. Les imports listés sont statiques : ils ne remplacent pas le parcours guidé des appels par injection.

## `backend/app/conversation/__init__.py`

Marque le répertoire comme package Python ; aucune logique métier autonome.

**Exemple :** Permet les imports des modules voisins.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

## `backend/app/conversation/context.py`

Fusionne les paramètres d’une relance avec la dernière demande analytique ; laisse une demande incomplète sans calcul.

**Exemple :** analysis_request(intent,context) renvoie AnalysisRequest ou None si une précision est nécessaire.

**Utilise :** `app.core.errors`, `app.schemas.analysis`

**Importé par :** `backend/app/conversation/service.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `analysis_request(intent, context)` | Construit le contrat analytique depuis l’intention et le contexte ; renvoie None si une information obligatoire manque. |

## `backend/app/conversation/graph.py`

Construit le graphe LangGraph à deux nœuds : interprétation puis outil autorisé, avec un état Turn explicite.

**Exemple :** build_graph(interpret,execute) retourne le graphe compilé ; invoke utilise recursion_limit=6.

**Utilise :** `langgraph.graph`

**Importé par :** `backend/app/conversation/service.py`

**Classe `Turn`** : hérite de TypedDict.

Champs contrôlés : `message: str`; `context: dict`; `access: Any`; `language: str`; `intent: Any`; `response: dict`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `build_graph(interpret, execute)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/conversation/intent.py`

Décrit Intent et demande au vrai modèle de choisir une action structurée parmi les outils autorisés.

**Exemple :** parse(message,context,catalog,language) retourne Intent, ensuite revalidé côté métier.

**Utilise :** `app.core.errors`, `app.schemas.common`

**Importé par :** `backend/app/main.py`

**Classe `Intent`** : hérite de Contract.

Champs contrôlés : `action: Literal['analyse', 'benchmark', 'report', 'revise', 'update_report', 'document', 'clarify']`; `group_by: Literal['destination', 'market']`; `dimensions: list[str] | None`; `metric_id: str | None`; `operation: Literal['value', 'compare', 'forecast'] | None`; `period: Period | None`; `comparison_period: Period | None`; `destination: str | None`; `market: str | None`; `language: Language`; `audience: Literal['direction', 'ministere', 'regional']`; `horizon: int | None`; `section_id: Literal['summary', 'diagnostic', 'comparison', 'forecast', 'recommendations', 'limitations']`; `instruction: str | None`; `clarification: str | None`.

**Classe `IntentParser`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `IntentParser.__init__(self, client)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `IntentParser.parse(self, message, context, catalog, language)` | Transforme la demande et son contexte autorisé en intention JSON validée ; ne calcule pas les KPI. |

## `backend/app/conversation/router.py`

Expose messages, lecture autorisée d’une conversation et synchronisation du contexte.

**Exemple :** POST /api/conversations/messages ne prend jamais un rôle ou un chemin de fichier.

**Utilise :** `app.core.errors`, `app.reports.router`, `app.schemas.common`

**Importé par :** `backend/app/main.py`

**Classe `Message`** : hérite de Contract.

Champs contrôlés : `message: str`; `conversation_id: str | None`; `base_version: int`; `language: Language`.

**Classe `ContextLink`** : hérite de Contract.

Champs contrôlés : `conversation_id: str | None`; `base_version: int`; `analysis_id: str | None`; `report_id: str | None`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `link(body: ContextLink, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `send(body: Message, request: Request, access: Access)` | Entrées : texte, accès, conversation, version et langue. Résultat : message avec analyse/rapport/preuves et trace des outils. |
| `read(conversation_id: str, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |

## `backend/app/conversation/service.py`

Coordonne les outils de Doha et Salma, conserve historique/contexte/version et synchronise les écrans complémentaires.

**Exemple :** send(message,access,cid,base_version,language) rend une réponse avec opérations réelles ; link_context rattache une sélection autorisée.

**Utilise :** `app.core.errors`, `app.schemas.report`

**Importé par :** `backend/app/main.py`

**Classe `ConversationService`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `ConversationService.__init__(self, state, analytics, reports, exporter, parser)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `ConversationService._title(self, analysis, access, multiple=False)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ConversationService._interpret(self, turn)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ConversationService._execute(self, turn)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `ConversationService.send(self, message, access, cid=None, base_version=0, language='fr')` | Entrées : texte, accès, conversation, version et langue. Résultat : message avec analyse/rapport/preuves et trace des outils. |
| `ConversationService.link_context(self, access, cid, base_version, analysis_id=None, report_id=None)` | Rattache une sélection autorisée aux paramètres de conversation en respectant sa version de base. |

## `backend/app/conversation/slots.py`

Ancre les mois et filtres explicitement nommés, avec les synonymes de dimensions configurés ; normalise une traduction identifiable.

**Exemple :** Février 2024 devient 2024-02-01/2024-02-29 ; un marché France ajouté par le modèle mais non demandé est retiré.

**Utilise :** `app.core.config`

**Importé par :** `backend/app/conversation/intent.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `normalized(text)` | Entrée : texte. Résultat : texte normalisé pour comparer les accents, chiffres arabes et synonymes sans modifier les données sources. |
| `explicit_periods(message)` | Entrée : texte de question. Résultat : au plus deux périodes mensuelles explicitement nommées, avec fin de mois exacte. |
| `ground_intent(intent, message, allowed=None)` | Entrées : intention, message et catalogue facultatif. Résultat : intention revalidée après ancrage des dates, filtres et traduction explicites. |
