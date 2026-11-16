# Bilan d'intégration et résultats observés

> **Version courante :** voir le [bilan du chantier de complétion](14-validation-completion.md) des 15–16 novembre. Les compteurs et durées ci-dessous décrivent les versions antérieures ; la [matrice actuelle](01-couverture-cps.md) indique les fonctionnalités disponibles.

Travaux commencés le 11 novembre 2026, clôture vérifiée le 13 novembre. Branche dédiée : `feature/full-onmt-app`, issue du dernier état Salma `4245369`. Les branches distantes ont été consultées sans être modifiées. Aucun déploiement, Docker, CI/CD, push ou fusion n'est ajouté.

**Actualisation du périmètre, 14 novembre 2026 :** les QVD synthétiques sont désormais les données de référence définitives confirmées par le professeur. Leur remplacement par un patrimoine réel n'est plus une condition de rendu. Les résultats datés ci-dessous restent des preuves d'exécution, pas une validation de toutes les exigences fonctionnelles. La nouvelle [matrice](01-couverture-cps.md) et le [reste à développer](10-perimetre-pedagogique.md) séparent ces sujets.

## Audit du corpus définitif — 14 novembre 2026

- Les trois fichiers déjà présents sous `local_data/qvd-synthetic/` ont été lus avec PyQvd et comparés aux données d'une génération neuve à graine `20261111` : **2 100 lignes identiques par domaine, 6 300 au total**. Les originaux n'ont pas été réécrits. Le compte rendu local est `local_data/pedagogical-audit/verification.json`.
- `test_synthetic_reference.py` : **20 passed en 3,87 s** lors du dernier contrôle. Vérifie format natif, clés/grains des trois domaines, invariants, références imposées, deux générations de même graine, effet d'une autre graine, unités et seize calculs sur l'oracle manuel indépendant. Une clé Finance absente bloque le rapprochement avec Commercial.
- Régression backend finale : **111 passed, 10 deselected en 31,21 s**, hors modèles et navigateur opt-in. Les nombres du bilan d'intégration du 13 novembre plus bas sont conservés comme résultats historiques, pas comme compteur actuel.
- Tests ciblés corpus + rapports : **54 passed en 18,55 s**, dont le marqueur « DONNÉES SYNTHÉTIQUES » extrait d'un vrai PDF français produit avec Chromium ; le drapeau synthétique est aussi vérifié en arabe. Le parcours de rédaction de ces tests utilise explicitement les gabarits, pas un appel LLM simulé présenté comme réel.
- OCR multilingue et recherche E5 : **2 passed, 1 deselected en 88,03 s**. Tesseract et E5 sont réellement exécutés sur les PDF et questions synthétiques ; le long scénario de rédaction est exclu de cette commande.
- Le manifeste enrichi porte schéma v2, version du générateur, statut de référence, colonnes, empreinte binaire et empreinte sémantique. Une graine différente est une variante explicitement marquée, pas une substitution silencieuse de référence.

L'oracle `examples/synthetic-reference.json` contient des entrées et attendus calculés à la main ; il n'est produit ni par le générateur ni par les fonctions analytiques testées. Le fichier `expected.json` généré n'est donc plus la seule source d'attendus. Les tests ci-dessus se recouvrent : ne pas additionner leurs comptes comme des tests distincts.

Les analyses et rapports déjà enregistrés conservent leurs avertissements historiques, comme les anciennes pages de documentation désormais contextualisées. Un nouveau calcul utilise la définition pédagogique actualisée ; il n'est pas nécessaire d'attendre ni de remplacer les QVD. Les instantanés de versions précédentes ne sont pas réécrits pour modifier rétroactivement leur contenu.

Les appels réels Ollama et le parcours complet restent attestés par les essais datés du 13 novembre ci-dessous ; ils n'ont pas été relancés pour ce changement de statut des données. L'audit du 14 novembre ne transforme pas les clients simulés des tests ordinaires en preuves d'inférence réelle.

## Fonctionnement réalisé

- Trois QVD synthétiques natifs, 6 300 lignes au total : historique mensuel 2021–octobre 2026, six destinations et cinq marchés. Chaque fichier est relu et comparé cellule par cellule après sa création.
- Catalogue et mapping centralisés, champs/types/grains/relations contrôlés ; versions liées au contenu et au mapping ; refus des analyses périmées.
- Seize indicateurs définis, comparaisons temporelles, territoriales et par marché ; ratios sur sommes, rapprochement de sources de même grain, prévision naïve/saisonnière avec bloc chronologique d'évaluation.
- Comptes locaux, sessions serveur, droits de modules/territoires/propriétaire ; conversations persistantes et versionnées, relances et outils bornés via LangGraph.
- Analyses réellement calculées depuis QVD branchées dans Salma ; documents texte/scannés, OCR, E5/Chroma, citations, rédaction locale, révisions et PDF.
- Interface chat principale et espaces analyses, rapports, documents, alertes et services ; états vides/erreurs, saisie conservée, mobile, clavier et réduction des animations.

