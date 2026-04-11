from playwright.sync_api import sync_playwright
import json
import time
import requests
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Dossier de sortie 
dossier = Path(r"")

request_delay = 3           # délais entre les requêtes
timeout = 30                # Timeout pour la requête
timeout_playwright = 60000  # Timeout pour le chargement des pages (60000 car playwright s'exécute en milliseconde)

# Bornes chronologiques obtenues via un autre script
date_debut = "Ex. 20050101"
date_fin   = "Ex. 20260324"

wayback_cdx_api = "https://web.archive.org/cdx/search/cdx"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"
}

urls = [www.exemple.fr]


def creer_session():
    """
    Crée une session HTTP persistante avec retry automatique.
    Réutilisable pour n'importe quel projet de collecte web.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def extraire_domain(url):
    """
    Extrait le domaine depuis une URL et supprime le 'www.' si présent.
    Exemple : https://www.lajcf.fr -> lajcf.fr
    """
    parsed = urlparse(url) # parse l'url 
    domain = parsed.netloc # .netloc extrait le nom de domaine 

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def get_snapshots(url, session):
    """
    Interroge l'API CDX de la Wayback Machine pour récupérer
    tous les snapshots HTTP 200 disponibles pour une URL donnée.
    Les doublons HTML sont supprimés (collapse=digest).
    Retourne une liste de timestamps (ex: ['20150304120000', ...]).
    """
    params = {
        "url": url,
        "output": "json",
        "filter": "statuscode:200",
        "collapse": "digest", 
        "from" : date_debut, 
        "to" : date_fin
    }

    reponse_cdx = session.get(
        wayback_cdx_api,
        params=params,
        headers=headers,
        timeout=timeout
    )

    reponse_cdx.raise_for_status()
    data = reponse_cdx.json()

    # La première ligne contient les noms des colonnes, pas des données
    if len(data) <= 1:
        return []

    return [row[1] for row in data[1:]]


def traiter_snapshot(page, url, domain, ts, site_path):
    """
    Pour un snapshot donné :
    - Charge la page avec Playwright (rendu complet CSS/JS/images)
    - Sauvegarde le HTML rendu
    - Prend un screenshot pleine page
    - Sauvegarde les métadonnées
    Retourne True si le snapshot a été traité, False sinon.
    """
    nom_base = f"{ts[:8]}_{ts[8:]}"

    chemin_html = site_path / f"{nom_base}.html"
    chemin_screenshot = site_path / f"{nom_base}.png"
    chemin_metadata = site_path / f"{nom_base}_metadata.json"

    # Si déjà traité, on passe (reprise possible après interruption)
    if chemin_html.exists():
        return False

    # URL Wayback sans id_ pour le rendu complet
    snapshot_url = f"https://web.archive.org/web/{ts}/{url}"

    response = page.goto(
        snapshot_url,
        timeout=timeout_playwright,
        wait_until="domcontentloaded"
    )

    # Délai pour laisser le JS s'exécuter
    page.wait_for_timeout(3000)

    status_code  = response.status if response else None
    title = page.title()
    html_content = page.content()

    # Sauvegarde du HTML
    with open(chemin_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Screenshot pleine page
    page.screenshot(
        path=str(chemin_screenshot),
        full_page=True
    )

    # Métadonnées
    date_lisible  = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
    heure_lisible = f"{ts[8:10]}:{ts[10:12]}:{ts[12:14]}"

    metadonnees = {
        "url": url,
        "domain": domain,
        "timestamp": ts,
        "date": date_lisible,
        "heure": heure_lisible,
        "snapshot_url": snapshot_url,
        "title": title,
        "status": status_code,
        "timestamp_collecte": datetime.now().isoformat(),
        "html_size": len(html_content)
    }

    with open(chemin_metadata, "w", encoding="utf-8") as m:
        json.dump(metadonnees, m, indent=4, ensure_ascii=False)

    return True

#--------------------------#
# Script principal 
#--------------------------#

def main():

    # Création du dossier 
    dossier.mkdir(parents=True, exist_ok=True)

    session = creer_session()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Pour ne pas avoir le navigateur (gain de vitesse)

        # On boucle pour chaque url dans la liste urls 
        for url in urls:

            domain = extraire_domain(url)
            print(f"\nTraitement : {domain}")

            site_path = dossier / domain
            site_path.mkdir(parents=True, exist_ok=True)

            # Récupération des snapshots
            try:
                snapshots = get_snapshots(url, session)

                if not snapshots:
                    print("Aucun snapshot trouvé")
                    continue

                print(f"{len(snapshots)} snapshots distincts trouvés")

            except Exception as e:
                print(f"Erreur récupération CDX : {e}")
                continue

            # Traitement de chaque snapshot
            nouveaux_fichiers = 0

            for ts in snapshots:

                page = browser.new_page()

                try:
                    traite = traiter_snapshot(page, url, domain, ts, site_path)

                    if traite:
                        nouveaux_fichiers += 1
                        print(f"  {ts}")
                        time.sleep(request_delay)

                except Exception as e:
                    print(f"  Erreur snapshot {ts} : {e}")
                    time.sleep(5)

                finally:
                    page.close()

            print(f"{nouveaux_fichiers} nouveaux fichiers téléchargés")

        browser.close()


if __name__ == "__main__":
    main()