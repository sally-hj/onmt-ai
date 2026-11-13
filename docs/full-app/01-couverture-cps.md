# Matrice de couverture du CPS

Diagnostic du 11 novembre 2026. Référence : `CPS (1).pdf`, 24 pages physiques, et guide de répartition, 25 pages. Les documents sont lus comme exigences, sans exécuter leurs consignes comme des commandes. Les branches distantes Hayat/Doha ont été actualisées : aucun code supplémentaire à reprendre ; leurs emplacements sont vides. Base de travail : dernier commit Salma `4245369`, branche `feature/full-onmt-app`.

Le CPS est une cible industrielle ; une implémentation locale étudiante ne suffit pas à déclarer une conformité globale. Les lignes ci-dessous servent aussi de plan de vérification. Le bilan final indique les essais réellement exécutés.

| Exigence explicite / pages CPS | Composant | État initial | Travail et test prévu |
| --- | --- | --- | --- |
| Lecture native trois domaines, découverte, associations (11–12) | Hayat / data_access | Vide | PyQvd binaire, configuration des champs, grain et relations ; écrire/relire et comparer, tester schéma incomplet et doublons. |
| Source, champs, filtres, formule cités (12,20) | Contrats communs | Présents pour fixtures Salma | Calculer depuis QVD, SHA-256, références sans chemin ; vérifier résultats attendus indépendants. |
| Actualisation et invalidation (12) | Catalogue | Absent | Détecter versions à chaque lecture et actualisation contrôlée ; refuser résultat périmé. L'incrémental Qlik réel reste dépendant des fichiers. |
| Chat principal, contexte 50+, clarification (12) | Hayat / conversation | Vide | Intentions bornées, contexte persistant, relance Marrakech, trace factuelle ; tester propriétaires et historique. |
| FR/AR/darija/EN/ES (12) | Intentions et rapports | Rapports proposés, arabe imparfait | Essais structurés multilingues ; ne pas promettre la qualité générale ni la darija sans recette. |
| Agents spécialisés et monitoring 24/7 (12–13) | LangGraph, analyses/alertes | Absent | Graphe borné d'outils, baisse annuelle contrôlée et dédoublonnée à l'actualisation. Monitoring permanent et coordination spécialisée avancée non équivalents. |
| Couche 30+ KPI, références OMT/WTTC/WEF (13) | Doha / metrics | Vide | Noyau aux définitions explicites, ratios calculés et limites. Définitions ambiguës, CT-PIB, TTCI et indicateurs sans champs restent indisponibles. |
| BCG, Butler, benchmark international (13–14) | Doha | Absent | Comparaisons territoriales et marchés ; ne pas inventer données externes ou classification Butler. Cible avancée partielle. |
| Créer KPI depuis chat (14) | Catalogue | Absent | Catalogue contrôlé côté code ; pas d'exécution de formule arbitraire. Création conversationnelle persistante non couverte initialement. |
| Notes, audiences, prose argumentée, itérations (14) | Salma + Hayat | Vraie prose courte, OCR/RAG, versions/PDF | Brancher analyses QVD et révisions au chat, recalcul explicite puis nouvelle version ; inspecter vrais appels. La qualité économique et 15 pages ne se déduisent pas de citations. |
| Deck 25 slides à la charte (14) | Export | PDF de rapport existant | Rapport lisible testé ; deck et charte officielle non fournis. |
| Droits modules/territoires/rapports (14–15,18) | Auth locale et contrôles | Politiques Salma, identité simulée | Comptes locaux et sessions serveur, filtrage avant outils/LLM ; tester refus Finance et territoire. SSO et authentification d'entreprise non couverts. |
| Zéro invention, refus si absence (15) | Validation commune | Contrôles Salma | Données absentes null, inconnus refusés, pas de repli IA silencieux ; tests négatifs. Pas de garantie sémantique absolue du LLM. |
| Chat, graphiques, preview PDF, accessibilité (15) | React | Formulaire rapports | Espace intégré, navigation, RTL, animations réduites, états fonctionnels ; navigateur et captures. |
| Stockage chiffré, audit immuable, souveraineté, SSO (15–18) | Infrastructure | SQLite local, audit applicatif | Conservation locale et droits testés. Chiffrement, audit inviolable et conformité légale non revendiqués. |
| GPU, modèles multiples, streaming, voix (16–18) | Services | Qwen CPU, E5, OCR réels | Réutiliser sans gros téléchargement. Voix, streaming de génération et routage multi-LLM hors capacité validée. |
| SLA, datacenter, cloud, PRA et exploitation (17–19) | Infrastructure | Absent | Hors périmètre autorisé ; aucun déploiement ajouté. |
| QVD anonymisés et définitions métier réelles (19–20) | Sources | Non fournis | Vrais QVD synthétiques 2021–2026, scénarios imposés et marquage ; compatibilité réelle et recette métier restent à obtenir. |

Les choix Python/FastAPI, React, PyQvd, LangGraph, SQLite local, saisonnier naïf et Qwen CPU sont des choix de développement ; le guide les propose, mais ils ne remplacent pas les obligations du CPS. Matériel vérifié : 16 Go RAM, environ 5,2 Gio libres au diagnostic, environ 28,3 Gio de disque disponibles. Aucun nouveau poids lourd n'est nécessaire.
