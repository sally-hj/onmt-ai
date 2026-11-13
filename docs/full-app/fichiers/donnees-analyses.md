# Inventaire : donnees-analyses

Signatures extraites du code ; descriptions pédagogiques maintenues dans `scripts/build-code-guide.py`. Les imports listés sont statiques : ils ne remplacent pas le parcours guidé des appels par injection.

## `backend/app/analytics/__init__.py`

Marque le répertoire comme package Python ; aucune logique métier autonome.

**Exemple :** Permet les imports des modules voisins.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

## `backend/app/analytics/anomalies.py`

Calcule et conserve les alertes de baisse annuelle à l’actualisation ; utilise une clé stable pour ne pas les dupliquer.

**Exemple :** refresh(access) retrouve Agadir février 2025 à −20 % dans le corpus fictif.

**Utilise :** `app.core.errors`

**Importé par :** `backend/app/main.py`

**Classe `AlertService`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `AlertService.__init__(self, catalog, state)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `AlertService.refresh(self, access)` | Relit les données autorisées et remplace les alertes du périmètre sans doublons ; pas un ordonnanceur permanent. |
| `AlertService.list(self, access)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/analytics/forecasting.py`

Évalue deux références temporelles sur douze mois mis de côté et produit les prévisions mensuelles avec limites explicites.

**Exemple :** forecast(series,6) retourne points prévus et avertissements d’erreur/méthode.

**Utilise :** `app.core.errors`, `app.schemas.analysis`

**Importé par :** `backend/app/analytics/service.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `next_month(value, offset=1)` | Entrées : date et décalage de mois. Résultat : premier jour du mois décalé, y compris au passage d’une année. |
| `forecast(series, horizon)` | Entrées : série mensuelle et horizon. Résultat : points projetés, méthode, erreurs et limites, sans données futures d’entraînement. |

## `backend/app/analytics/metrics.py`

Déclare les seize définitions métier du noyau et leurs calculs autorisés, sans eval ni code produit par IA.

**Exemple :** calculate(metric,totals) donne une somme ou un ratio ; un dénominateur nul donne None.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/analytics/service.py`

**Classe `Metric`**.

Champs contrôlés : `id: str`; `label: str`; `unit: str`; `fields: dict[str, list[str]]`; `formula: str`; `kind: str`; `limit: str`.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `metric_catalog(access, sources)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `calculate(metric, totals)` | Applique uniquement les opérations du catalogue aux totaux déjà sélectionnés ; renvoie nombre ou None. |
| `Metric.source_formula(self, sources)` | Entrée : mapping des sources. Résultat : description de formule utilisant les colonnes réellement lues, avec qualification des domaines pour un rapprochement. |

## `backend/app/analytics/quality.py`

Recherche les erreurs de qualité avant les sommes : doublons, dates, valeurs, unités et capacité.

