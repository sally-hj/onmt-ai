# Catalogue et conventions de calcul

Les 46 définitions ci-dessous sont distinctes : ni traductions, ni filtres comptés comme nouveaux KPI. Les exemples proviennent des attendus manuels versionnés des tests et de `examples/synthetic-reference.json`, sans appeler le moteur de calcul pour produire la réponse attendue.

Le minijeu indépendant comporte deux marchés à Agadir : 100 nuitées, 25 arrivées, 200 sièges, 2 000 MAD de budget, 1 000 MAD exécutés, 1 500 MAD engagés, 20 000 MAD de recettes, 6 000 MAD de chambres, 40 chambres-nuits vendues sur 100 disponibles, 2 000 impressions et 100 clics. Les compléments manuels et piliers sont détaillés dans `test_extended_analytics.py`. Ce minijeu diffère du corpus volumineux.

Règles communes : grain mensuel/destination/marché ; dimensions et droits appliqués avant calcul. Les sommes portent sur les lignes du périmètre ; un ratio agrège d’abord numérateur/dénominateur. Une source invalide bloque le calcul. Une période sans ligne ou un dénominateur nul donne `null`, jamais un zéro inventé. Les métriques temporelles requièrent les historiques complets décrits ci-dessous.

| Identifiant / définition | Formule | Champs requis | Unité | Agrégation | Attendu manuel |
| --- | --- | --- | --- | --- | --- |
| `overnight_stays` — Nuitées | `SUM(overnight_stays)` | commercial: overnight_stays | nuitees | sum | 100 |
| `arrivals` — Arrivées touristiques | `SUM(arrivals)` | commercial: arrivals | arrivees | sum | 25 |
| `seats` — Sièges aériens disponibles | `SUM(seats)` | commercial: seats | sieges | sum | 200 |
| `bookings` — Réservations | `SUM(bookings)` | commercial: bookings | reservations | sum | 20 |
| `budget` — Budget prévu | `SUM(budget)` | finance: budget | MAD | sum | 2000 |
| `spent` — Dépenses exécutées | `SUM(spent)` | finance: spent | MAD | sum | 1000 |
| `committed` — Engagements | `SUM(committed)` | finance: committed | MAD | sum | 1500 |
| `travel_receipts` — Recettes voyages | `SUM(travel_receipts)` | performance: travel_receipts | MAD | sum | 20000 |
| `room_revenue` — Recettes des chambres | `SUM(room_revenue)` | performance: room_revenue | MAD | sum | 6000 |
| `average_stay` — Durée moyenne de séjour | `SUM(overnight_stays) / SUM(arrivals)` | commercial: overnight_stays, arrivals | nuits/arrivee | ratio | 4 |
| `occupancy` — Taux d’occupation des chambres | `100 * SUM(rooms_sold) / SUM(rooms_available)` | performance: rooms_sold, rooms_available | % | percent | 40 |
| `revpar` — Revenu par chambre disponible | `SUM(room_revenue) / SUM(rooms_available)` | performance: room_revenue, rooms_available | MAD/chambre-nuit | ratio | 60 |
| `average_room_price` — Prix moyen par chambre vendue | `SUM(room_revenue) / SUM(rooms_sold)` | performance: room_revenue, rooms_sold | MAD/chambre-nuit | ratio | 150 |
| `budget_execution` — Taux d’exécution budgétaire | `100 * SUM(spent) / SUM(budget)` | finance: spent, budget | % | percent | 50 |
| `click_rate` — Taux de clic | `100 * SUM(clicks) / SUM(impressions)` | performance: clicks, impressions | % | percent | 5 |
| `spend_per_night` — Dépenses promotionnelles par nuitée | `SUM(spent) / SUM(overnight_stays)` | finance: spent ; commercial: overnight_stays | MAD/nuitee | ratio | 10 |
| `receipts_per_arrival` — DMT — Recettes par arrivée | `SUM(travel_receipts) / SUM(arrivals)` | performance: travel_receipts ; commercial: arrivals | MAD/arrivee | ratio | 800 |
| `receipts_per_night` — DMN — Recettes par nuitée | `SUM(travel_receipts) / SUM(overnight_stays)` | performance: travel_receipts ; commercial: overnight_stays | MAD/nuitee | ratio | 200 |
| `spend_per_arrival` — Dépenses promotionnelles par arrivée | `SUM(spent) / SUM(arrivals)` | finance: spent ; commercial: arrivals | MAD/arrivee | ratio | 40 |
| `commitment_rate` — Taux d’engagement | `100 * SUM(committed) / SUM(budget)` | finance: committed, budget | % | percent | 75 |
| `budget_remaining` — Crédits non exécutés | `SUM(budget) - SUM(spent)` | finance: budget, spent | MAD | difference | 1000 |
| `commitments_unpaid` — Engagements non exécutés | `SUM(committed) - SUM(spent)` | finance: committed, spent | MAD | difference | 500 |
| `impressions` — Impressions publicitaires | `SUM(impressions)` | performance: impressions | impressions | sum | 2000 |
| `clicks` — Clics publicitaires | `SUM(clicks)` | performance: clicks | clics | sum | 100 |
| `cost_per_click` — Coût par clic | `SUM(spent) / SUM(clicks)` | finance: spent ; performance: clicks | MAD/clic | ratio | 10 |
| `cost_per_thousand` — Coût de mille impressions | `1000 * SUM(spent) / SUM(impressions)` | finance: spent ; performance: impressions | MAD/1000 impressions | per_thousand | 500 |
| `rooms_available` — Capacité disponible | `SUM(rooms_available)` | performance: rooms_available | chambres-nuits | sum | 100 |
| `rooms_sold` — Chambres-nuits vendues | `SUM(rooms_sold)` | performance: rooms_sold | chambres-nuits | sum | 40 |
| `international_arrivals` — ATI — Arrivées internationales | `SUM(arrivals WHERE market != Maroc)` | commercial: arrivals | arrivees | international | 25 |
| `market_concentration` — ICME — Concentration des marchés émetteurs | `10000 * SUM((arrivals_market / arrivals_total)^2)` | commercial: arrivals | indice 0-10000 | hhi | 5200 |
| `market_diversification` — IDT — Diversification des marchés | `1 - SUM((arrivals_market / arrivals_total)^2)` | commercial: arrivals | indice 0-1 | diversification | 0.48 |
| `tourism_gini` — CGT — Inégalité territoriale des nuitées | `SUM_i SUM_j ABS(nights_i - nights_j) / (2 * n * SUM(nights))` | commercial: overnight_stays | indice 0-1 | gini | 0 |
| `seasonality` — ISM — Coefficient de variation mensuel | `100 * STDDEV_POP(monthly_nights) / MEAN(monthly_nights)` | commercial: overnight_stays | % | seasonality | null sur un mois isolé |
| `annual_growth` — TCA — Croissance des arrivées entre années complètes | `100 * (arrivals_last_year / arrivals_previous_year - 1)` | commercial: arrivals | % | annual_growth | null sur un mois isolé |
| `annual_cagr` — TCAM — Croissance annuelle moyenne des arrivées | `100 * ((arrivals_last_year / arrivals_first_year)^(1/years_elapsed) - 1)` | commercial: arrivals | % | cagr | null sur un mois isolé |
| `conversions` — Conversions attribuées fictives | `SUM(conversions)` | extension: conversions | conversions | sum | 5 |
| `campaign_conversion` — ECT — Conversion des clics | `100 * SUM(conversions) / SUM(clicks)` | extension: conversions ; performance: clicks | % | percent | 5 |
| `event_attendance` — Fréquentation événementielle | `SUM(event_attendance)` | extension: event_attendance | entrees | sum | 30 |
| `event_fill` — SFE — Remplissage événementiel | `100 * SUM(event_attendance) / SUM(event_capacity)` | extension: event_attendance, event_capacity | % | percent | 50 |
| `tourism_gdp_share` — CT-PIB — Part de valeur ajoutée touristique | `100 * SUM(tourism_gva) / SUM(gdp)` | extension: tourism_gva, gdp | % | percent | 10 |
| `employment_share` — Part d’emploi touristique | `100 * SUM(tourism_jobs) / SUM(total_jobs)` | extension: tourism_jobs, total_jobs | % | percent | 20 |
| `web_conversion` — Conversion des visites web | `100 * SUM(conversions) / SUM(web_visits)` | extension: conversions, web_visits | % | percent | 5 |
| `marketing_visibility` — SVM — Engagements pour mille impressions | `1000 * SUM(engagements) / SUM(impressions)` | extension: engagements ; performance: impressions | engagements/1000 impressions | per_thousand | 10 |
| `campaign_roi` — IRT — Marge attribuée moins coût, sur coût | `100 * (SUM(attributed_margin) - SUM(spent)) / SUM(spent)` | extension_finance: attributed_margin ; finance: spent | % | roi | 20 |
| `regional_performance` — IPR — Score pédagogique de pilotage territorial | `100 * (0.5 * (SUM(arrivals)/SUM(seats))/0.65 + 0.3 * (SUM(spent)/SUM(budget))/0.80 + 0.2 * (SUM(clicks)/SUM(impressions))/0.03)` | commercial: arrivals, seats ; finance: spent, budget ; performance: clicks, impressions | score base 100 | regional_index | 61.6987 |
| `ttci2019_pedagogical` — TTCI 2019 — Agrégation de piliers synthétiques | `WEIGHTED_MEAN_BY(arrivals, MEAN(MEAN(pillars_1_5), MEAN(pillars_6_9), MEAN(pillars_10_12), MEAN(pillars_13_14)))` | competitiveness: business_environment, safety, health, human_resources, ict, tourism_priority, openness, price_competitiveness, sustainability, air_infrastructure, ground_infrastructure, tourism_services, natural_resources, cultural_resources ; commercial: arrivals | score 1-7 | ttci | 4.2 |

