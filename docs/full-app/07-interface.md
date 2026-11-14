# Une interface organisée autour de la conversation

L'interface complète remplace la page de formulaire comme accueil. L'ancienne page Salma est conservée pour compatibilité et ses tests, sous `/?legacy=1` ; elle n'est pas le parcours principal.

## Direction visuelle

La palette associe vert profond, ivoire, sauge et terre cuite. La typographie utilise les polices système pour les commandes et Georgia pour les titres. Elle ne télécharge aucune police. Les courbes et motifs évoquent une arcade ; ils ne représentent pas des données. Tous les graphiques analytiques utilisent les valeurs retournées par l'API.

Les animations servent à l'apparition des messages, aux états occupés et au retour des boutons. Une préférence `prefers-reduced-motion` les désactive. Aucun pourcentage de progression artificiel n'est affiché : le statut décrit le traitement en cours sans estimer sa fin.

## Espaces fonctionnels

- Conversation : exemples qui remplissent réellement la saisie, questions, relances, résultats, références, opérations et accès au rapport.
- Analyses : résultats calculés, graphiques SVG, valeurs, périodes, filtres, formule, avertissements et création d'une synthèse.
- Rapports : bibliothèque, lecture, actions de révision, aperçu PDF protégé et téléchargement.
- Documents : import et nouvelle version d'un PDF, catalogue, consultation de l'original et recherche des passages.
- Alertes : baisses annuelles réellement calculées à l'actualisation ; source et règle consultables.
- Sources et services : schéma découvert, champs logiques/physiques, unités, grain, relations et disponibilité observée d'Ollama/Tesseract.

Les comptes ne choisissent pas leurs droits dans l'interface. Le sélecteur de langue règle la conversation ; il ne traduit pas tout le menu. Les textes des messages et sections utilisent une direction automatique ; le PDF applique le RTL par section.

## État et erreurs

`Workspace` conserve saisie, conversation, version, analyses et rapports sélectionnés. Une erreur de génération laisse la question intacte. Le dernier identifiant de conversation est conservé par compte dans le navigateur ; le serveur doit autoriser sa restauration avant de retourner les messages.

La saisie envoie avec Entrée, garde Maj+Entrée pour un retour à la ligne et respecte la composition de caractères. Les liens d'évitement, libellés, focus visibles et éléments natifs permettent l'utilisation au clavier. Les versions mobiles replient la navigation et évitent un débordement horizontal.

Ces dispositions ne constituent pas une certification d'accessibilité. Les essais navigateur et contrastes vérifiés sont détaillés dans le bilan ; une recette avec utilisateurs et lecteurs d'écran reste à faire.

Les noms des composants et leurs entrées figurent dans l'inventaire. Les petits gestionnaires React ne font pas de calcul métier ; le serveur reste l'autorité des chiffres et des droits.