**Exemple :** inspect_rows(rows,source) renvoie une liste de codes ; une liste non vide bloque l’analyse.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** `backend/app/data_access/catalog.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `inspect_rows(rows, source)` | Entrées : lignes et définition de source. Résultat : codes d’anomalies bloquantes, sans correction silencieuse. |

## `backend/app/analytics/router.py`

Expose catalogue, indicateurs, analyses, alertes, actualisation et état des services à l’interface, sous contrôle d’accès.

**Exemple :** POST /api/analyses appelle analytics.run ; GET /api/sources appelle catalog.describe.

**Utilise :** `app.core.errors`, `app.reports.router`, `app.schemas.analysis`

**Importé par :** `backend/app/main.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `status(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `sources(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `metrics(request: Request, access: Access)` | Entrée : accès. Résultat : définitions des indicateurs dont tous les modules requis sont autorisés. |
| `analyse(body: AnalysisRequest, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `analyses(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `read(analysis_id: str, request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `alerts(request: Request, access: Access)` | Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée. |
| `refresh(request: Request, access: Access)` | Relit les données autorisées et remplace les alertes du périmètre sans doublons ; pas un ordonnanceur permanent. |

## `backend/app/analytics/service.py`

Orchestre accès, agrégations, comparaisons et prévisions ; fournit aussi l’adaptateur AnalysisProvider de Salma.

**Exemple :** run(AnalysisRequest,AccessContext) rend un AnalysisResult ; get_analysis recontrôle droits et fraîcheur.

**Utilise :** `app.core.errors`, `app.schemas.analysis`, `app.schemas.common`

**Importé par :** `backend/app/main.py`

**Classe `AnalyticsService`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `AnalyticsService.__init__(self, catalog, state)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `AnalyticsService.metrics(self, access)` | Entrée : accès. Résultat : définitions des indicateurs dont tous les modules requis sont autorisés. |
| `AnalyticsService.benchmark(self, request, access, group_by, dimensions=None)` | Entrées : demande analytique, accès, dimension de regroupement et valeurs facultatives. Résultat : une analyse autorisée par destination/marché, sans jointure multiplicative. |
| `AnalyticsService._metric(self, metric_id, access)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `AnalyticsService._read(self, metric, filters, access)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `AnalyticsService._aggregate(self, metric, data, period)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `AnalyticsService.run(self, request, access)` | Entrées : demande validée et accès serveur. Résultat : analyse calculée et persistée, ou erreur explicite. |
| `AnalyticsService.authorize_snapshot(self, analysis_id, access_context)` | Contrôle propriétaire et périmètre d’un instantané sans le présenter comme à jour ; utilisé pour un recalcul explicite. |
| `AnalyticsService.get_analysis(self, analysis_id, access_context)` | Entrées : identifiant et accès. Résultat : analyse du propriétaire avec droits et version de source contrôlés. |

## `backend/app/data_access/__init__.py`

Marque le répertoire comme package Python ; aucune logique métier autonome.

**Exemple :** Permet les imports des modules voisins.

**Utilise :** bibliothèque standard, imports relatifs ou types du module.

**Importé par :** chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.

## `backend/app/data_access/catalog.py`

Charge les mappings, valide le grain, contrôle les lignes, décrit les sources et vérifie les associations.

**Exemple :** read_authorized_data("commercial",fields,filters,access) retourne des colonnes logiques et une version de source.

**Utilise :** `app.analytics.quality`, `app.core.errors`

**Importé par :** `backend/app/main.py`

**Classe `Catalog`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `Catalog.__init__(self, config: Path, root: Path)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `Catalog.version(self, sid, digest)` | Entrées : source et empreinte. Résultat : empreinte combinant contenu QVD et mapping métier, pour invalider aussi un changement de définition. |
| `Catalog.read_authorized_data(self, dataset_id, fields, filters, access_context)` | Entrées : source logique, champs, filtres et accès. Résultat : lignes logiques contrôlées et version combinée. |
| `Catalog.versions(self, source_ids)` | Entrée : identifiants de sources. Résultat : dictionnaire des versions actuelles relues depuis les fichiers configurés. |
| `Catalog.describe(self, access)` | Entrée : accès serveur. Résultat : catalogue des sources visibles, types, périodes, unités, erreurs et relations contrôlées. |

## `backend/app/data_access/qvd_reader.py`

Borne les chemins, vérifie les autorisations, lit nativement PyQvd, découvre les types et normalise les dates mensuelles.

**Exemple :** read(source,access,{"destination":"Agadir"}) retourne lignes autorisées, empreinte et types.

**Utilise :** `app.core.errors`, `pyqvd`

**Importé par :** `backend/app/data_access/catalog.py`

**Classe `QvdReader`**.

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `source_version(path: Path)` | Entrée : chemin configuré. Résultat : empreinte SHA-256 du contenu ; une source absente provoque une erreur. |
| `normalize_month(value)` | Entrée : date ISO, date Python ou numéro Qlik. Résultat : date ISO du premier jour du mois ; refuse une date hors grain. |
| `QvdReader.__init__(self, root: Path)` | Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné. |
| `QvdReader.path(self, source)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |
| `QvdReader.read(self, source, access, filters=None)` | Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact. |

## `backend/app/data_access/synthetic.py`

Crée le corpus mensuel fictif, l’écrit en QVD, relit toutes les cellules et écrit manifeste/références/jeux défectueux.

**Exemple :** generate(Path("local_data/qvd-synthetic")) produit trois domaines, chacun de 2 100 lignes.

**Utilise :** `pyqvd`

**Importé par :** `backend/app/core/auth.py`

| Fonction / paramètres | Résultat et rôle |
| --- | --- |
| `write_qvd(path, rows)` | Entrées : chemin de sortie et lignes. Écrit un vrai QVD et compare sa relecture cellule par cellule ; erreur en cas de différence. |
| `generate(directory: Path, seed=20261111)` | Entrées : dossier de sortie et graine fixe. Résultat : manifeste après écriture et relecture native des QVD. |
