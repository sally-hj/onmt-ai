"""Construire le catalogue documenté et l'inventaire pédagogique des fichiers modifiés."""
import ast
import json
import subprocess
from pathlib import Path
from app.analytics.metrics import METRICS

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/full-app'

ROLES={
 'analytics/metrics.py':('Définit les 46 indicateurs et leurs réducteurs autorisés.','lignes QVD et définition','valeur calculée, unité et formule','AnalyticsService et catalogue API'),
 'analytics/custom.py':('Contrôle la proposition et la confirmation des KPI personnalisés.','deux termes structurés, opération, droits','brouillon avec exemple ou définition active versionnée','SQLite et AnalyticsService ; aucun code arbitraire'),
 'analytics/diagnostics.py':('Calcule BCG, Valeur–Volume, Butler, cartes et scénarios.','périodes, filtres, seuils et droits','résultat structuré avec hypothèses, unités et sources','catalogues QVD internes et comparateurs'),
 'analytics/products.py':('Conserve les diagnostics privés et refuse leur réemploi si sources/droits changent.','diagnostic et propriétaire','identifiant persistant ou refus','SQLite, analyses, rapports et exports'),
 'analytics/service.py':('Lit les sources autorisées, agrège et conserve des analyses réutilisables.','AnalysisRequest et droits','AnalysisResult','catalogue, métriques, projections et rapports'),
 'analytics/forecasting.py':('Compare deux références de projection sur un bloc chronologique.','historique mensuel et horizon','points projetés, erreurs et limites','AnalyticsService ; horizon long signalé comme mécanique'),
 'analytics/anomalies.py':('Détecte les baisses annuelles et dédoublonne les alertes.','données Commercial autorisées','alertes et trace de vérification','surveillance périodique et bouton actualiser'),
 'analytics/quality.py':('Bloque les données invalides et les scores hors échelle.','lignes et conventions de source','liste d’erreurs','Catalog avant calcul'),
 'analytics/router.py':('Expose sources, KPI, analyses, diagnostics, alertes et état des services.','requêtes HTTP validées et session','JSON calculé ou erreur','services analytiques et audit'),
 'data_access/supplement.py':('Ajoute les QVD complémentaires sans réécrire les trois références.','QVD existants et règles déterministes','compléments relus et manifestes','configuration étendue, comparateurs et tests'),
 'data_access/qvd_reader.py':('Lit les QVD natifs et réapplique les droits, même dans le cache.','source, filtres et droits','lignes autorisées et empreinte','Catalog ; cache borné et contrôle de modification'),
 'core/state.py':('Conserve l’état applicatif local.','analyses, contextes et états','enregistrements SQLite','authentification, conversation et outils'),
 'core/audit.py':('Ajoute et vérifie des événements chaînés.','acteur, action, ressource, versions','empreinte et verdict d’intégrité','audit des requêtes, outils et documents ; ancre externe facultative'),
 'core/jobs.py':('Gère la file de tâches, l’idempotence et l’annulation entre étapes.','propriétaire, clé et traitement','état persistant, étapes, résultat ou erreur','routes conversation/rapports et worker unique'),
 'core/monitor.py':('Vérifie périodiquement les sources lorsque l’API est active.','intervalle et comptes autorisés','alertes, dernière réussite ou erreur','cycle de vie FastAPI et AlertService'),
 'core/timing.py':('Mesure les étapes réellement exécutées.','fonction décorée','durée et état','traces des tâches et mesures ; aucun pourcentage inventé'),
 'core/config.py':('Lit les chemins et paramètres locaux.','variables d’environnement','Settings validés','API, modèles, QVD, OCR et surveillance'),
 'core/security.py':('Applique les politiques privées et de bibliothèque partagée.','ressource et droits serveur','autorisation ou refus','documents et rapports ; migration conservatrice des imports anciens'),
 'core/llm_client.py':('Appelle le service Ollama local par HTTPX et contrôle ses réponses.','schéma JSON, consignes et données','texte réellement généré et mesures','planification et rédaction ; erreurs explicites, aucun repli simulé'),
 'conversation/intent.py':('Demande à Qwen une intention structurée.','question, contexte et catalogue autorisé','Intent validé puis ancré','client Ollama, dates/dimensions et orchestration'),
 'conversation/slots.py':('Ancre dates, dimensions et relances explicites.','intention, texte et contexte','paramètres contrôlés','interprétation hybride ; ne calcule pas les KPI'),
 'conversation/context.py':('Fusionne une relance avec la dernière demande, y compris suppression de filtres.','Intent et contexte','AnalysisRequest ou besoin de précision','service de conversation'),
 'conversation/agents.py':('Implémente les décisions et transmissions des spécialistes.','demande, droits, résultats précédents','analyses, décision de contrôle budgétaire, preuves et traces','outils autorisés QVD/RAG/rapports ; pas de raisonnement interne publié'),
 'conversation/graph.py':('Relie les spécialistes avec des chemins conditionnels bornés.','tour structuré','réponse contrôlée','LangGraph et Specialists'),
 'conversation/service.py':('Exécute le tour, conserve le contexte et réévalue les droits en relecture.','message et session serveur','réponse et nouvelle version de conversation','calculs, KPI, diagnostics, rapports et présentation'),
 'conversation/router.py':('Expose conversations et tâches avec propriété contrôlée.','messages ou identifiants','JSON de contexte, tâche ou réponse','ConversationService et Jobs'),
 'reports/documents.py':('Définit métadonnées, passages et preuves documentaires.','données typées d’import','documents et références versionnés','ingestion, recherche et citations'),
 'reports/ingestion.py':('Importe les PDF et conserve leur état d’indexation.','PDF et métadonnées autorisés','document, passages et vecteurs','pdfplumber, Tesseract, E5, Chroma et SQLite'),
 'reports/retrieval.py':('Recherche après filtrage des droits et du contexte.','question, période, indicateurs et droits','passages/pages/versions ou absence de preuve','E5 produit les vecteurs ; Chroma classe les candidats'),
 'reports/library.py':('Prépare et réindexe le corpus partagé de façon explicite et idempotente.','corpus versionné et compte autorisé','documents indexés ou inchangés','registre SQLite ; les imports privés restent privés'),
 'reports/narrative.py':('Fait rédiger la prose puis insère et vérifie les faits et citations.','analyses, preuves, langue et audience','section et manifeste de génération','Qwen ; chiffres libres, incohérences et alphabets inattendus sont contrôlés'),
 'reports/actions.py':('Propose des vérifications opérationnelles liées aux constats.','analyses calculées et langue','propositions avec condition et référence','rapport, interface et exports ; validation humaine requise'),
 'reports/generation.py':('Conserve textes contrôlés et gabarits explicites, avec audience internationale.','demandes, faits et preuves','sections de gabarit et libellés','tests/mode explicite et insertion canonique des nombres'),
 'reports/service.py':('Crée, révise, protège et exporte les rapports.','demandes et identifiants autorisés','rapport versionné, PDF ou deck','analyses/diagnostics, RAG, Qwen, validation et stockage'),
 'reports/validation.py':('Vérifie les sections, propositions et références.','rapport et données de preuve','validation ou refus','fusionne les champs d’une même source/version, refuse les versions contradictoires'),
 'reports/presentation.py':('Construit vingt-cinq diapositives distinctes depuis les résultats disponibles.','instantané du rapport et diagnostics','PDF de 25 pages','Chromium ; manques explicites, abrégés signalés et débordements contrôlés'),
 'reports/strategic.py':('Met en page une note de quinze parties distinctes.','rapport, analyses et diagnostics','PDF de 15 pages','gabarit A4 ; aucun KPI recalculé dans l’export'),
 'reports/export.py':('Choisit le rendu standard ou la note structurée.','instantané autorisé','PDF','Jinja2 et Chromium sans ressources réseau'),
 'reports/storage.py':('Conserve les versions et fichiers PDF en SQLite.','documents, rapports et exports','instantanés persistants','ajout de colonnes/métadonnées sans suppression des données antérieures'),
 'reports/revisions.py':('Interprète les opérations éditoriales autorisées.','instruction de révision','opération bornée','service de rapports ; audience internationale ajoutée'),
 'reports/router.py':('Expose rapports, tâches, exports et bibliothèque.','requêtes HTTP, PDF et session','JSON ou fichier protégé','services documentaires et file de tâches'),
 'schemas/report.py':('Étend les contrats de façon compatible.','JSON de demande/résultat','modèles Pydantic','layout, question, diagnostics, audience internationale et propositions restent optionnels'),
 'main.py':('Assemble les services et leur cycle de vie.','Settings et composants','application FastAPI','démarre/arrête surveillance et tâches, protège les routes et journalise les requêtes'),
}