Les données sont fictives. L'exécution de PyQvd, des calculs, de Tesseract, d'E5, d'Ollama et de Chromium est réelle dans les essais indiqués comme tels.

## Vérifications

| Contrôle | Preuve observée |
| --- | --- |
| Backend ordinaire | Contrôle global : `91 passed, 10 deselected` en 30,32 s. Les tests de modèles et navigateur sont explicitement exclus de cette commande. |
| Contrôle rédactionnel supplémentaire | `20 passed` dans `test_narrative.py`, dont les deux nouveaux cas refusant de déduire un nombre de visiteurs depuis les seules nuitées. |
| Dernier contrôle des modules intégrés | `13 passed` dans `test_full_app.py` en 12,97 s : inclut le remplacement d'une colonne réelle dans le mapping, la formule citée et le titre après recalcul. Ces cas sont également dans le noyau ordinaire ; ne pas additionner les comptes. |
| React | `8 passed`, deux fichiers de tests ; API simulée dans ces cas. Comprend l'affichage de deux résultats territoriaux distincts. |
| TypeScript/Vite | Compilation réussie, 37 modules transformés. |
| Navigateur intégré réel | `1 passed` en 15,73 s : compte local, résultat calculé depuis QVD, sources, alertes, saisie conservée, clavier et largeur mobile. |
| Régression navigateur Salma | `1 passed` en 18,10 s, interface legacy et gabarits/embeddings de démonstration explicitement configurés. |
| Contraste échantillonné | Cinq petits textes mesurés dans le navigateur : ratios de 5,02 à 5,36. Ce n'est pas un audit complet d'accessibilité. |
| Chaîne complète avec modèles réels | Scénario QVD → chat → OCR/E5 → rapport français → révision arabe → PDF réussi. La commande groupée du 13 novembre a donné `1 passed, 1 failed` en 623,90 s : l'échec distinct concernait le benchmark décrit et corrigé ci-dessous. |
| Benchmark territorial réel | Après correction : `1 passed, 2 deselected` en 29,99 s. La question au modèle produit deux calculs QVD : 80 000 pour Agadir, 165 000 pour Marrakech. |
| Contrôle sémantique arabe réel | Le cas `test_real_arabic_nights_cannot_claim_arrival_counts` a réussi lors de l'exécution ciblée contenant l'ancien échec du benchmark (`1 passed, 1 failed, 1 deselected`, 168,85 s). Les valeurs sont conservées et l'inférence identifiée sur le nombre de visiteurs est refusée. |
| Ollama réellement arrêté | `1 passed` en 4,21 s : erreur HTTP 503 explicite et bibliothèque de rapports inchangée, sans gabarit de secours. Seul le service démarré pour les essais a été arrêté. |
| Dépendances et cohérence | `pip check` sans dépendance déclarée cassée ; compilation Python et `git diff --check` réussis. Les données, poids, SQLite, PDF et captures sont exclus de Git. |

Le scénario complet importe un vrai PDF mixte fictif, conserve l'origine texte/OCR, calcule de vrais vecteurs E5, interprète réellement les messages avec Ollama, calcule Agadir/Marrakech depuis les QVD, crée le rapport avec preuves documentaires, traduit la synthèse et produit les PDF. Les chiffres attendus sont indépendants : Agadir 80 000 / 100 000 = −20 %, Marrakech 165 000 / 150 000 = +10 %.

Les tests ordinaires vérifient aussi les valeurs nulles, doublons, dates erronées, unités incompatibles, Qlik dual/numéro de date, absence de double comptage, seuils et dédoublonnage des alertes, accès Finance/territoires interdits, propriété des ressources et conflits de versions. Le mécanisme de recalcul de rapport est testé avec un interpréteur simulé ; la chaîne de rédaction réelle est vérifiée séparément.

## Essai linguistique ciblé

L'appel réel à Qwen est suivi de l'ancrage déterministe des dates et filtres. Une question de référence par langue a été contrôlée, y compris l'absence de filtre de marché non demandé :

| Langue | Paramètres de référence | Temps observé |
| --- | --- | --- |
| Français | Vérifiés dans le scénario intégré, puis relance Marrakech | Compris dans la durée globale. |
| Anglais | Correspondance complète du cas testé | 44,61 s |
| Espagnol | Correspondance complète du cas testé | 23,70 s |
| Arabe classique | Correspondance complète du cas testé | 25,55 s |
| Darija | Correspondance complète du cas testé | 43,77 s |

