"""
Script d'extraction du texte par site pour analyse diachronique
depuis les fichiers HTML collectés par le script archiveVisuelleAccueilWayback.py

Output : Un dossier qui contient, pour chaque urls (site), un dossier portant 
le nom de domaine de celui-ci. A l'intérieur de ce dossier se trouve les fichiers
.txt contenant le contenu lexcical extrait via Trafilatura, ainsi que le fichier
.csv qui comporte pour chaque fichier texte (snapshot) les métadonnées et le texte. 

Biais : Ce script dépend de la qualité des archives collectés en amont. 
Le contenu ne porte que sur les pages d'accueil, faute de qualité pour les 
autre pages. Donc le discours émis par chaque site n'est pas représentatif 
de tout le site. 

"""

from pathlib import Path
from langdetect import detect, LangDetectException
import trafilatura
import csv

# Dossier contenant les archives collectées par le script utilisant playwright 
dossier_entree = Path(r"Mettre le chemin correspondant au répertoire dans lequel sont stockés les snapshots")

# Chemin de sortie
dossier_corpus = Path(r"Mettre le chemin de sortie des fichiers .txt et du CSV")
dossier_corpus.mkdir(parents=True, exist_ok=True)

# sorted() permet de garantir l'ordre chronologique des fichiers 
# iterdir() permet de parcourir tout le dossier 
for dossier_source in sorted(dossier_entree.iterdir()):

    if not dossier_source.is_dir():
        continue

    domain = dossier_source.name

    # Dossier de sortie — nom différent
    dossier_site = dossier_corpus / domain
    dossier_site.mkdir(parents=True, exist_ok=True)

    # On lit depuis le dossier source
    fichiers_html = sorted(dossier_source.glob("*.html"))

    if not fichiers_html:
        print("Aucun fichier HTML trouvé")
        continue

    print(f"{len(fichiers_html)} fichiers HTML trouvés")

    # Création du CSV du site
    chemin_csv = dossier_site / f"{domain}_metadata.csv"

    with open(chemin_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL) # Entoure chaque champ de guillemets pour éviter les problèmes d'écriture

        # En-têtes
        writer.writerow(["timestamp", "date", "langue", "nb_mots", "taille_octets", "fichier", "texte"])

        for chemin_html in fichiers_html:
            
            # nom_base correspond au timestamp
            nom_base = chemin_html.stem              # Ex. 20110705_182442
            nom_fichier = f"{domain}_{nom_base}.txt" # Ex. lajcf_20110705.txt
            chemin_txt = dossier_site / nom_fichier

            # Si le fichier .txt existe alors on continue
            if chemin_txt.exists():
                continue 

            # On lit d'abord le fichier 
            html_content = chemin_html.read_text(encoding="utf-8")
            
            # C'est ici qu'on extrait le texte des différents fichiers 
            # Trafilatura extrait le contenu principal de la page 
            # en ignorant tous les autres éléments qui pourraient être
            # superflus comme les tableaux, etc. 
            # Il faut faire attention à Trafilatura car il est essentiellemnt
            # entraîné sur des articles de presse, donc certains éléments pertinents
            # peuvent passer à la trappe. Il faut garder une lecture proche. 
            # Il faut faire attention à l'interprétation ! 
            texte = trafilatura.extract(html_content)

            # Si Trafilatura n'a rien extrait, on continue
            if not texte or len(texte.strip()) == 0:
                print(f"Texte vide : {nom_base}")
                continue

            # Détection de la langue
            # Utilisation d'un modèle probabiliste donc il faut faire attention. 
            # Biais : Sur les sites bilingues (Ex. Français/Chinois), langdetec
            # retourne la langue dominante donc il faut faire attention à l'interprétation
            # de la métadonnée langue !!
            # De même, sur des textes très courts, langdetect peut confondre certaines
            # langues latines.  
            try:
                langue = detect(texte)
            except LangDetectException:
                langue = "inconnue"

            # Métriques
            nb_mots = len(texte.split())               # Il faut faire attention avec le chinois puisque les caractères n'utilisent pas d'espace donc le chiffre peut être faussé
            taille_octets = len(texte.encode("utf-8")) # Un caractère chinois prend 3 octets en utf-8 donc cela peut possiblement gongler la taille d'une page

            # Date lisible
            ts = nom_base.replace("_", "")                  # On remplace l'underscore 
            date_lisible = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"  # On met la date au format YYYY-MM-DD

            # Sauvegarde du texte brut
            # Pour analyse future sur Iramuteq
            try:
                chemin_txt.write_text(texte, encoding="utf-8")
            except Exception as e:
                print(f"Erreur sauvegarde txt {nom_base} : {e}")
                continue

            # Ajout d'une ligne dans le CSV
            # Attention, on inclut le texte dans le fichier csv 
            # donc celui-ci peut devenir extrêmement lourd en fonction du nombre 
            # de données textuels dans un snapshot
            try:
                writer.writerow([
                    nom_base,
                    date_lisible,
                    langue,
                    nb_mots,
                    taille_octets,
                    nom_fichier,
                    texte
                ])
                print(f"{nom_base} -> {langue} ({nb_mots} mots)")

            except Exception as e:
                print(f"Erreur sauvegarde CSV {nom_base} : {e}")
                continue

print("\nTerminé.")