FILE_ROLES={
 'frontend/src/features/workspace/Workspace.tsx':'Ajoute la navigation Diagnostics & cartes, les traces des spécialistes, les confirmations de KPI, les étapes/annulations des tâches et la surveillance des alertes. Charge chaque ressource dès sa réponse pour qu’un service lent ne masque pas les analyses disponibles.',
 'frontend/src/features/workspace/api.ts':'Soumet les conversations et opérations de rapport comme tâches persistantes, interroge leur état et transmet la progression. Conserve une tâche conversationnelle en attente pour éviter les doublons ; efface cette référence à la déconnexion.',
 'frontend/src/features/workspace/DiagnosticPanel.tsx':'Permet de choisir outil, dates, territoire et seuls seuils pertinents. Affiche matrices, benchmark à treize colonnes sélectionnables, carte filtrable et scénario ; les calculs viennent de l’API. Les graphiques restent défilables et accessibles au clavier sur petit écran.',
 'frontend/src/features/workspace/InteractiveChart.tsx':'Ajoute filtre temporel, sélection observations/prévisions, info-bulles au survol/focus, courbes et valeurs négatives. Le tableau donne aussi toutes les valeurs et les bornes ; aucun KPI n’est recalculé.',
 'frontend/src/features/workspace/InteractiveChart.test.tsx':'Contrôle filtres, focus, valeurs négatives et résultat vide avec des données de test. Ce sont des interactions React, sans serveur ni modèle réel.',
 'frontend/src/features/workspace/AnalysisCard.tsx':'Réutilise le graphique interactif dans chaque analyse tout en conservant formule, unités, sources et avertissement synthétique.',
 'frontend/src/features/workspace/DocumentsPanel.tsx':'Affiche les métadonnées, le caractère privé/partagé, les passages et l’état d’indexation ; conserve le parcours d’import et de recherche autorisé.',
 'frontend/src/features/workspace/ReportPanel.tsx':'Exécute révisions et exports comme tâches, affiche leur étape et permet l’annulation entre étapes. Ajoute propositions sourcées et téléchargement de la présentation PDF de vingt-cinq diapositives.',
 'frontend/src/features/workspace/Workspace.test.tsx':'Adapte les assertions à la progression des tâches et conserve les cas de saisie préservée, contexte, restauration refusée et graphique. Les appels API sont simulés explicitement.',
 'frontend/src/features/workspace/workspace.css':'Ajoute styles des graphiques interactifs, tables défilables et formulaire de diagnostic en deux colonnes sur grand écran, une sur mobile.',
 'frontend/src/features/reports/types.ts':'Étend les types avec audience internationale, question, format quinze pages, identifiants de diagnostics et propositions ; les propriétés antérieures restent compatibles.',
 'scripts/setup-local.ps1':'Installe Python/Chromium/npm, prépare facultativement outils et bibliothèque. Génère la référence seulement si les trois QVD sont absents, refuse une référence partielle et préserve une configuration personnalisée.',
 'scripts/start-full-app.ps1':'Démarre l’API locale avec vrais modèles/OCR, mapping étendu par défaut et surveillance toutes les soixante secondes, tout en respectant les variables de sources déjà configurées.',
 'scripts/start-local-ollama.ps1':'Démarre le service d’inférence local, avec un seul modèle et une seule inférence à la fois ; fixe le contexte CPU et garde le cloud désactivé.',
 'scripts/prepare-local-ai.py':'Prépare séparément service Ollama, poids Qwen/E5 et Tesseract. Épingle les ressources et évite de retélécharger les langues OCR déjà vérifiées ; ne copie aucune DLL dans Windows.',
 'scripts/lock-requirements.py':'Parcourt les dépendances réellement nécessaires, leurs extras et marqueurs Windows ; vérifie les contraintes installées puis écrit l’unique relevé transitif, sans réseau.',
 'scripts/measure-local.py':'Mesure trois répétitions des outils natifs, enregistre matériel, versions, volumes et état Git. Distingue première lecture et cache chaud ; ne simule aucune inférence ni SLA.',
 'scripts/measure-models.py':'Mesure réellement E5 puis Qwen trois fois, au premier chargement et à chaud. Décharge explicitement Qwen avant sa première mesure, vérifie dimensions/intentions et conserve les durées natives ; ne constitue pas une évaluation aveugle.',
 'scripts/evaluate-cps-languages.py':'Appelle réellement Ollama sur les cas tenus à part, compare l’intention aux attentes versionnées et conserve langue, tâche, durée et erreurs. Les options sélectionnent les cas et le fichier de résultats.',
 'scripts/build-completion-guide.py':'Produit le catalogue depuis les définitions et constantes manuelles des tests, puis cet inventaire depuis le diff et les descriptions. N’appelle pas le calcul métier pour fabriquer ses attendus.',
 'config/sources.extended.json':'Déclare six vues logiques sur cinq QVD internes : trois références, extension Performance, vue de marge Finance sur cette même extension et piliers de compétitivité. Garde les unités, relations et restrictions de domaine.',
 'config/international.synthetic.json':'Décrit le catalogue des six comparateurs publics fictifs, leurs champs et conventions monétaires communes ; ne modifie pas les droits internes.',
 'config/regional.synthetic.json':'Décrit le scénario des douze régions et ses données concurrentielles fictives, distinctes des six villes internes.',
 'config/geography.json':'Associe six villes à leurs coordonnées Wikidata vérifiées, liens et attribution CC0. Ne contient aucun contour administratif ou chiffre de fréquentation.',
 'config/business-glossary.json':'Fixe les termes métier dans les cinq langues, les noms propres et sigles admis en arabe, et les confusions interdites entre nuitées, journées et arrivées.',
 'config/ttci2019.json':'Déclare les quatre groupes de quatorze piliers et la référence WEF 2019. Indique explicitement les adaptations synthétiques et la différence avec le TTDI actuel.',
}


