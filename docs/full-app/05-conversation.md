# Hayat : comprendre, conserver le contexte, appeler les outils

## Identité locale

`LocalAuth` crée deux comptes de développement : `direction` et `regional`. Le premier peut lire les trois domaines et six destinations ; le second n'accède pas à Finance et reste limité à Agadir/Marrakech. Les politiques sont stockées côté serveur ; sélectionner une langue ou envoyer un rôle dans le navigateur ne change pas les droits.

Les mots de passe sont dérivés avec scrypt et sel aléatoire. Le cookie de session est opaque, HttpOnly, SameSite Strict et expire après huit heures. Son empreinte, et non sa valeur brute, est stockée. Le cookie n'utilise pas Secure sur le serveur HTTP local : il ne constitue pas une configuration Internet. Les tentatives de connexion sont limitées ; les écritures d'origine étrangère sont refusées. SSO et gestion d'utilisateurs d'entreprise ne sont pas implémentés.

Les identifiants de développement figurent dans le guide d'utilisation. Ce sont des comptes locaux sur corpus fictif, pas une politique de secrets pour des données réelles.

## Interprétation

`IntentParser.parse(message, context, catalog, language)` transmet au modèle la question, les paramètres de contexte et une liste compacte d'indicateurs/dimensions autorisés. Il ne transmet pas les lignes des QVD. L'appel Ollama est réel dans l'application normale.

La réponse est un `Intent` strict : action, indicateur, opération, périodes, destination/marché, langue, public, section et consigne éventuelle. Les actions sont analyse, comparaison de destinations/marchés (`benchmark`), création de rapport, révision, recalcul de rapport, recherche documentaire et clarification. Aucun code Python, SQL ou chemin n'est exécuté.

Un premier essai réel du petit modèle a omis des dates explicites et un autre a ajouté un marché non demandé. `slots.py` corrige ces cas en ancrant les mois nommés en FR/EN/ES/AR/darija, les destinations et marchés explicitement écrits. Les synonymes de dimensions sont centralisés dans `config/dimension-aliases.json`. Les paramètres omis peuvent venir du contexte autorisé ; ils ne doivent pas être inventés. Plusieurs valeurs d'une même dimension déclenchent un benchmark borné ; plusieurs dimensions simultanées nécessitent une précision. Ce contrôle ne calcule aucun KPI. Une structure JSON correcte ne prouve pas une compréhension parfaite.

La langue sélectionnée dans l'interface fixe celle des réponses courtes. Une traduction explicitement demandée peut changer la langue de la section. La compréhension est hybride : sélection de l'action par le modèle, puis ancrage/contrôle des paramètres par le code ; ce n'est pas une preuve d'autonomie linguistique du seul LLM.

## Contexte et versions

Le contexte conserve la dernière demande analytique, l'identifiant de l'analyse et celui du rapport avec sa version. L'historique complet reste dans SQLite ; le prompt reçoit le contexte structuré, pas une répétition illimitée des messages. Cela permet de conserver de nombreux échanges sans gonfler le contexte du modèle. Les longues conversations et toutes les références linguistiques possibles restent à évaluer.

`analysis_request()` réutilise les paramètres non remplacés lors d'une relance. « Et pour Marrakech ? » garde l'indicateur et les périodes, puis change la destination. S'il manque un indicateur ou une période obligatoire, aucun calcul n'est lancé et la réponse demande une précision.

`ConversationService.send()` refuse une version obsolète et les conversations d'un autre propriétaire. Une seule opération de conversation est exécutée à la fois ; l'utilisateur reçoit une erreur explicite si le service est occupé. `AppState.save_conversation()` applique aussi une transaction avec contrôle de version.

## Orchestration et révisions

LangGraph organise deux étapes bornées : interpréter, puis exécuter l'outil autorisé. Il n'y a pas de boucle autonome de réflexion ou de mécanisme `eval`. Les opérations affichées sont factuelles.

- Analyse : `AnalyticsService.run()`.
- Rapport : `ReportService.create_report()` à partir de la dernière analyse.
- Révision éditoriale : `ReportService.revise_report()` avec `base_version`.
- Nouveau calcul dans un rapport : calcul Doha, puis `ReportService.recalculate_report()` ; les faits modifiés affectent ici toutes les sections, donc elles sont régénérées et la version augmente.
- Document : `Retriever.search_evidence()`.

Lorsqu'un rapport est créé ou révisé dans l'espace Rapports, `link_context()` synchronise sa référence et sa version avec le chat après vérification des droits. Le contexte lui-même utilise une version de base ; une modification concurrente reste un conflit explicite. L'identifiant de la dernière conversation est mémorisé dans le navigateur, par utilisateur ; les messages et les droits restent sur le serveur et sont revérifiés à la restauration.

Les réponses de statut courtes utilisent des textes contrôlés dans cinq langues. Elles ne sont pas présentées comme de longues réponses rédigées par IA. La qualité de compréhension multilingue et la darija sont évaluées séparément dans le bilan des tests.
