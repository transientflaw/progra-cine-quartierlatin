# Guide de déploiement

Procédure pas-à-pas pour mettre l'application en ligne. Compte ~15 minutes.

## Étape 1 — Pousser le repo sur GitHub

### 1.1 Créer le dépôt distant

Va sur [github.com/new](https://github.com/new) et crée un nouveau repo :
- **Nom** : `progra-cine-quartierlatin`
- **Visibilité** : Public (obligatoire pour GitHub Pages gratuit)
- **Ne coche pas** "Initialize with README" — on l'a déjà.

### 1.2 Pousser le code

Décompresse le zip puis, dans le dossier `progra-cine-quartierlatin` :

```bash
git init
git add .
git commit -m "Initial commit — scraper + frontend + workflow"
git branch -M main
git remote add origin https://github.com/TON_USER/progra-cine-quartierlatin.git
git push -u origin main
```

Remplace `TON_USER` par ton nom d'utilisateur GitHub.

## Étape 2 — Activer GitHub Pages

1. Sur la page du repo, va dans **Settings** (engrenage en haut).
2. Menu de gauche → **Pages**.
3. Section "Build and deployment" :
   - **Source** : `Deploy from a branch`
   - **Branch** : `main` / dossier `/public`
4. Clique **Save**.

Au bout de 1-2 minutes, l'URL apparaît en haut de la page :
**`https://TON_USER.github.io/progra-cine-quartierlatin/`**

Ouvre-la sur ton iPhone — l'app fonctionne avec les données pré-scrapées du `data.json` initial.

## Étape 3 — Autoriser le workflow à committer

Le scraper a besoin de pouvoir pousser le `data.json` mis à jour.

1. **Settings** → **Actions** → **General**.
2. Section "Workflow permissions" en bas :
   - Coche **Read and write permissions**.
   - Clique **Save**.

## Étape 4 — Premier scraping manuel

1. Onglet **Actions** du repo.
2. Sélectionne **Daily scrape** dans la liste de gauche.
3. Bouton **Run workflow** → laisse `main` → **Run workflow**.

Ça tourne 1-2 minutes. À la fin, un nouveau commit apparaît sur `main` avec
le `data.json` fraîchement scrapé. L'app se met à jour automatiquement sur
GitHub Pages dans la minute qui suit.

## Étape 5 — Installer sur iPhone (PWA)

1. Ouvre l'URL dans **Safari** (pas Chrome ; iOS impose Safari pour la PWA).
2. Touche l'icône **Partager** (la flèche qui sort d'un carré, en bas).
3. Scrolle et touche **Ajouter à l'écran d'accueil**.
4. Touche **Ajouter** en haut à droite.

L'icône Ciné&q apparaît sur ton écran d'accueil. Au lancement, l'app
s'ouvre en plein écran sans la barre Safari — comme une vraie app native.

## Vérifier que tout fonctionne

À partir du lendemain matin, vers 4h30 du matin (heure de Paris), un nouveau
commit `chore(data): scrape ...` doit apparaître automatiquement sur le repo.

Si rien ne se passe :

- **Actions désactivées** : vérifie Settings → Actions → General → "Allow all actions".
- **Workflow en échec** : clique sur le run rouge dans l'onglet Actions pour voir les logs.
- **Slug incorrect** : si un cinéma sort à 0 séances dans tous les runs, son slug
  offi.fr est probablement faux ; édite `scripts/cinemas.json` et corrige.

## Cinémas à vérifier au premier run

Les 4 derniers slugs n'ont pas pu être confirmés à 100 % au moment de la
génération du repo. Le premier `Run workflow` te dira lesquels marchent :

- ✓ Confirmés : Champo, Filmothèque, Reflet, 3 Lux, Grand Action, Studio Galande, La Clef, Nouvel Odéon
- ? À vérifier : Écoles Cinéma Club, Cinéma du Panthéon, Christine Cinéma Club, Saint-André des Arts

Si l'un d'eux retourne "0 séances", trouve son vrai slug en cherchant son
nom sur [offi.fr](https://www.offi.fr/cinema/arrondissements.html) — l'URL
sera de la forme `/cinema/SLUG.html`. Mets à jour `scripts/cinemas.json` et
push.
