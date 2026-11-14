# Explication fichier par fichier

Cet inventaire couvre les sources de l'application complète, y compris les composants Salma nécessaires au parcours. Les bibliothèques externes, `.venv`, `node_modules`, poids et caches sont exclus.

- [Composants communs, contrats et montage](commun.md).
- [QVD, calculs, prévisions et alertes](donnees-analyses.md).
- [Conversation et contexte](conversation.md).
- [Documents, recherche, rédaction et PDF](rapports.md).
- [Interface React et ses appels](interface.md).
- [Tests, configurations, scripts et fichiers générés](outils-tests.md).

Pour les modules Python, les signatures et champs sont extraits du code. Chaque entrée explique son rôle, un exemple et les imports statiques. Les appels indirects par injection sont expliqués dans le [parcours guidé](../02-vue-ensemble.md). Le script `scripts/build-code-guide.py` permet de mettre à jour ces signatures après une modification ; les explications métier restent à relire.
