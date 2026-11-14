# Résultats des essais locaux — 9 novembre 2026

> **Actualisation du 14 novembre 2026 :** ce bilan conserve les essais du 9 novembre, avant l'intégration des trois modules. Les QVD synthétiques sont désormais les données définitives du rendu ; aucun dataset réel n'est attendu. Consulter le [bilan actuel](full-app/09-resultats.md) et la [matrice réévaluée](full-app/01-couverture-cps.md) pour les fonctions restantes.

Ollama, E5 et Tesseract ont réellement été exécutés sur ce PC Windows. Les documents et les analyses utilisés sont entièrement fictifs. Ces résultats ne constituent pas une recette des modules réels de Doha et Hayat, ni une conformité globale au CPS.

## Contrôles exécutés

| Vérification | Résultat observé |
| --- | --- |
| Régression backend, hors modèles réels | `71 passed, 1 skipped, 4 deselected`, en 27,55 s. Le test navigateur est désactivé par défaut et a été exécuté séparément. |
| Parcours navigateur FastAPI/Vite/Chromium | `1 passed`, en 35,84 s ; données synthétiques, gabarits et embeddings de démonstration explicitement configurés. |
| Interface React | `4 passed` ; API simulée dans ces tests. |
| Compilation TypeScript et Vite | Réussie, 30 modules transformés. |
| Dépendances Python | `pip check` : aucune dépendance déclarée cassée. |
| Cohérence des modifications | `git diff --check` réussi ; seuls des avertissements de conversion LF/CRLF sont affichés. |
| Import et encodage E5 réel | Réussis après réparation des DLL ; vecteurs de 384 dimensions. L'essai E5 isolé a également donné `1 passed`, en 22,35 s. |
| OCR réel multilingue et PDF mixte | Reconnaissance française, anglaise et arabe sur des images ; extraction directe conservée sur la page textuelle, provenance OCR sur les trois pages scannées. |
| Recherche sémantique réelle | Trois questions reformulées retrouvent chacune le document attendu en première position ; question sur le néon sans preuve ; contexte sans accès aux documents sans résultat. |
| Chaîne complète réelle | `1 passed, 2 deselected`, en 188,84 s : scan → Tesseract → E5 → recherche → Ollama → rapport français → traduction ciblée arabe → conflit de version → export PDF. |

Le dernier essai complet utilise `onmt-qwen25:3b` avec les poids officiels Qwen2.5 3B Instruct Q4_K_M et l'API locale `/api/generate`. Le français contient des introductions distinctes pour la période étudiée, la référence historique, la variation et l'extrait documentaire. Le modèle ne fait aucun calcul métier. Le serveur insère les valeurs structurées exactes : notamment `80000 nuitees` et `-20 %`, avec unités, périodes et références.

Les deux essais réels indépendants OCR/recherche ont aussi réussi ensemble lors de la confirmation finale : `2 passed, 1 deselected`, en 56,91 s. Ils tournaient en parallèle avec les autres vérifications locales ; cette durée n'est pas un benchmark isolé.

## Ce que les essais démontrent et leurs limites

- Les vrais appels Ollama ont rédigé la synthèse et sa révision arabe. Les six familles de révision sont vérifiées avec un client simulé ; elles n'ont pas toutes fait l'objet d'une campagne multilingue réelle exhaustive.
- Les erreurs service absent, modèle manquant, délai, chiffres libres, sortie mal formée et altération des faits sont contrôlées dans les tests simulés. Les essais exploratoires ont aussi rencontré de vraies erreurs et sorties refusées. Aucun gabarit n'est présenté comme leur réussite.
- La traduction arabe produit de la prose arabe et un PDF RTL, mais sa qualité métier est insuffisante pour publication : le modèle a notamment traduit des nuitées par une formulation évoquant des journées et mélangé des caractères cyrilliques dans le nom d'Agadir. Les contrôles numériques ne détectent pas toutes les erreurs de sens. Une relecture linguistique est indispensable ; la darija n'est pas validée.
- Les PDF français et arabe ont été produits ; les valeurs sont lisibles par extraction PDF. L'aperçu du PDF arabe a été inspecté visuellement. Les libellés métier, unités et citations d'origine sont conservés et peuvent rester français dans une section arabe. La couverture conserve le titre du rapport.
- Le test OCR arabe vérifie la présence de texte arabe ; il ne mesure pas un taux d'erreur mot à mot. Les tableaux, chiffres incertains, manuscrits et scans dégradés restent à évaluer.
- La recherche sémantique porte sur un petit corpus fictif. Le seuil E5 `0.24` n'est pas un seuil universel validé sur les documents ONMT.
- Les autres sections sont prises en charge par le code, mais l'essai réel complet récent porte sur une synthèse. Il ne constitue pas une validation éditoriale de tous les types de rapports et recommandations.

## Artefacts consultables sur ce poste

Tous restent dans `local_data/real-ai-results/`, hors Git :

- `rapport-fr-modeles-reels.pdf` et `.json` : version française, avant traduction.
- `rapport-reel-modeles-donnees-fictives.pdf` et `.json` : version révisée, quatre pages dans l'essai observé.
- `generation-manifest.json` : modèle, prose générée, paramètres par section et mesures d'inférence.
- `synthetic-llm-trace.json` : réponses brutes du modèle sur les seules données fictives de ce test ; pas de raisonnement privé du modèle.
- `apercu-page-1.png` et `apercu-page-2.png` : rendu de contrôle du PDF arabe.

Ces fichiers sont remplacés au prochain essai réel. Le test peut échouer sans les remplacer tous ; leur seule présence ne prouve donc pas la réussite d'une exécution ultérieure.

## Choix corrigés pendant les essais

Le téléchargement standard Ollama a expiré sur son serveur de fichiers. Le téléchargement officiel Hugging Face puis l'import GGUF local ont permis de continuer sans API payante. Qwen3 1.7B a été écarté après plusieurs réponses non conformes. Les appels structurés `/api/chat` ont rencontré des erreurs de grammaire `peg-native` ; le chemin testé utilise ChatML explicite avec `/api/generate`, sans relais distant et avec échappement des délimiteurs de rôle dans les données.

La première génération techniquement réussie répétait trop un exemple de consigne. Cet exemple JSON a été retiré et le test complet a été relancé avec des introductions distinctes adaptées aux rôles des mesures.

## Reste à connecter ou à valider

Doha : `AnalysisResult` réels, calculs et prévisions métier, autorisations sur ces analyses. Hayat : identité serveur, `AccessContext`, orchestration conversationnelle et demandes de rapports. Les contrats existants et points d'injection sont conservés ; leurs modules complets n'ont pas été développés ici.

Restent aussi la qualité rédactionnelle et linguistique à grande échelle, les documents réels, la charge, la charte officielle et les autres exigences de production du CPS. Aucun push, fusion ou déploiement n'a été effectué.
