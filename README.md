# Protocole d'extraction des archives du web utilisant l'API de la Wayback Machine

## Description

Ce protocole de recherche collecte et structure les archives web issue de la **Wayback Machine** (Internet Archive). Il s'agit de sites d'associations françaises et chinoises réunies en corpus autour d'une thématique commune . Il s'inscrit dans le cadre d'un mémoire de recherche universitaire à l'Université Paris 1 Panthéon-Sorbonne et vise à constituer un corpus diachronique à partir des pages d'accueil archivées de 46 sites associatifs.

L'analyse porte uniquement sur les **pages d'accueil**, la profondeur d'archivage variant selon les sites, ce qui rend l'extraction des sous-pages peu fiable sur le plan temporel.

---

## Pipeline - Ordre d'exécution

Les scripts doivent être exécutés **dans l'ordre suivant** :

```
01_DateArchives.py
        ↓
02_ScriptWaybackPageAccueilVisuel.py
        ↓
03_ExtractionMetriques.py
        ↓
04_corpus_texte_par_pageAccueil.py
```

---

## Description des scripts

### `01_DateArchives.py`
Interroge l'API CDX de la Wayback Machine pour chaque URL de la liste afin de récupérer :
- Le **nombre de snapshots valides** (status HTTP 200)
- La **date du premier snapshot**
- La **date du dernier snapshot**

**Output :** `ArchivesDates.csv`

---

### `02_ScriptWaybackPageAccueilVisuel.py`
Pour chaque snapshot disponible, collecte via **Playwright** (navigateur headless) :
- Le **HTML rendu** (avec CSS, JavaScript et images)
- Un **screenshot** pleine page (`.png`)
- Les **métadonnées** du snapshot (`.json`)

**Output :** Un dossier par domaine contenant les fichiers `.html`, `.png` et `_metadata.json`

---

### `03_ExtractionMetriques.py`
Analyse les fichiers HTML collectés par le script précédent et extrait les métriques suivantes :
- Détection du **CMS** (WordPress, Wix, Joomla, etc.)
- **Taille** en octets
- **Nombre de mots** (via Trafilatura)
- **Nombre d'images**, de boutons, de liens internes/externes
- Présence de **réseaux sociaux** (Facebook, Instagram, YouTube, Twitter/X, Weibo, WeChat, LinkedIn)

**Output :** `CorpusWayback_Metriques.csv`

---

### `04_corpus_texte_par_pageAccueil.py`
Extrait le **contenu textuel** de chaque snapshot pour constituer un corpus linguistique diachronique :
- Extraction via **Trafilatura**
- Détection de la **langue** (via langdetect)
- Sauvegarde en `.txt` (pour analyse sur **Iramuteq**) et `.csv` avec métadonnées

**Output :** Un dossier par domaine contenant les fichiers `.txt` et un `_metadata.csv`

---

## Installation

### Prérequis
- Python 3.9 ou supérieur

### Installer les dépendances

```bash
pip install -r requirements.txt
```

### Installer Playwright et son navigateur

```bash
pip install playwright
playwright install chromium
```

---

## Configuration

Avant d'exécuter les scripts, **modifiez les chemins de sortie** en haut de chaque fichier selon votre environnement :

```python
# Exemple dans 01_DateArchives.py
dossier_sortie = r"chemin/vers/votre/dossier/ArchivesDates.csv"
```

---

## Avertissements et biais

- **Trafilatura** est principalement entraîné sur des articles de presse. Certains contenus associatifs pertinents peuvent ne pas être extraits. Une lecture proche des sources reste nécessaire.
- **langdetect** utilise un modèle probabiliste. Sur des sites bilingues (français/chinois), il retourne la langue dominante. Sur des textes très courts, des confusions entre langues latines sont possibles.
- Le **nombre de mots** peut être sous-estimé pour les pages en chinois, car les caractères ne sont pas séparés par des espaces.
- La **taille en octets** peut être gonflée pour les pages en chinois (un caractère = 3 octets en UTF-8).
- Ce protocole dépend de la **qualité et de la complétude des archives** de la Wayback Machine.

---

## Structure du projet

```
protocole-wayback/
├── README.md
├── requirements.txt
├── 01_DateArchives.py
├── 02_ScriptWaybackPageAccueilVisuel.py
├── 03_ExtractionMetriques.py
└── 04_corpus_texte_par_pageAccueil.py
```

---

## Auteur

Geoffroy Zhang — Mémoire SDHC, 2026
