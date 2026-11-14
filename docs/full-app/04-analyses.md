# Doha : calculer sans inventer

Le catalogue contient seize indicateurs définis dans `analytics/metrics.py`. Un indicateur décrit son identifiant, son libellé, son unité, les champs nécessaires, sa formule et ses limites. `metric_catalog()` n'expose que ceux autorisés par les modules du compte.

Ces définitions s'appliquent au corpus pédagogique définitif. Leur validation ne dépend pas de fichiers réels ; le test `test_synthetic_reference.py` contrôle les seize calculs sur l'oracle manuel versionné. L'objectif des KPI supplémentaires et des autres analyses du CPS reste dans le [reste à développer](10-perimetre-pedagogique.md).

## Noyau disponible

Sommes : nuitées, arrivées, sièges, réservations, budget, dépenses, engagements, recettes voyages et revenus des chambres.

Ratios : durée moyenne de séjour ; taux d'occupation ; RevPAR ; prix moyen d'une chambre vendue ; taux d'exécution budgétaire ; taux de clic ; dépenses promotionnelles par nuitée.

Un ratio se calcule sur les sommes du périmètre, jamais comme une moyenne non pondérée de ratios de lignes. Par exemple la durée moyenne est `somme(nuitées) / somme(arrivées)`. Le taux d'occupation est `100 × chambres-nuits vendues / chambres-nuits disponibles`.

Le dernier ratio rapproche Finance et Commercial avec contrôle des grains. Il ne s'appelle volontairement pas ROI : nous ne disposons pas d'une attribution économique validée des recettes aux dépenses.

`AnalyticsService.benchmark()` compare aussi plusieurs destinations ou marchés en appelant les mêmes calculs pour chaque périmètre autorisé. Le chat prend en charge, par exemple, « Compare les nuitées à Agadir et Marrakech en février 2025 » ou « Montre les nuitées à Agadir par marché en février 2025 ». Les résultats conservent chacun leurs filtres et sources ; un rapport demandé ensuite peut utiliser l'ensemble de ces analyses. Ce rapprochement interne n'est pas un benchmark international avec des données OMT/WTTC externes.

## Qualité et cas non calculables

`inspect_rows()` recherche doublons de clé/grain, dimensions vides, dates invalides, mesures manquantes, types non numériques, nombres négatifs ou non finis, unités absentes et occupation supérieure à la capacité. Une erreur bloque le calcul ; une cellule manquante ne devient pas zéro.

`AnalyticsService.run(request, access)` accepte le contrat commun `AnalysisRequest`. Les périodes doivent couvrir des mois complets. Les filtres autorisés sont `destination` et `market`. `value` produit une valeur et sa série mensuelle ; `compare` donne `current`, `previous` et `change_pct`. Une référence nulle ne permet pas de division. Une période absente des QVD produit un statut `unavailable`, une valeur nulle et un avertissement.

Les mois ou périmètres incomplets sont signalés. Une clé de même nom ne suffit pas à autoriser une jointure. Les sources d'un ratio entre domaines doivent contenir les mêmes mois, destinations et marchés.

## Prévisions

Le prototype propose des prévisions mensuelles, sur 36 mois complets minimum et au plus douze mois d'horizon. Les douze derniers mois sont gardés hors entraînement. Deux références sont comparées : dernière valeur constante et même mois de l'année précédente. La méthode de plus faible MAE sur ce bloc est utilisée pour prévoir depuis la fin de l'historique fourni.

Les avertissements donnent les MAE des deux références, la RMSE et la méthode retenue. La bande autour des projections utilise les erreurs empiriques du bloc de test ; sa couverture probabiliste n'est pas garantie. Les points ont `kind: observed` ou `forecast`. Cette sélection sur un petit bloc ne remplace pas une évaluation glissante complète ni une validation économique.

## Alertes

`AlertService.refresh(access)` compare chaque mois au même mois de l'année précédente. Une variation d'au plus −15 % produit une alerte. Une clé stable par règle, destination et mois évite les doublons. La source versionnée permet de marquer une alerte ancienne après modification des fichiers.

L'actualisation est déclenchée par le bouton Sources/Alertes ou `/api/sources/refresh`. Aucun service ne prétend surveiller en permanence. La baisse injectée de −20 % à Agadir en février 2025 est le scénario de référence.

## Ajouter un indicateur

1. Définir et documenter la convention pédagogique : formule, unité, grain et cas non calculables. Une validation sur un patrimoine réel n'est pas un prérequis du projet.
2. Vérifier les champs logiques disponibles dans le mapping et leurs unités canoniques dans le contrôle de `AnalyticsService._read()` si de nouveaux champs sont ajoutés.
3. Ajouter une instance `Metric` dans `METRICS`. Les agrégations supportées sont somme, ratio et pourcentage ; une formule différente nécessite une fonction testée dans `calculate()`.
4. Ajouter un test avec une réponse attendue calculée indépendamment du moteur.
5. Vérifier les droits, les avertissements et la restitution dans le chat/rapport.

La formule du catalogue utilise les noms logiques. `Metric.source_formula()` restitue les colonnes physiques effectivement configurées dans le résultat, et qualifie les sources lorsqu'il y a plusieurs domaines. Le test de remplacement de colonne vérifie qu'une nouvelle correspondance conserve le calcul et met aussi à jour la formule et les champs cités.

Les acronymes ambigus, les indices internationaux sans données, le PIB, les benchmarks étrangers et la classification Butler ne sont pas inventés. Leur absence est une limite du noyau, pas une donnée à compléter par le LLM.
