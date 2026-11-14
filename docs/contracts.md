# ONMT AI - Contrats d’échange

Version : 0.1

Périmètre de données confirmé le 14 novembre 2026 : les QVD synthétiques sont la référence
définitive du rendu pédagogique. Leur emploi n'implique pas des traitements simulés.
Les résultats et exports conservent `is_synthetic: true` et un marquage visible ;
la configuration d'autres QVD demeure facultative. Aucun champ de contrat n'est supprimé.
Statut : proposition commune à valider par Hayat, Doha et Salma.

Intégration locale du 11 novembre 2026 : les champs de ces contrats sont conservés.
Le fournisseur `AnalysisProvider` de Salma est implémenté par `AnalyticsService`, avec
des calculs sur QVD natifs. Les routes supplémentaires de session, catalogue,
conversation et alertes sont décrites dans [le guide d'intégration](full-app/README.md).
Une réponse analytique synthétique utilise maintenant les QVD générés dans le mode
complet ; les anciens exemples JSON restent des fixtures de test explicites.

## 1. Responsabilités

- Hayat : compréhension des questions, contexte, coordination et accès QVD.
- Doha : qualité des données, calculs, analyses et prévisions.
- Salma : recherche documentaire, RAG, rapports et export PDF.

Chaque membre développe les routes, fonctions et écrans de son module.

## 2. Principes communs

- Les échanges utilisent des objets JSON.
- Les noms de champs sont écrits en snake_case.
- Les dates suivent le format YYYY-MM-DD.
- Les périodes incluent leur date de début et leur date de fin.
- Les horodatages suivent ISO 8601 avec un fuseau horaire.
- Une valeur manquante est null : elle ne doit pas devenir zéro.
- Les nombres et leurs unités sont séparés.
- Les résultats fictifs portent is_synthetic: true.
- Les champs et filtres sont contrôlés côté serveur.
- Les permissions ne sont jamais décidées par le LLM.
- Une modification de contrat doit être communiquée aux trois membres.

Langues :

- fr : français
- ar : arabe
- ary : darija
- en : anglais
- es : espagnol

request_id identifie une opération et permet de retrouver ses événements.
analysis_id et report_id identifient les ressources réutilisables.

## 3. AnalysisRequest : Hayat vers Doha

Objectif : demander une consultation, une comparaison ou une prévision.

Champs :

| Champ              | Type            | Rôle                                    |
| ------------------ | --------------- | --------------------------------------- |
| request_id         | string          | Identifiant de la demande               |
| operation          | string          | value, compare ou forecast              |
| metric_id          | string          | Identifiant d’un KPI du catalogue       |
| period             | Period          | Période consultée ou historique utilisé |
| comparison_period  | Period ou null  | Période de comparaison                  |
| filters            | object          | Critères autorisés                      |
| language           | string          | Langue demandée                         |
| forecast_horizon   | integer ou null | Nombre de périodes à prévoir            |
| forecast_frequency | string ou null  | month, quarter ou year                  |

Period :

- start : date
- end : date

Règles :

- start doit être antérieur ou égal à end.
- metric_id doit exister dans le catalogue de Doha.
- Les filtres doivent correspondre à des champs autorisés.
- comparison_period est obligatoire pour la comparaison temporelle.
- forecast_horizon doit être positif pour une prévision.
- forecast_frequency est obligatoire pour une prévision.
- Pour les autres opérations, les champs forecast valent null.
- Une demande ambiguë est clarifiée par Hayat avant exécution.

## 4. AnalysisResult : Doha vers Hayat et Salma

Objectif : fournir un résultat calculé et vérifiable.

| Champ             | Type           | Rôle                                |
| ----------------- | -------------- | ----------------------------------- |
| request_id        | string         | Demande associée                    |
| analysis_id       | string         | Identifiant du résultat             |
| metric_id         | string         | Indicateur calculé                  |
| status            | string         | ok, partial ou unavailable          |
| period            | Period         | Période réellement utilisée         |
| comparison_period | Period ou null | Comparaison réellement utilisée     |
| filters           | object         | Filtres réellement appliqués        |
| unit              | string         | Unité de l’indicateur               |
| values            | object         | Valeurs numériques ou null          |
| series            | array          | Points destinés aux graphiques      |
| formula           | string         | Description de la formule appliquée |
| sources           | array          | Liste de SourceReference            |
| warnings          | array[string]  | Limites et avertissements           |
| is_synthetic      | boolean        | Indique un résultat fictif          |

Signification des statuts :

- ok : résultat disponible sur le périmètre demandé.
- partial : résultat incomplet, avec limites précisées.
- unavailable : données insuffisantes pour produire le résultat.

Clés initiales de values :

- Pour value : value.
- Pour compare : current, previous, change_pct.
- Pour forecast : les prévisions sont placées dans series.

unit s’applique à value, current, previous et aux valeurs de series.
change_pct est exprimé en pourcentage.

Un point de series contient :

- date : date du point ou début de la période agrégée.
- value : number ou null.
- kind : observed ou forecast.
- lower : borne inférieure ou null.
- upper : borne supérieure ou null.

Règles :

- Les chiffres sont calculés par le code métier de Doha.
- Une référence de comparaison nulle ne permet pas une division.
- Les intervalles de prévision doivent être justifiés par la méthode.
- Le statut unavailable comporte un avertissement explicatif.
- Les données synthétiques restent clairement identifiées.
- Salma ne recalcule pas les KPI à partir du texte du résultat.

## 5. SourceReference

Objectif : identifier une source réellement utilisée.

| Champ       | Type           | Rôle                              |
| ----------- | -------------- | --------------------------------- |
| source_id   | string         | Identifiant de la source          |
| source_type | string         | qvd, document ou external         |
| name        | string         | Nom affichable                    |
| version     | string         | Version ou identifiant du contenu |
| fields      | array[string]  | Champs utilisés, si applicable    |
| pages       | array[integer] | Pages utilisées, si applicable    |

Règles :

- Les pages commencent à 1.
- fields et pages peuvent être des listes vides.
- Ne pas exposer un chemin local sensible.
- Le backend conserve le moyen de retrouver la source.
- Les références documentaires doivent permettre de retrouver
  le passage utilisé.
- Les filtres et périodes des calculs restent dans AnalysisResult.

## 6. ReportRequest : Hayat vers Salma

Objectif : demander un rapport fondé sur des analyses disponibles.

| Champ        | Type          | Rôle                             |
| ------------ | ------------- | -------------------------------- |
| request_id   | string        | Identifiant de la demande        |
| analysis_ids | array[string] | Analyses à utiliser              |
| title        | string        | Titre du rapport                 |
| language     | string        | Langue demandée                  |
| audience     | string        | direction, ministere ou regional |
| sections     | array[string] | Sections demandées               |

Identifiants initiaux des sections :

- summary : résumé exécutif.
- diagnostic : diagnostic.
- comparison : comparaison.
- forecast : prévisions.
- recommendations : recommandations.
- limitations : limites des résultats.

Règles :

- Pour ce premier contrat de rapport analytique, analysis_ids
  contient au moins un identifiant.
- Salma récupère les résultats via un adaptateur commun.
- L’existence et les droits de chaque analyse sont vérifiés.
- Une section sans données suffisantes indique la limite.
- Une donnée manquante ne doit pas être inventée.

## 7. ReportResult : Salma vers Hayat

Objectif : fournir l’état et le contenu du rapport.

| Champ         | Type           | Rôle                                  |
| ------------- | -------------- | ------------------------------------- |
| request_id    | string         | Demande associée                      |
| report_id     | string         | Identifiant du rapport                |
| version       | integer        | Version du rapport                    |
| status        | string         | pending, running, completed ou failed |
| sections      | array          | Sections disponibles                  |
| sources       | array          | Références du rapport                 |
| download_path | string ou null | Route API protégée du PDF             |
| warnings      | array[string]  | Limites et avertissements             |
| is_synthetic  | boolean        | Présence de données fictives          |

Une section contient :

- section_id : string.
- title : string.
- content : string.
- source_ids : array[string].

Signification des statuts :

- pending : demande enregistrée.
- running : génération en cours.
- completed : génération et contrôles terminés.
- failed : génération en échec.

Règles :

- version est un entier positif.
- Chaque source_id cité existe dans sources.
- download_path reste null tant que le PDF n’est pas disponible.
- L’accès à cette route vérifie les permissions.
- Un rapport utilisant des résultats synthétiques conserve
  is_synthetic: true.
- Ne pas considérer une simple présence de citation comme
  une preuve que le texte est correct.

## 8. ReportRevisionRequest : modification d’un rapport

| Champ        | Type    | Rôle                              |
| ------------ | ------- | --------------------------------- |
| request_id   | string  | Identifiant de la demande         |
| report_id    | string  | Rapport concerné                  |
| base_version | integer | Version que l’utilisateur modifie |
| section_id   | string  | Section visée                     |
| instruction  | string  | Modification demandée             |

Règles :

- Vérifier les permissions.
- Vérifier que base_version correspond à la version courante.
- Sinon, retourner version_conflict.
- Mettre à jour la section et les autres sections qui en dépendent.
- Conserver les parties non concernées.
- Une modification réussie produit une nouvelle version.

## 9. ErrorResponse : erreurs communes

| Champ      | Type   | Rôle                           |
| ---------- | ------ | ------------------------------ |
| request_id | string | Demande concernée              |
| code       | string | Identifiant stable de l’erreur |
| message    | string | Explication compréhensible     |

Codes initiaux :

- missing_data : données nécessaires absentes.
- forbidden : opération non autorisée.
- invalid_request : paramètres invalides.
- version_conflict : version de rapport obsolète.
- tool_failed : échec d’un composant.

Règles :

- Ne pas renvoyer une trace technique brute au navigateur.
- Ne pas révéler l’existence d’une ressource confidentielle.
- Ne pas remplacer une erreur réelle par un succès fictif.

## 10. AccessContext : contexte interne au backend

Champs :

- user_id : string.
- roles : array[string].
- allowed_modules : array[string].
- allowed_territories : array[string].

Règles :

- Construit à partir d’une identité authentifiée.
- Transmis séparément aux fonctions sensibles.
- Jamais accepté comme une permission déclarée par le navigateur.
- Les listes vides n’accordent aucun accès.
- Les droits sur les documents et rapports sont également vérifiés
  à partir de leur classification et de leurs règles d’accès.
- Ce contexte ne suffit pas à lui seul à définir toute la politique
  d’autorisation.

## 11. Fonctions d’intégration proposées

Les signatures exactes seront implémentées dans le code.

Hayat utilise :

- run_analysis(request, access_context)
- create_report(request, access_context)
- revise_report(request, access_context)

Salma utilise :

- get_analysis(analysis_id, access_context)

Doha fournit :

- Le traitement des AnalysisRequest.
- La récupération des AnalysisResult autorisées.

Salma fournit :

- La création, la lecture et la modification des rapports.
- La génération et l’accès protégé au PDF.

Les modules peuvent communiquer par appels Python internes.
Il n’est pas obligatoire de créer des appels HTTP entre eux.

## 12. Développement sans les autres modules

- Utiliser les exemples de examples/contracts/.
- Garder les simulations dans les tests ou un mode démo explicite.
- Ne pas transformer les exemples en véritables données ONMT.
- Prévoir un adaptateur pour remplacer les simulations.
- Tester ensuite les échanges avec les modules réels.

## 13. Validation des contrats

- Implémenter les modèles Pydantic dans backend/app/schemas/.
- Vérifier les exemples JSON avec ces modèles.
- Préparer les types TypeScript correspondants.
- Tester les valeurs nulles, erreurs, permissions et versions.
- Relire ensemble tout changement incompatible.
- Mettre à jour ce document et les exemples dans le même changement.