def catalogue():
    original=json.loads((ROOT/'examples/synthetic-reference.json').read_text(encoding='utf-8'))['calculation_oracle']['expected']
    tree=ast.parse((ROOT/'backend/tests/test_extended_analytics.py').read_text(encoding='utf-8'))
    extra=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets))
    expected={**original,**extra}
    lines=['# Catalogue et conventions de calcul','',
      'Les 46 définitions ci-dessous sont distinctes : ni traductions, ni filtres comptés comme nouveaux KPI. Les exemples proviennent des attendus manuels versionnés des tests et de `examples/synthetic-reference.json`, sans appeler le moteur de calcul pour produire la réponse attendue.','',
      'Le minijeu indépendant comporte deux marchés à Agadir : 100 nuitées, 25 arrivées, 200 sièges, 2 000 MAD de budget, 1 000 MAD exécutés, 1 500 MAD engagés, 20 000 MAD de recettes, 6 000 MAD de chambres, 40 chambres-nuits vendues sur 100 disponibles, 2 000 impressions et 100 clics. Les compléments manuels et piliers sont détaillés dans `test_extended_analytics.py`. Ce minijeu diffère du corpus volumineux.','',
      'Règles communes : grain mensuel/destination/marché ; dimensions et droits appliqués avant calcul. Les sommes portent sur les lignes du périmètre ; un ratio agrège d’abord numérateur/dénominateur. Une source invalide bloque le calcul. Une période sans ligne ou un dénominateur nul donne `null`, jamais un zéro inventé. Les métriques temporelles requièrent les historiques complets décrits ci-dessous.','',
      '| Identifiant / définition | Formule | Champs requis | Unité | Agrégation | Attendu manuel |',
      '| --- | --- | --- | --- | --- | --- |']
    for m in METRICS.values():
        fields=' ; '.join(s+': '+', '.join(fs) for s,fs in m.fields.items())
        value=expected[m.id]; example='null sur un mois isolé' if value is None else str(value)
        lines.append(f'| `{m.id}` — {m.label} | `{m.formula}` | {fields} | {m.unit} | {m.kind} | {example} |')
    lines+=['','## Limites et exigences d’historique','',
      '- ATI exclut le marché domestique Maroc. Les autres arrivées et recettes sont les grandeurs fictives définies dans le corpus, sans attribution automatique à une statistique officielle.',
      '- TCA/TCAM utilisent au moins deux années complètes ; le TCAM applique le nombre d’années écoulées. Sur trois années à 10, 12 puis 14,4 arrivées par mois, les deux attendus sont 20 %. ISM demande douze mois consécutifs ; un historique mensuel plat donne 0 %.',
      '- HHI : parts d’arrivées par marché, échelle 0–10 000 ; IDT = complément sur 0–1. Le marché domestique est inclus s’il appartient au périmètre. Gini : distribution des nuitées entre destinations autorisées ; un filtre change l’univers de l’indice.',
      '- IPR : score pédagogique sur trois ratios et cibles explicites (sièges 65 %, exécution 80 %, clics 3 %), poids 50/30/20. Ce choix de conception n’est pas attribué à un référentiel officiel.',
      '- ROI/IRT : marge attribuée par scénario, coût promotionnel et périmètres de même grain. Il ne démontre aucune incrémentalité ni cause économique.',
      '- TTCI : agrégation de quatorze piliers fictifs déjà normalisés en quatre groupes de 5/4/3/2, puis moyenne des quatre groupes. La pondération par arrivées pour les périodes/destinations est une convention du projet. Les indicateurs bruts du WEF ne sont pas reconstitués. Le résultat n’est ni un classement officiel ni le TTDI actuel. [Méthode historique, annexe B](https://www3.weforum.org/docs/WEF_TTCR_2019.pdf), [méthode TTDI 2026 distincte](https://www.weforum.org/publications/travel-tourism-development-index-2026/technical-notes-and-methodology).',
      '- Les prévisions comparent naïf et saisonnier sur les douze derniers mois réservés à l’évaluation. Au-delà de douze mois, la répétition de profil jusqu’à soixante mois est un scénario mécanique non calibré pour 2030. Les bandes empiriques ne garantissent aucune couverture.',
      '', '## KPI personnalisés','',
      'La DSL autorise deux sommes de champs déclarés, éventuellement filtrées par un marché, et une opération ratio/pourcentage/différence. Les unités sont vérifiées ; les scores non additifs sont refusés. La proposition montre la formule, l’interprétation et l’exemple calculé. Une confirmation explicite enregistre auteur et version. Les droits, le périmètre de l’exemple et ses versions de sources sont contrôlés à nouveau. Aucun Python/SQL/expression arbitraire n’est exécuté.','',
      'Les définitions actives peuvent être réutilisées par les utilisateurs autorisés aux sources ; seule une personne autorisée peut enregistrer une définition. Les résultats antérieurs sont invalidés si la définition change. Les seuils de qualité et conventions restent des choix pédagogiques à distinguer des obligations fonctionnelles du CPS.']
    (DOCS/'12-catalogue-et-conventions.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def inventory():
    changed=subprocess.check_output(['git','diff','--name-only','51fe630'],cwd=ROOT,text=True).splitlines()
    extra=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    paths=sorted(set(changed+extra))
    lines=['# Fichiers de la livraison et pipeline expliqué','',
      'Inventaire produit depuis la différence avec la version intégrée `51fe630`. Les signatures ci-dessous servent de repères de lecture ; les tests distinguent fonctions simulées et modèles réels.','',
      '## Exemple complet','',
      '1. Une question sur Agadir/février 2025 entre dans une tâche persistante. Qwen produit une intention, les dates/filtres sont ancrés, les droits sont appliqués.',
      '2. Le spécialiste marchés calcule 80 000 contre 100 000 nuitées (−20 %) depuis Commercial. Une note croisant les domaines appelle aussi Finance et Performance ; un pic saisonnier peut déclencher le contrôle budgétaire.',
      '3. Les diagnostics facultatifs BCG/Valeur–Volume/carte/scénario sont calculés, identifiés et conservés. Un scénario de −10 % sur 80 000 produit 72 000, explicitement hypothétique.',
      '4. La recherche consulte les PDF déjà indexés et autorisés ; elle transmet les passages utiles avec pages/versions. E5 calcule les embeddings, Chroma recherche ; aucune réimportation systématique ni entraînement.',
      '5. Qwen rédige. Le serveur ajoute les chiffres/citations exacts et vérifie la sortie. Une erreur produit un refus explicite, pas un rapport simulé.',
      '6. Le rapport garde ses versions, diagnostics et propositions. Chromium produit la note ou le rapport, puis les vingt-cinq diapositives. Les manques restent visibles ; les données synthétiques sont marquées.',
      '7. Une révision change une section et ses dépendances. Un ajout de KPI conserve les analyses antérieures lorsqu’il est demandé comme ajout. Une source ou permission modifiée est réévaluée à la consultation.','',
      'Installation = logiciels/poids ; génération des données = corpus fictif ; calcul = outils numériques ; indexation = vecteurs persistants ; inférence = modèles déjà entraînés ; évaluation = comparaison à des attendus. Aucun entraînement/fine-tuning n’est effectué.','',
      '## Inventaire','']
    for name in paths:
        path=ROOT/name
        if not path.exists():
            lines += [f'### `{name}` — supprimé','', 'Ancienne liste de dépendances remplacée par le point d’entrée `backend/requirements.txt` et son unique relevé de versions. Le contenu historique reste dans Git.',''];continue
        if name.endswith('13-fichiers-et-pipeline.md'):continue
        label=f'[{name}](../../{name})';lines += [f'### {label}','']
        if name.startswith('backend/app/') and name.endswith('.py'):
            role=ROLES.get(name.removeprefix('backend/app/'),('Module de la chaîne locale.','paramètres typés','résultat contrôlé','services applicatifs'))
            lines += [role[0],f'Entrées : {role[1]}. Sorties : {role[2]}. Interactions : {role[3]}.','']
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            functions=[]
            for node in tree.body:
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):functions.append(node.name)
                if isinstance(node,ast.ClassDef):functions += [node.name+'.'+m.name for m in node.body if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef))]
            if functions:lines += ['Repères : '+', '.join('`'+f+'`' for f in functions)+'.','']
        elif name.startswith('backend/app/reports/templates/') and name.endswith('.html'):
            role=('Met en page vingt-cinq diapositives de 320 × 180 mm : textes, graphiques, matrices avec repères/légendes et références.' if name.endswith('presentation.html') else
                  'Met en page les quinze parties A4 de la note structurée : textes, tableaux et graphiques avec unités et provenance.')
            lines += [role,'Entrées : instantané autorisé du rapport. Sortie : HTML échappé rendu par Chromium en PDF. CSS fixe, support RTL et marquage synthétique ; aucun accès réseau ni calcul métier dans le gabarit.','']
        elif name.startswith('backend/tests/'):
            lines += ['Tests de régression ou attendus indépendants. Le texte en tête du fichier précise les composants simulés et les essais nécessitant des modèles/navigateur réels. Les résultats datés sont dans le bilan de validation.','']
        elif name.startswith('frontend/'):
            role=('Définit les types compatibles des échanges.' if name.endswith('types.ts') else
                  'Teste les interactions avec données/API simulées ; ne prouve pas une inférence.' if '.test.' in name else
                  'Affiche les étapes, résultats et contrôles du parcours ; utilise les valeurs du backend et gère erreurs/chargements.' if name.endswith(('.ts','.tsx')) else
                  'Règles de présentation, petits écrans, tableaux et graphiques.')
            lines += [FILE_ROLES.get(name,role),'Entrées : état/session/réponses API. Sorties : interface et actions utilisateur. Interactions : routes FastAPI protégées ; aucun calcul métier confié au navigateur.','']
        elif name.startswith('config/'):
            lines += [FILE_ROLES.get(name,'Configuration versionnée : champs, unités, domaines, conventions ou vocabulaire. Lue par les services concernés ; ne contient pas de résultats analytiques précalculés.'),'']
        elif 'requirements' in name:
            lines += ['Décrit l’installation : dépendances directes commentées ou fermeture transitive des versions vérifiées. Les poids, le service Ollama, Tesseract et Chromium sont préparés séparément.','']
        elif name.startswith('scripts/'):
            lines += [FILE_ROLES.get(name,'Commande de préparation, mesure, évaluation ou documentation. Ses arguments et son en-tête indiquent les entrées et artefacts produits. Les serveurs restent locaux et les téléchargements sont explicites.'),'']
        elif name.startswith('examples/'):
            lines += ['Corpus versionné : données documentaires fictives ou cas linguistiques avec attentes. Ces fichiers servent à préparer/évaluer ; ils ne remplacent pas l’inférence ni les calculs du fonctionnement normal.','']
        else:
            lines += ['Documentation mise en accord avec le comportement livré : usage, conventions, preuves, architecture ou limites. Les résultats historiques restent identifiés comme historiques.','']
    (DOCS/'13-fichiers-et-pipeline.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':catalogue();inventory()
