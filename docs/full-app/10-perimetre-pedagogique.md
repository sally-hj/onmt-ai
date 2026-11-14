# Périmètre confirmé et reste à développer

Décision transmise le 14 novembre 2026 : les QVD synthétiques sont les données de référence définitives. Aucune attente de fichiers ONMT ne conditionne le rendu. Les définitions du corpus sont documentées, les calculs doivent être exacts sur ce corpus et les traitements IA réellement exécutés.

## Ce qui est acquis sur les données

Le format QVD est natif ; les trois domaines partagent un grain contrôlé et des clés cohérentes. Génération à graine fixe, dictionnaire, scénarios de baisse/saisonnalité, attendus manuels et jeu défectueux séparé sont disponibles. Le marquage synthétique reste requis dans l'interface, les réponses et les exports. Les documents du parcours peuvent eux aussi être fictifs, en PDF textuel ou réellement scanné.

Ce choix n'autorise pas à remplacer l'inférence, les embeddings, l'OCR ou les calculs par une réponse précalculée présentée comme fonctionnelle. Les clients simulés restent des outils de test identifiés ; le mode normal utilise les services locaux configurés et signale leur indisponibilité.

## Travail fonctionnel qui reste au bilan

Les priorités ci-dessous sont une proposition de réalisation, **pas une nouvelle réduction de périmètre**. Les critères du CPS restent dans la [matrice](01-couverture-cps.md) tant qu'un arbitrage explicite ne les adapte pas.

| Priorité | Écart constaté | Prochaine réalisation / preuve attendue |
| --- | --- | --- |
| P1 | 16 KPI, pas la totalité des 30+ | Définir les indicateurs suivants avec conventions pédagogiques, enrichir les champs synthétiques nécessaires, ajouter un oracle indépendant par calcul. Aucune fausse conformité à un référentiel international. |
| P1 | Diagnostic, recommandations et notes courtes | Enrichir le diagnostic avec faits calculés, hypothèses clairement séparées, sections/audiences, longs rapports et grille de relecture. Les sources ne suffisent pas à prouver la qualité économique du texte. |
| P1 | Révisions avancées et ajout de données/domaines | Tester cinq modifications successives, conserver les analyses utiles quand on ajoute un KPI, recalculer les dépendances et vérifier chiffres/citations/versions par vrai parcours conversationnel. Le remplacement actuel ne démontre pas tous les ajouts demandés. |
| P1 | Conversation longue et multilingue | Campagne de 50+ échanges, périodes/marchés référencés, ambiguïtés et erreurs ; plusieurs demandes par langue, darija et traductions. Un seul cas réussi par langue n'est pas une recette. |
| P1 | Scénarios inter-domaines et agents spécialisés | Démontrer collecte autorisée, calculs Finance/Commercial/Performance et rapport dans une seule demande, puis workflows spécialisés contrôlés. Deux nœuds LangGraph ne prouvent pas une équipe autonome. |
| P2 | BCG, Butler et benchmarks étrangers | Choisir des définitions/conventions explicites, créer les comparateurs synthétiques utiles et vérifier matrices/classements. L'absence de données réelles n'est plus un motif pour supprimer ces fonctions. |
| P2 | Création persistante de KPI via chat | Langage d'expressions limité, unités/champs/permissions validés, persistance et tests ; aucun `eval` de code utilisateur ou LLM. |
| P2 | Présentation 25 slides | Produire un vrai deck PDF avec graphiques calculés, lisibilité et marquage ; charte pédagogique cohérente sans prétendre à une charte officiellement homologuée. |
| P2 | Alertes, rafraîchissement et reprise | Étendre les règles et scénarios de résolution, vérifier les résultats obsolètes et l'actualisation contrôlée. Ne pas confondre ce déclenchement avec un monitoring 24/7. |
| P2 | Protection et traçabilité applicatives | Étendre profils/classifications et audit, tester refus et révocations. Définir l'adaptation attendue du chiffrement/audit immuable ; les données synthétiques ne dispensent pas de protéger les accès. |
| À arbitrer explicitement | Voix, streaming et routage multi-modèles | Présents dans la cible CPS, pas réalisés actuellement. Confirmer leur adaptation locale et développer les fonctions retenues ; l'accord sur les données seul ne les met pas hors périmètre. |
| Validation transversale | UX, accessibilité, exactitude et latence | Recette plus large des graphiques/exports/RTL/erreurs, lecteurs d'écran et temps mesurés sur ce PC. Les délais industriels ne sont pas atteints par le simple succès d'un scénario. |

## Exigences industrielles distinctes

Le développement local exclut déjà déploiement, Docker, CI/CD et infrastructure cloud. Datacenter certifié, GPU souverains industriels, PRA multi-sites et SLA d'exploitation ne sont pas des acquis de ce projet local. L'intégration SSO d'entreprise est distincte des comptes locaux réalisés. Les protections applicatives et fonctions de restitution restent, elles, à évaluer dans le projet pédagogique.

Les QVD de production et leur recette ONMT ne sont plus à classer comme « bloqués/en attente ». Leur compatibilité relève uniquement de l'extension facultative de configuration. Les conventions actuelles du corpus et des KPI sont la référence du projet ; un indicateur ambigu doit recevoir une définition pédagogique transparente, pas une formule attribuée sans preuve à l'ONMT.

## Conditions de finalisation à suivre

Le rendu pourra être annoncé comme complet lorsque les fonctions retenues auront une preuve adaptée : calculs sur oracle indépendant, contrats et droits, parcours réels IA/documentaires, conversations et révisions, exports lisibles et erreurs explicites. La matrice doit conserver chaque écart non résolu, ou l'arbitrage qui l'adapte. La décision sur les données ne constitue pas cette validation fonctionnelle globale.
