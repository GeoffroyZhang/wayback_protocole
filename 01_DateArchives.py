"""
Objectif : Interroger l'API de la Wayback Machine afin de collecter des informations, métadonnées sur les sites.
Le nombre de snapshots valides (status code de 200) ; la date du premier snapshot ; et la 
date du dernier snapshot afin de délimiter les limites temporelles du corpus. 
Ce protocole s'appliquant seulement aux pages d'accueil des différents sites (urls) puisque la profondeur
d'archivage varie selon les sites, donc il n'est pas pertinent d'extraire tout le site en raison des
sauts temporels d'un lien à l'autre au sein de la même entité web.
"""

import requests
import csv
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Interrogation de l'API
API_Wayback = "https://web.archive.org/cdx/search/cdx"

# A configurer selon votre environnement 
dossier_sortie = r""

# Paramètres 
deley_requests = 1  # secondes
max_tentatives = 5
timeout = 20


def create_session():

    """Création d'une session pour améliorer l'efficacité du script"""
    
    session = requests.Session()
    retries = Retry(
        total=max_tentatives,
        backoff_factor=1,  # délai progressif entre tentatives
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session



def get_wayback_info(session, url):
    params = {
        "url": url,
        "output": "json",
        "fl": "timestamp",
        "filter": "statuscode:200"
    }

    try:
        response = session.get(API_Wayback, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if len(data) <= 1:
            return 0, None, None

        timestamps = [row[0] for row in data[1:]]
        count = len(timestamps)

        first = min(timestamps)
        last = max(timestamps)

        first_date = datetime.strptime(first, "%Y%m%d%H%M%S")
        last_date = datetime.strptime(last, "%Y%m%d%H%M%S")

        return count, first_date, last_date

    except Exception as e:
        print(f"Erreur pour {url}: {e}")
        return 0, None, None

# Liste des Urls → mettez votre liste (corpus)
urls = ["www.exemple.fr", ...]

session = create_session()

with open(dossier_sortie, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["URL", "Nombre_snapshots", "Premiere_archive", "Derniere_archive"])

    for url in urls:
        print(f"Analyse de {url}...")
        count, first, last = get_wayback_info(session, url)

        writer.writerow([
            url,
            count,
            first.strftime("%Y-%m-%d %H:%M:%S") if first else "",
            last.strftime("%Y-%m-%d %H:%M:%S") if last else ""
        ])

        time.sleep(deley_requests)

print("Terminé.")
