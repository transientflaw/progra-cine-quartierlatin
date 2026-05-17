# 🎬 Progra Ciné Quartier Latin

Application web mobile-first qui agrège les séances quotidiennes des cinémas indépendants du Quartier latin (Paris 5e/6e) en une **timeline horaire unifiée**.

**Source des données** : [L'Officiel des spectacles (offi.fr)](https://www.offi.fr)
**Hébergement** : GitHub Pages (gratuit)
**Mise à jour** : automatique via GitHub Actions chaque nuit à 4h (heure de Paris)

## Cinémas couverts

| Cinéma | Adresse |
|---|---|
| Le Champo | 51 rue des Écoles |
| Filmothèque du Quartier latin | 9 rue Champollion |
| Reflet Médicis | 3 rue Champollion |
| Les 3 Luxembourg | 67 rue Monsieur-le-Prince |
| Grand Action | 5 rue des Écoles |
| Studio Galande | 42 rue Galande |
| La Clef | 34 rue Daubenton |
| Nouvel Odéon | 6 rue de l'École de Médecine |
| Écoles Cinéma Club | 23 rue des Écoles |
| Cinéma du Panthéon | 13 rue Victor-Cousin |
| Christine Cinéma Club | 4 rue Christine |
| Saint-André des Arts | 30 rue Saint-André des Arts |

## Architecture

```
┌───────────────────────────────────────────────┐
│  GitHub Actions (cron quotidien, 4h Paris)    │
│  ├─ scripts/scraper.py                        │
│  ├─ Parse offi.fr (12 cinémas)                │
│  └─ Commit public/data.json                   │
└───────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────┐
│  GitHub Pages                                  │
│  ├─ public/index.html (PWA)                   │
│  ├─ public/data.json (lu en fetch)            │
│  └─ public/manifest.json + icons              │
└───────────────────────────────────────────────┘
```

## Mise en route

### 1. Créer le repo sur GitHub

```bash
# Sur ton ordi, dans le dossier du repo cloné depuis ce zip :
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TON_USER/progra-cine-quartierlatin.git
git push -u origin main
```

### 2. Activer GitHub Pages

Dans **Settings → Pages** du repo :
- Source : **Deploy from a branch**
- Branch : **main** / Folder : **/public**
- Save

L'URL sera : `https://TON_USER.github.io/progra-cine-quartierlatin/`

### 3. Premier scraping manuel

Dans **Actions → Daily scrape → Run workflow**, tu déclenches la première récolte manuellement. Ensuite le cron prend le relais chaque nuit.

### 4. Installation sur iPhone (PWA)

Ouvre l'URL dans Safari sur iPhone → bouton Partager → **Ajouter à l'écran d'accueil**. L'app apparaît avec l'icône, en plein écran.

## Développement local

```bash
# Test du scraper
pip install -r scripts/requirements.txt
python3 scripts/scraper.py

# Test du frontend (serveur statique simple)
cd public && python3 -m http.server 8000
# Ouvrir http://localhost:8000
```

## Personnalisation

- **Ajouter un cinéma** : éditer `scripts/cinemas.json` (id, nom, coordonnées GPS, slug offi.fr)
- **Changer le style** : `public/index.html` (CSS dans le `<style>`)
- **Changer le cron** : `.github/workflows/scrape.yml`

## Avertissement données

Les séances sont scrapées depuis offi.fr à des fins personnelles d'agrégation. Pour réservation et tarifs, toujours vérifier sur le site du cinéma concerné.

## Licence

MIT