Il ne s'agit pas d'une mesure de qualité générale : un exemple par langue, un petit catalogue et des paramètres explicitement écrits ne valident pas toutes les demandes libres. Les réponses de statut sont des textes contrôlés dans la langue sélectionnée. Seules les rédactions française/arabe du scénario de rapport ont fait l'objet des essais de génération décrits ici.

## Problèmes réellement rencontrés et corrections

Le modèle a omis des dates, proposé une consigne de traduction non canonique, ajouté un marché « France » non demandé, produit des variables minuscules et parlé du serveur dans une clôture. L'examen des réponses brutes et des PDF a conduit à renforcer les ancrages et validations, puis à relancer les essais. Une sortie JSON correcte n'a pas été considérée comme une preuve de qualité.

Le benchmark réel a aussi montré que le modèle pouvait placer « Marrakech » dans le champ marché. Il produisait alors des valeurs nulles, et le test indépendant a échoué. Le contrôle des dimensions refuse désormais ce mauvais typage ; l'essai isolé a ensuite réussi avec les valeurs QVD attendues. Les sorties de ces essais restent consultables dans `benchmark-intent.json` et `benchmark-synthetique.json` sous le dossier local d'artefacts.

La prose arabe reste moins fiable. Une clôture déduisait une hausse des visiteurs d'une hausse des nuitées : cette inférence identifiée est maintenant refusée lorsque le résultat d'arrivées n'est pas fourni. Ces contrôles ciblés ne détectent pas toutes les affirmations non justifiées ; relecture linguistique et métier toujours nécessaire. Aucun repli silencieux vers un gabarit n'est présenté comme une réussite IA.

## Couverture du CPS

| État | Périmètre |
| --- | --- |
| Opérationnel et vérifié sur corpus synthétique | Lecture native, contrôles de grain, calculs du noyau, filtres/droits locaux, contexte et relance de référence, documents/OCR, recherche, rapports versionnés et PDF, alertes à l'actualisation, interface intégrée. |
| Partiel | Découverte de schéma avec mapping/relations configurés ; compréhension multilingue et ancrage hybride ; prose analytique courte, qualité arabe ; prévisions simples ; benchmarks internes ; sécurité et audit applicatifs locaux. |
| Fonctions restant à développer ou à valider | Catalogue au-delà des 16 KPI, BCG/Butler et comparateurs synthétiques étrangers, KPI via chat, agents spécialisés, conversations longues, rapports/itérations avancés, deck, voix/streaming, sécurité et audit applicatifs. Leur absence ne devient pas une dispense liée aux données. |
| Cible industrielle distincte | QVD de production non requis pour ce rendu ; compatibilité future facultative. Datacenter/GPU industriels, PRA, déploiement et SLA d'exploitation hors livraison locale ; SSO d'entreprise non fourni. Les adaptations pédagogiques de sécurité restent à expliciter. |

Le modèle CPU Qwen2.5 3B et ce PC 16 Go ne sont pas assimilés à l'infrastructure GPU du CPS. Les durées observées se comptent en minutes pour un rapport ; aucune conformité au délai industriel n'est revendiquée.

## Artefacts et reproduction

Sous `local_data/full-app-results/`, hors Git : conversation synthétique, réponses éditoriales, corpus PDF fictif, rapports français/arabe, captures desktop/mobile, mesures de contraste et évaluation des langues. Les fichiers sont remplacés lors des essais suivants ; leur simple présence ne prouve pas la réussite d'une nouvelle exécution.

Le PDF `rapport-ar-controle-semantique.pdf` correspond au contrôle arabe renforcé, distinct du PDF de la chaîne principale. Les refus du modèle restent possibles sur d'autres formulations : ces réussites vérifient les scénarios indiqués, pas toutes les sorties futures ni la qualité professionnelle générale.

La [procédure de lancement et les commandes de test](08-utilisation.md) permettent de reproduire les essais. Lire le [guide pédagogique](README.md), puis l'[inventaire des fichiers](fichiers/README.md). La [matrice détaillée du CPS](01-couverture-cps.md) conserve la distinction entre exigences explicites, choix étudiants et limites.

## Commits d'intégration du 13 novembre

- `5d1dedd` — modules QVD, analyses, conversation, accès locaux, contrôles et tests.
- `aadfbdb` — interface conversationnelle intégrée, graphiques, espaces complémentaires et tests React.
- `4996c65` — documentation d'intégration et inventaire pédagogique. L'actualisation du 14 novembre ajoute le contrat de données définitif, le nouvel oracle et l'audit ; consulter `git log -4 --oneline` pour la référence de cette actualisation.

Aucun commit ne contient les QVD, bases locales, rapports ou poids. Les serveurs lancés temporairement pour les essais ont été arrêtés ; les trois commandes du guide permettent un démarrage normal dans vos terminaux.
