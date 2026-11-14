"""Reconstruit l'inventaire pédagogique depuis les signatures et imports du dépôt."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/full-app/fichiers'

ROLES={
 'main.py':('Assemble FastAPI, les services et leurs adaptateurs ; monte les routes et transforme les erreurs en réponses contrôlées.','Démarrer start-full-app.ps1 construit le fournisseur QVD et l’authentification locale.'),
 'core/config.py':('Centralise les paramètres et chemins, avec valeurs par défaut et variables d’environnement.','ONMT_FULL_APP=1 sélectionne l’intégration ; ONMT_OCR=1 active le traitement des scans.'),
 'core/errors.py':('Définit AppError, qui transporte code, message et statut HTTP ; forbidden évite de révéler une ressource interdite.','Un accès Finance interdit produit forbidden/403.'),
 'core/security.py':('Définit ResourcePolicy et les contrôles de rôles, modules, territoires et propriétaire utilisés par documents et rapports.','Un utilisateur régional ne lit pas un rapport privé du compte direction.'),
 'core/runtime.py':('Prépare les DLL C++ de la venv Windows avant le chargement de PyTorch, sans modifier Windows.','Le premier encodage E5 peut charger VCRUNTIME140_1.dll depuis .venv/Scripts.'),
 'core/llm_client.py':('Appelle Ollama localhost avec schéma JSON, vérifie le modèle local et gère délais, erreurs et sorties tronquées.','generate_json(schema,system,payload) rend le texte JSON réel du modèle ou lève AppError.'),
 'core/state.py':('Persiste l’état applicatif local dans SQLite : analyses calculées, conversations versionnées, alertes, comptes et sessions. Ne copie pas les tables QVD.','save_conversation(cid,owner,payload,base) refuse une version de base obsolète.'),
 'core/auth.py':('Gère comptes locaux, mots de passe scrypt, cookie opaque, expiration, limitation des connexions et routes login/me/logout.','resolve(request) transforme le cookie vérifié en AccessContext serveur.'),
 'data_access/synthetic.py':('Crée le corpus pédagogique définitif, l’écrit en QVD, relit toutes les cellules et écrit manifeste versionné/empreintes/références/jeux défectueux.','generate(Path("local_data/qvd-synthetic")) produit trois domaines, chacun de 2 100 lignes ; semantic_digest identifie les cellules indépendamment des métadonnées QVD.'),
 'data_access/qvd_reader.py':('Borne les chemins, vérifie les autorisations, lit nativement PyQvd, découvre les types et normalise les dates mensuelles.','read(source,access,{"destination":"Agadir"}) retourne lignes autorisées, empreinte et types.'),
 'data_access/catalog.py':('Charge les mappings, valide le grain, contrôle les lignes, décrit les sources et vérifie les associations.','read_authorized_data("commercial",fields,filters,access) retourne des colonnes logiques et une version de source.'),
 'analytics/quality.py':('Recherche les erreurs de qualité avant les sommes : doublons, dates, valeurs, unités et capacité.','inspect_rows(rows,source) renvoie une liste de codes ; une liste non vide bloque l’analyse.'),
 'analytics/metrics.py':('Déclare les seize définitions métier du noyau et leurs calculs autorisés, sans eval ni code produit par IA.','calculate(metric,totals) donne une somme ou un ratio ; un dénominateur nul donne None.'),
 'analytics/forecasting.py':('Évalue deux références temporelles sur douze mois mis de côté et produit les prévisions mensuelles avec limites explicites.','forecast(series,6) retourne points prévus et avertissements d’erreur/méthode.'),
 'analytics/anomalies.py':('Calcule et conserve les alertes de baisse annuelle à l’actualisation ; utilise une clé stable pour ne pas les dupliquer.','refresh(access) retrouve Agadir février 2025 à −20 % dans le corpus fictif.'),
 'analytics/service.py':('Orchestre accès, agrégations, comparaisons et prévisions ; fournit aussi l’adaptateur AnalysisProvider de Salma.','run(AnalysisRequest,AccessContext) rend un AnalysisResult ; get_analysis recontrôle droits et fraîcheur.'),
 'analytics/router.py':('Expose catalogue, indicateurs, analyses, alertes, actualisation et état des services à l’interface, sous contrôle d’accès.','POST /api/analyses appelle analytics.run ; GET /api/sources appelle catalog.describe.'),
 'conversation/slots.py':('Ancre les mois et filtres explicitement nommés, avec les synonymes de dimensions configurés ; normalise une traduction identifiable.','Février 2024 devient 2024-02-01/2024-02-29 ; un marché France ajouté par le modèle mais non demandé est retiré.'),
 'conversation/intent.py':('Décrit Intent et demande au vrai modèle de choisir une action structurée parmi les outils autorisés.','parse(message,context,catalog,language) retourne Intent, ensuite revalidé côté métier.'),
 'conversation/context.py':('Fusionne les paramètres d’une relance avec la dernière demande analytique ; laisse une demande incomplète sans calcul.','analysis_request(intent,context) renvoie AnalysisRequest ou None si une précision est nécessaire.'),
 'conversation/graph.py':('Construit le graphe LangGraph à deux nœuds : interprétation puis outil autorisé, avec un état Turn explicite.','build_graph(interpret,execute) retourne le graphe compilé ; invoke utilise recursion_limit=6.'),
 'conversation/service.py':('Coordonne les outils de Doha et Salma, conserve historique/contexte/version et synchronise les écrans complémentaires.','send(message,access,cid,base_version,language) rend une réponse avec opérations réelles ; link_context rattache une sélection autorisée.'),
 'conversation/router.py':('Expose messages, lecture autorisée d’une conversation et synchronisation du contexte.','POST /api/conversations/messages ne prend jamais un rôle ou un chemin de fichier.'),
 'reports/adapters.py':('Définit le protocole AnalysisProvider et les fournisseurs historiques non connecté ou à fixtures explicites.','L’application complète injecte AnalyticsService à la place de SyntheticAnalysisProvider.'),
 'reports/documents.py':('Décrit métadonnées, passages, document versionné et preuves ; construit une référence exacte pour un passage.','reference(doc,passage) inclut identifiant du passage, version et pages physiques.'),
 'reports/ocr.py':('Rend une page et exécute Tesseract local avec langues, limite de pixels, délai et avertissements de relecture.','extract_page(pdf_bytes,index) retourne texte, confiance moyenne et avertissements.'),
 'reports/ingestion.py':('Contrôle et importe un PDF, traite texte/scans, découpe en passages, indexe et conserve les versions et originaux.','ingest_pdf(content,metadata,access,document_id) renvoie document et booléen de doublon.'),
 'reports/retrieval.py':('Définit encodeurs réel/de test, collection Chroma par modèle et recherche sur documents autorisés.','search_evidence(question,access,limit) retourne des passages citables et des avertissements.'),
 'reports/generation.py':('Définit les textes contrôlés multilingues, la table des faits et la génération par gabarits explicite.','facts(analyses) extrait les valeurs déjà calculées ; render_fact restitue unité, période, filtres et sources.'),
 'reports/narrative.py':('Fait rédiger une prose locale, injecte les faits exacts et contrôle les éléments vérifiables et erreurs linguistiques identifiées.','generate_section(request,id,analyses,evidence,options) retourne section et manifeste de génération.'),
 'reports/revisions.py':('Convertit une consigne éditoriale connue en paramètres de section ; refuse les demandes inconnues ou nouveaux calculs isolés.','parse_revision("langue:ar") donne la langue de section ; un nouveau KPI doit passer par Doha.'),
 'reports/validation.py':('Vérifie sections, sources, chiffres et marqueur synthétique d’un rapport avant conservation.','verify_report(...) compare la sortie à son manifeste ou au gabarit explicitement utilisé.'),
 'reports/storage.py':('Conserve documents, originaux, rapports, versions, PDF et audit applicatif dans SQLite local.','save_report(payload,base_version) utilise une transaction pour éviter l’écrasement concurrent.'),
 'reports/service.py':('Orchestre création, lecture autorisée, révision, recalcul depuis de nouvelles analyses, export et téléchargement.','recalculate_report(id,analysis_ids,base,access) conserve l’identifiant et crée la version suivante.'),
 'reports/router.py':('Expose les routes protégées Salma : rapports, documents, preuves, versions et PDF.','get_access_context(request) utilise le résolveur serveur ; la démo historique est un mode distinct.'),
 'reports/export.py':('Prépare les faits et graphiques, applique le template HTML puis rend le PDF avec Chromium sans requêtes réseau du document.','render(payload) retourne les octets PDF ou une erreur explicite.'),
 'reports/demo.py':('Conserve le scénario historique Salma, explicitement à analyses/gabarits/embeddings de démonstration.','Ce script ne démontre pas l’intégration QVD ni un vrai LLM.'),
 'reports/demo_real.py':('Crée un PDF mixte fictif et montre OCR/E5/Ollama/PDF sur les anciennes fixtures synthétiques Salma.','synthetic_mixed_pdf() est aussi réutilisé par le test réel de la nouvelle intégration.'),
 'schemas/common.py':('Définit les contrats communs stricts, langues, périodes, sources, identité et erreurs.','Period refuse une date de fin antérieure au début.'),
 'schemas/analysis.py':('Définit demande/résultat d’analyse et points observés/prévus, avec règles de comparaison, horizon et intervalles.','AnalysisRequest compare exige comparison_period ; AnalysisResult conserve formule et is_synthetic.'),
 'schemas/report.py':('Définit demandes, sections, résultats et modifications de rapport avec version de base.','ReportRevisionRequest porte report_id, base_version, section_id et instruction.'),
}

HELP={
 'semantic_digest':'Entrée : table décodée avec colonnes et cellules. Résultat : SHA-256 du JSON canonique, indépendant des horodatages du conteneur QVD ; vérifie la reproductibilité des données.',
 'source_formula':'Entrée : mapping des sources. Résultat : description de formule utilisant les colonnes réellement lues, avec qualification des domaines pour un rapprochement.',
 'benchmark':'Entrées : demande analytique, accès, dimension de regroupement et valeurs facultatives. Résultat : une analyse autorisée par destination/marché, sans jointure multiplicative.',
 'describe':'Entrée : accès serveur. Résultat : catalogue des sources visibles, types, périodes, unités, erreurs et relations contrôlées.',
 'metrics':'Entrée : accès. Résultat : définitions des indicateurs dont tous les modules requis sont autorisés.',
 'source_version':'Entrée : chemin configuré. Résultat : empreinte SHA-256 du contenu ; une source absente provoque une erreur.',
 'normalize_month':'Entrée : date ISO, date Python ou numéro Qlik. Résultat : date ISO du premier jour du mois ; refuse une date hors grain.',
 'explicit_periods':'Entrée : texte de question. Résultat : au plus deux périodes mensuelles explicitement nommées, avec fin de mois exacte.',
 'ground_intent':'Entrées : intention, message et catalogue facultatif. Résultat : intention revalidée après ancrage des dates, filtres et traduction explicites.',
 'normalized':'Entrée : texte. Résultat : texte normalisé pour comparer les accents, chiffres arabes et synonymes sans modifier les données sources.',
 'write_qvd':'Entrées : chemin de sortie et lignes. Écrit un vrai QVD et compare sa relecture cellule par cellule ; erreur en cas de différence.',
 'next_month':'Entrées : date et décalage de mois. Résultat : premier jour du mois décalé, y compris au passage d’une année.',
 'save_analysis':'Entrées : résultat, propriétaire, demande initiale et périmètre autorisé. Conserve un instantané calculé, pas les lignes QVD.',
 'analysis':'Entrées : identifiant et propriétaire. Résultat : instantané de l’analyse autorisée ou None.',
 'list_analyses':'Entrée : propriétaire. Résultat : les cent derniers instantanés de ses analyses ; la fraîcheur est ensuite recontrôlée par le service.',
 'conversation':'Entrées : identifiant et propriétaire. Résultat : historique/contexte/version enregistrés, ou None si la ressource ne lui appartient pas.',
 'save_conversation':'Entrées : identifiant, propriétaire, charge utile et version de base. Sauvegarde atomique ou conflit explicite.',
 'bootstrap':'Crée les comptes locaux de développement absents ; ne remplace ni mot de passe ni droits d’un compte déjà présent.',
 '_digest':'Entrées : mot de passe et sel hexadécimal. Résultat : dérivé scrypt utilisé pour comparer les mots de passe sans les stocker en clair.',
 'version':'Entrées : source et empreinte. Résultat : empreinte combinant contenu QVD et mapping métier, pour invalider aussi un changement de définition.',
 'versions':'Entrée : identifiants de sources. Résultat : dictionnaire des versions actuelles relues depuis les fichiers configurés.',
 'connect':'Ouvre une connexion SQLite avec transaction et fermeture garanties ; le bloc appelant reçoit la connexion.',
 '__init__':'Construit l’objet et conserve ses dépendances ; aucun résultat métier n’est retourné.',
 'run':'Entrées : demande validée et accès serveur. Résultat : analyse calculée et persistée, ou erreur explicite.',
 'get_analysis':'Entrées : identifiant et accès. Résultat : analyse du propriétaire avec droits et version de source contrôlés.',
 'authorize_snapshot':'Contrôle propriétaire et périmètre d’un instantané sans le présenter comme à jour ; utilisé pour un recalcul explicite.',
 'read_authorized_data':'Entrées : source logique, champs, filtres et accès. Résultat : lignes logiques contrôlées et version combinée.',
 'generate_section':'Entrées : rapport, section, analyses, preuves et options. Résultat : ReportSection et manifeste contenant la prose contrôlée.',
 'send':'Entrées : texte, accès, conversation, version et langue. Résultat : message avec analyse/rapport/preuves et trace des outils.',
 'parse':'Transforme la demande et son contexte autorisé en intention JSON validée ; ne calcule pas les KPI.',
 'analysis_request':'Construit le contrat analytique depuis l’intention et le contexte ; renvoie None si une information obligatoire manque.',
 'forecast':'Entrées : série mensuelle et horizon. Résultat : points projetés, méthode, erreurs et limites, sans données futures d’entraînement.',
 'refresh':'Relit les données autorisées et remplace les alertes du périmètre sans doublons ; pas un ordonnanceur permanent.',
 'generate':'Entrées : dossier de sortie et graine fixe. Résultat : manifeste après écriture et relecture native des QVD.',
 'inspect_rows':'Entrées : lignes et définition de source. Résultat : codes d’anomalies bloquantes, sans correction silencieuse.',
 'calculate':'Applique uniquement les opérations du catalogue aux totaux déjà sélectionnés ; renvoie nombre ou None.',
 'resolve':'Transforme une session valide en AccessContext provenant de la base serveur ; sinon erreur 401.',
 'login':'Vérifie le mot de passe local et crée une session opaque, avec limitation des tentatives.',
 'create_report':'Charge les analyses autorisées, cherche les preuves, rédige/contrôle et conserve un ReportResult versionné.',
 'revise_report':'Applique une opération éditoriale aux sections concernées ; refuse base_version obsolète.',
 'recalculate_report':'Utilise de nouveaux identifiants d’analyse déjà calculés ; conserve le rapport et crée une version.',
 'render':'Entrée : instantané de rapport. Résultat : octets du PDF produit par Chromium.',
 'extract_page':'Entrées : octets PDF et index de page. Résultat : texte OCR, score moyen et avertissements.',
 'encode':'Entrées : textes et indicateur question/passage. Résultat : vecteurs normalisés ; encodeur réel ou test explicitement distinct.',
 'ingest_pdf':'Entrées : PDF, métadonnées, accès et identifiant éventuel. Résultat : document versionné et indicateur de doublon.',
 'search_evidence':'Recherche parmi les versions et documents permis ; retourne EvidenceResult avec références vérifiables.',
 'generate_json':'Entrées : schéma, consigne et données. Résultat : JSON brut du modèle local ; aucune arithmétique ou commande libre.',
 'link_context':'Rattache une sélection autorisée aux paramètres de conversation en respectant sa version de base.',
}


def module_name(path):
    return '.'.join(path.relative_to(ROOT/'backend').with_suffix('').parts)


def inventory():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    files=sorted((ROOT/'backend/app').rglob('*.py'))
    importers={module_name(p):set() for p in files}
    trees={p:ast.parse(p.read_text(encoding='utf-8-sig')) for p in files}
    for path,tree in trees.items():
        current=module_name(path)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                target='.'.join(current.split('.')[:-node.level]+([node.module] if node.module else [])) if node.level else node.module
                if target in importers:
                    importers[target].add(str(path.relative_to(ROOT)).replace('\\','/'))
    groups={'commun':[],'donnees-analyses':[],'conversation':[],'rapports':[]}
    for path,tree in trees.items():
        local=str(path.relative_to(ROOT/'backend/app')).replace('\\','/')
        group='rapports' if local.startswith('reports/') else 'conversation' if local.startswith('conversation/') else 'donnees-analyses' if local.startswith(('analytics/','data_access/')) else 'commun'
        relative=str(path.relative_to(ROOT)).replace('\\','/')
        role,example=ROLES.get(local,('Marque le répertoire comme package Python ; aucune logique métier autonome.','Permet les imports des modules voisins.'))
        lines=[f'## `{relative}`','',role,'',f'**Exemple :** {example}','']
        dependencies=sorted({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module and n.module.startswith(('app.','pyqvd','langgraph'))})
        callers=sorted(importers[module_name(path)])
        lines += ['**Utilise :** '+(', '.join(f'`{n}`' for n in dependencies) or 'bibliothèque standard, imports relatifs ou types du module.'),'',
                  '**Importé par :** '+(', '.join(f'`{n}`' for n in callers) or 'chargement Python, montage par FastAPI/Pydantic, script ou test ; voir le parcours guidé pour les appels indirects.'),'']
        classes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
        for cls in classes:
            fields=[f'`{n.target.id}: {ast.unparse(n.annotation)}`' for n in cls.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)]
            lines += [f'**Classe `{cls.name}`**'+(f' : hérite de {", ".join(ast.unparse(b) for b in cls.bases)}.' if cls.bases else '.'),'']
            if fields:
                lines += ['Champs contrôlés : '+ '; '.join(fields)+'.','']
        functions=[(n.name,n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        for cls in classes:
            functions += [(cls.name+'.'+n.name,n) for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        if functions:
            lines += ['| Fonction / paramètres | Résultat et rôle |','| --- | --- |']
            for name,node in functions:
                signature=ast.unparse(node.args).replace('|','\\|')
                explanation=HELP.get(node.name) or ast.get_docstring(node) or ('Route HTTP : délègue au service décrit ci-dessus et restitue sa réponse contrôlée.' if any(isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr in ['get','post','patch'] for d in node.decorator_list) else 'Étape interne du composant décrit ci-dessus ; ses paramètres nommés indiquent les objets transmis. Voir le parcours et le code pour son branchement exact.')
                result=(' Retour typé : `'+ast.unparse(node.returns).replace('|','\\|')+'`.') if node.returns else ''
                lines.append(f'| `{name}({signature})` | {explanation.replace(chr(10)," ").replace("|",chr(92)+"|")}{result} |')
            lines.append('')
        groups[group].extend(lines)
    for group,lines in groups.items():
        (OUTPUT/f'{group}.md').write_text('# Inventaire : '+group+'\n\nSignatures extraites du code ; descriptions pédagogiques maintenues dans `scripts/build-code-guide.py`. Les imports listés sont statiques : ils ne remplacent pas le parcours guidé des appels par injection.\n\n'+'\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    inventory()
    print('Inventaires backend reconstruits sous docs/full-app/fichiers/.')
