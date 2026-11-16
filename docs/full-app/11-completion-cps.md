# Complétion locale du CPS

État initial vérifié le 15 novembre 2026 : `main`, commit `51fe630`, arbre propre.
Branche de réalisation : `feature/cps-completion`. Les QVD de référence sont conservés.
Les pages ci-dessous désignent le CPS fourni (24 pages), relu dans son extraction locale.

Cette matrice sépare les obligations du CPS des conventions nécessaires au corpus
synthétique. Elle sera complétée avec les preuves de la nouvelle version. Les 111 tests
du 14 novembre et l'essai de 188,84 s du 9 novembre sont historiques.

| Exigence et référence | État initial constaté | Fichiers concernés | Réalisation / critère d'acceptation |
| --- | --- | --- | --- |
| 30+ KPI, acronymes, formules (p.13) | 16 définitions, sommes/ratios | analytics/metrics.py, service.py, data_access, config | Catalogue étendu, définitions précises, données complémentaires, attendus manuels indépendants ; indices composites pédagogiques sans homologation revendiquée. |
| KPI conversationnel persistant (p.14) | Absent | analytics, conversation, core/state.py, interface | Proposition structurée, exemple, confirmation explicite, auteur/version, droits sources, opérations bornées. |
| BCG, Valeur–Volume, Butler (p.13) | Absents | analytics, données complémentaires, interface | Croissance du marché et part relative, valeur/volume définis, Butler prudent et indéterminé possible. |
| Benchmark Maroc/Tunisie/Espagne/Dubaï/Thaïlande/Rwanda, 10+ KPI (p.13–14) | Comparaison interne seulement | analytics, données complémentaires | Définitions/unités/périodes comparables, classement fictif clairement marqué ; aucune conversion implicite. |
| Graphiques/cartes interactifs (p.15) | SVG simples | frontend/features/workspace | Filtres, info-bulles, séries, clavier/mobile ; géographie réelle sourcée, indicateurs fictifs. |
| Agents Marchés/Saisonnalité/Budget/Territorial/COMEX (p.12–13) | Graphe interpréter/exécuter | conversation/graph.py, service.py | Décisions spécialisées, outils autorisés, échanges structurés et traces de tâches, sources et résultats ; aucun raisonnement interne affiché. |
| Contexte 50+ échanges, 20 questions liées (p.12) | Relance Agadir/Marrakech | conversation, tests | Séquences avec changements de période/langue/marché, ambiguïtés, erreurs, reprise persistante ; simulations et modèles réels distingués. |
| RAG durable (p.16) ; enrichissement demandé par l'utilisateur | Persistance E5/Chroma et documents privés existants | reports/ingestion.py, retrieval.py, service.py, scripts | Corpus fictif initial idempotent, bibliothèque partagée explicite, métadonnées, recherche avec contexte, citations vérifiables et ACL avant classement. |
| Notes longues, audiences, scénarios, 5 révisions (p.14,19–20) | Notes courtes, versions | reports, conversation | Sections analytiques enrichies, ajouts sans perte, propositions liées aux preuves, brouillon arabe/darija à relire. |
| Présentation PDF 25 slides (p.14) | Absente | reports/export.py, templates, router, interface | 25 diapositives distinctes, analyses sélectionnées, graphiques/sources/limites, rendu local vérifié. Le CPS demande PDF ; PowerPoint est un choix facultatif. |
| Monitoring périodique et alerte sans requête (p.12,16,20) | Bouton actualiser uniquement | analytics/anomalies.py, core, main.py | Boucle locale configurable, état persistant, erreurs, dédoublonnage, contrôle des arrivées allemandes et nuitées ; pas de promesse 24/7. |
| Audit immuable et accès (p.15–18) | Tables SQLite ordinaires | core, reports/storage.py, main.py | Journal enrichi, chaîne d'empreintes et vérificateur ; limites face au contrôle total du disque explicites. Immutabilité industrielle reste non démontrée. |
| Latences : découverte <2 min, refresh <5 min, benchmark <10 s, note <1 min (p.11–14,20) | CPU, rapports de plusieurs minutes | instrumentation, tâches, scripts | Mesures par étape avec environnement/répétitions ; tâches longues bornées, erreurs et annulation ; aucun SLA déduit d'un essai. |
| Installation simplifiée (demande utilisateur) | Plusieurs requirements et listes initiales inutilisées | requirements, scripts, README | Un point d'entrée direct et un relevé transitif, usages vérifiés ; service Ollama/poids/OCR/Chromium séparés. |
| FR/AR/darija/EN/ES (p.12) | Évaluation minimale | corpus d'évaluation, glossaire, scripts/tests | Jeux développement/évaluation distincts, résultats par langue/tâche, vérifications automatiques séparées de la relecture humaine indisponible. |

Le CPS cite aussi voix, streaming, plusieurs modèles, SSO, chiffrement, charge à 50
utilisateurs et infrastructure souveraine. Aucun de ces critères ne devient acquis par
l'emploi de données synthétiques. Déploiement/cloud/Docker/CI sont exclus par la demande
utilisateur ; les protections et fonctionnalités locales restent à examiner.
# Statut de ce document

Cette matrice conserve le diagnostic **avant** le chantier. Voir la [matrice actuelle](01-couverture-cps.md), le [bilan exécuté](14-validation-completion.md) et le [guide des fichiers](13-fichiers-et-pipeline.md) pour l'état livré.

