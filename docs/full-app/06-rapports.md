# Salma : préserver les faits et construire le document

Le module existant est conservé. L'intégration remplace seulement son fournisseur d'analyses par `AnalyticsService` lorsqu'on démarre l'application complète. Les anciens scripts Salma restent disponibles ; ils ne correspondent pas à l'application intégrée.

## Import et recherche documentaire

`DocumentService.ingest_pdf()` contrôle le PDF, ses métadonnées et les droits. pdfplumber extrait le texte sélectionnable. Les pages sans texte ou essentiellement scannées passent par `LocalOCR.extract_page()` si l'OCR est activé. PDFium rend la page et Tesseract reconnaît le français, l'anglais et l'arabe.

Les passages gardent document, version, page, identifiant, langue et origine texte/OCR. Les scores de reconnaissance ne sont pas des garanties. Les nombres reconnus dans un scan ne deviennent jamais des KPI du moteur analytique.

`LocalSentenceEmbedder` charge E5-small sur CPU. `ChromaIndex` conserve les vecteurs dans une collection liée à l'identité/révision du modèle. `Retriever` filtre les sources autorisées avant la recherche et revérifie les passages contre le stockage. Un modèle différent nécessite une réindexation ; les vecteurs ne sont pas mélangés.

## Rapport sourcé

`ReportService._analyses()` récupère les résultats par l'adaptateur. `AnalyticsService.get_analysis()` recontrôle propriétaire, droits et version des QVD/mappings. Une analyse périmée est refusée avant un nouveau rapport.

`NarrativeWriter` donne au modèle le rôle de chaque mesure et les extraits autorisés. Il fait écrire une prose courte par constat ; les valeurs exactes et sources sont insérées par le serveur. Le sens d'une comparaison déjà calculée peut être fourni explicitement. Le modèle n'a aucun outil de calcul. Les chiffres libres, références inventées, altérations de faits et certaines affirmations causales provoquent un refus.

Ce mécanisme produit une synthèse contrôlée. Il ne constitue pas à lui seul le diagnostic économique long, argumenté et validé par un expert demandé dans le CPS. La qualité du vocabulaire, les interprétations implicites et les recommandations exigent une relecture.

L'ancien essai arabe avait montré une confusion nuitées/journées et des caractères cyrilliques dans un nom. Cette évolution ajoute un glossaire et refuse ces erreurs identifiées avant sauvegarde. La relecture a aussi révélé des variables minuscules et une clôture parlant du serveur : elles sont désormais refusées. Cela ne constitue pas une validation générale de la langue ni une garantie contre toutes les erreurs sémantiques.

## Versions et PDF

`create_report()` crée une version ; `revise_report()` applique les modifications éditoriales et leurs dépendances sans recalcul des KPI. `recalculate_report()` n'invente pas de calcul : Hayat a d'abord demandé de nouveaux résultats à Doha. Elle conserve le même identifiant de rapport, augmente la version et régénère les sections concernées ; les anciens instantanés restent dans SQLite.

`verify_report()` contrôle sections, faits, sources et marqueur synthétique. `Store.save_report()` utilise une transaction et vérifie la version de base. `PDFExporter.render()` applique Jinja2, puis Chromium produit le PDF avec une direction de lecture par section. Les citations et unités d'origine peuvent rester françaises dans une section arabe. Le titre global ne se traduit pas automatiquement.

L'aperçu et le téléchargement du PDF passent par les routes protégées existantes. L'option `inline=true` conserve les contrôles d'accès mais sert le PDF en affichage intégré ; le téléchargement ordinaire garde sa disposition pièce jointe. Les modèles et données ne quittent pas l'ordinateur pendant l'inférence. Le stockage SQLite local n'est pas déclaré chiffré ni inviolable ; les exigences de sécurité de production du CPS restent distinctes.