## Limites et exigences d’historique

- ATI exclut le marché domestique Maroc. Les autres arrivées et recettes sont les grandeurs fictives définies dans le corpus, sans attribution automatique à une statistique officielle.
- TCA/TCAM utilisent au moins deux années complètes ; le TCAM applique le nombre d’années écoulées. Sur trois années à 10, 12 puis 14,4 arrivées par mois, les deux attendus sont 20 %. ISM demande douze mois consécutifs ; un historique mensuel plat donne 0 %.
- HHI : parts d’arrivées par marché, échelle 0–10 000 ; IDT = complément sur 0–1. Le marché domestique est inclus s’il appartient au périmètre. Gini : distribution des nuitées entre destinations autorisées ; un filtre change l’univers de l’indice.
- IPR : score pédagogique sur trois ratios et cibles explicites (sièges 65 %, exécution 80 %, clics 3 %), poids 50/30/20. Ce choix de conception n’est pas attribué à un référentiel officiel.
- ROI/IRT : marge attribuée par scénario, coût promotionnel et périmètres de même grain. Il ne démontre aucune incrémentalité ni cause économique.
- TTCI : agrégation de quatorze piliers fictifs déjà normalisés en quatre groupes de 5/4/3/2, puis moyenne des quatre groupes. La pondération par arrivées pour les périodes/destinations est une convention du projet. Les indicateurs bruts du WEF ne sont pas reconstitués. Le résultat n’est ni un classement officiel ni le TTDI actuel. [Méthode historique, annexe B](https://www3.weforum.org/docs/WEF_TTCR_2019.pdf), [méthode TTDI 2026 distincte](https://www.weforum.org/publications/travel-tourism-development-index-2026/technical-notes-and-methodology).
- Les prévisions comparent naïf et saisonnier sur les douze derniers mois réservés à l’évaluation. Au-delà de douze mois, la répétition de profil jusqu’à soixante mois est un scénario mécanique non calibré pour 2030. Les bandes empiriques ne garantissent aucune couverture.

## KPI personnalisés

La DSL autorise deux sommes de champs déclarés, éventuellement filtrées par un marché, et une opération ratio/pourcentage/différence. Les unités sont vérifiées ; les scores non additifs sont refusés. La proposition montre la formule, l’interprétation et l’exemple calculé. Une confirmation explicite enregistre auteur et version. Les droits, le périmètre de l’exemple et ses versions de sources sont contrôlés à nouveau. Aucun Python/SQL/expression arbitraire n’est exécuté.

Les définitions actives peuvent être réutilisées par les utilisateurs autorisés aux sources ; seule une personne autorisée peut enregistrer une définition. Les résultats antérieurs sont invalidés si la définition change. Les seuils de qualité et conventions restent des choix pédagogiques à distinguer des obligations fonctionnelles du CPS.
