# Périmètre pédagogique et travail restant

État du 16 novembre 2026. Les QVD synthétiques natifs constituent la référence définitive. Aucune réception de données réelles n'est nécessaire. Les trois originaux sont préservés ; les compléments restent séparés et reproductibles. Configurer d'autres QVD est une extension facultative.

Les écarts précédents « 16 KPI », « graphe à deux nœuds », « pas de BCG/Butler/KPI personnalisé/deck », « alertes seulement à l'actualisation » ne décrivent plus le code courant. Voir la [matrice actuelle](01-couverture-cps.md), le [catalogue](12-catalogue-et-conventions.md) et le [bilan](14-validation-completion.md).

| Travail restant | État précis / validation utile |
| --- | --- |
| Qualité multilingue | Relecture humaine arabe/darija et campagne complète des cas tenus à part. Une intention correcte ne valide pas la rédaction économique. |
| Conversation entièrement réelle de 50+ tours | Les 60 tours actuels éprouvent contexte et outils avec interpréteur simulé. Une campagne Ollama de même ampleur, avec cinq révisions, reste distincte. |
| Interprétation métier | Seuils, IPR, attribution de marge et piliers TTCI sont des conventions fictives transparentes. Butler indique son incertitude ; poursuivre la grille humaine de qualité. |
| Prévision économique | La projection saisonnière sur cinq ans reste mécanique, sans exogènes ni preuve de causalité. |
| Délais et robustesse rédactionnelle | Les sorties non conformes sont refusées ; l'inférence sur CPU peut durer plusieurs minutes ou échouer. Aucun SLA inférieur à une minute démontré. |
| Voix, streaming, routage multi-modèles | Fonctions CPS non réalisées. La décision sur les données ne réduit pas automatiquement ces exigences. |
| Accessibilité et charge | Clavier/mobile/contrastes échantillonnés disponibles ; lecteurs d'écran, volumes et 50 utilisateurs restent à éprouver. |
| Sécurité industrielle | Comptes locaux et audit chaîné utiles ; SSO, chiffrement et WORM absents. Une ancre externe et un stockage séparé seraient nécessaires contre un administrateur du disque. Rétention industrielle de 30 jours non certifiée. |
| Exploitation permanente | La boucle d'alertes fonctionne backend et ordinateur actifs ; ni disponibilité 24/7, ni PRA, ni envoi externe garantis. |

Les calculs, OCR, embeddings, recherche, génération et exports sont réels dans les essais identifiés comme tels. Les interpréteurs simulés et gabarits sont signalés. Le marquage synthétique reste visible dans l'interface et les exports.

Datacenter, GPU industriel, cloud, Docker et CI/CD sont hors périmètre local du chantier. Cette limite d'infrastructure ne supprime pas les écarts fonctionnels ci-dessus. Aucune conformité intégrale au CPS n'est revendiquée.
