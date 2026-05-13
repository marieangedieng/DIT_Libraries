# DIT Librairie

DIT Librairie est une application de bibliothèque numérique basée sur une architecture microservices.

Le projet contient :
- un frontend HTML/CSS/JavaScript ;
- des services Django REST pour `livres`, `utilisateurs`, `emprunts` et `statistiques` ;
- un service FastAPI pour les recommandations ;
- une base MySQL via Docker Compose ;
- un pipeline DVC pour versionner les données, le modèle et les métriques.

## Prérequis

Installer :
- Git ;
- Docker Desktop ;
- Docker Compose ;
- Python 3.10 ou plus récent ;
- DVC avec le support Google Drive.

Installation de DVC :

```powershell
python -m pip install "dvc[gdrive]"
```

Vérification :

```powershell
dvc --version
```

## Récupérer le projet

Cloner le dépôt :

```powershell
git clone https://github.com/marieangedieng/DIT_Libraries.git
cd DIT_Libraries
```

Si le projet est déjà cloné :

```powershell
git pull origin main
```

Créer le fichier d’environnement local :

```powershell
Copy-Item .env.example .env
```

## Configuration DVC avec Google Drive

Les fichiers de données volumineux ne sont pas stockés directement dans Git. Git contient seulement les fichiers de suivi DVC :

```text
data/raw/loans.csv.dvc
data/raw/books_catalog.csv.dvc
```

Les vrais fichiers sont stockés dans Google Drive via le remote DVC `stockage_gdrive`.

### 1. Recevoir le fichier JSON du service account

Un membre de l’équipe doit vous transmettre le fichier JSON du service account Google.

Exemple de nom :

```text
dit-librairie-service-account.json
```

Ne jamais commit ce fichier dans Git.

### 2. Placer le fichier JSON dans le projet

Depuis la racine du projet, créer le dossier `secrets` si il n'existe pas déja :

```powershell
New-Item -ItemType Directory -Force secrets
```

Copier le fichier JSON dans ce dossier 


Vérifier que le fichier est bien présent :

```powershell
Test-Path "secrets\dit-librairie-service-account.json"
```

La commande doit retourner :

```text
True
```

Le dossier `secrets` est ignoré par Git pour éviter de publier les clés privées.

### 3. Configurer DVC pour utiliser ce fichier local

Configurer le fichier JSON du service account dans la configuration locale DVC :

```powershell
dvc remote modify --local stockage_gdrive gdrive_use_service_account true
dvc remote modify --local stockage_gdrive gdrive_service_account_json_file_path "secrets\dit-librairie-service-account.json"
dvc remote modify --local stockage_gdrive gdrive_acknowledge_abuse true
```

Cette configuration est écrite dans :

```text
.dvc/config.local
```

Ce fichier est local et ne doit pas être commité.

### 4. Télécharger les données depuis Google Drive

Récupérer toutes les données suivies par DVC :

```powershell
dvc pull
```

Ou récupérer uniquement les fichiers bruts nécessaires au pipeline :

```powershell
dvc pull data/raw/loans.csv data/raw/books_catalog.csv
```

Vérifier que les fichiers ont bien été téléchargés :

```powershell
Test-Path "data\raw\loans.csv"
Test-Path "data\raw\books_catalog.csv"
```

Les deux commandes doivent retourner :

```text
True
True
```

### 5. En cas d’erreur d’accès Google Drive

Si `dvc pull` renvoie une erreur d’autorisation, vérifier que le dossier Google Drive DVC est bien partagé avec l’email du service account.

L’email se trouve dans le fichier JSON, dans le champ :

```json
"client_email": "..."
```

Le dossier Google Drive à partager est celui utilisé par le remote DVC :

```text
gdrive://1EBNyKEMcvo02ES3U_px54d-xgGjCPnFq
```

Donner au service account au minimum le rôle :

```text
Lecteur
```

Utiliser le rôle `Éditeur` seulement si la personne doit aussi exécuter :

```powershell
dvc push
```

## Exécuter le pipeline DVC

Après `dvc pull`, exécuter le pipeline complet :

```powershell
dvc repro
```

Ou exécuter les scripts manuellement :

```powershell
python scripts/preprocess.py
python scripts/train.py
python scripts/evaluate.py
```

Le pipeline produit :

```text
data/processed/loans_clean.csv
models/model.pkl
metrics/metrics.json
```

Consulter les métriques :

```powershell
Get-Content metrics\metrics.json
```

## Lancement de l’application

### Développement

```powershell
docker compose --profile dev up --build
```

Le profil `dev` est celui à utiliser pour travailler sur le projet :
- le code local est monté dans les conteneurs ;
- les fichiers frontend sont pris directement depuis `services/frontend` ;
- Django et FastAPI rechargent plus facilement pendant le développement.

### Production locale

```powershell
docker compose --profile prod up --build
```

## URLs utiles

Frontend :
- Accueil : `http://localhost:8080/index.html`
- Livres : `http://localhost:8080/livres.html`
- Créer un compte : `http://localhost:8080/register.html`
- Connexion : `http://localhost:8080/login.html`
- Mon compte : `http://localhost:8080/account.html`

Back-offices Django :
- Utilisateurs : `http://localhost:8002/admin/`
- Livres : `http://localhost:8001/admin/`
- Emprunts : `http://localhost:8003/admin/`

APIs :
- Livres : `http://localhost:8001/api/`
- Utilisateurs : `http://localhost:8002/api/`
- Emprunts : `http://localhost:8003/api/`
- Statistiques : `http://localhost:8004/api/`
- Recommandation : `http://localhost:8005/`

## Comptes disponibles au démarrage

Ces comptes sont créés automatiquement au lancement du service `utilisateurs`.

### Admin

Utilisable pour :
- le frontend ;
- l’admin Django `utilisateurs` ;
- l’admin Django `livres` ;
- l’admin Django `emprunts`.

Identifiants :
- nom d’utilisateur : `ditadmin`
- email : `admin@dit.local`
- mot de passe : `AdminDIT123!`

### Manager

Utilisable pour le frontend.

Identifiants :
- identifiant : `manager1`
- email : `manager1@dit.local`
- mot de passe : `manager`

Ce compte a le rôle `gestionnaire`.

## Créer un compte manager

L’inscription publique ne permet de créer que des comptes `étudiant` et `professeur`.

Pour créer un nouveau manager :
1. se connecter à `http://localhost:8002/admin/` avec le compte admin ;
2. ouvrir `Utilisateur bibliotheque` ;
3. cliquer sur `Add` ;
4. remplir les informations du compte ;
5. mettre `type_utilisateur = gestionnaire` ;
6. définir un mot de passe dans `mot_de_passe` ;
7. enregistrer.

Le nouveau manager pourra ensuite se connecter sur le frontend avec son email ou son numéro de carte.

## Jenkins

Le pipeline Jenkins utilise :
- Git pour récupérer le dépôt ;
- Docker pour lancer un conteneur Python ;
- DVC pour récupérer les données depuis Google Drive ;
- Docker Compose pour construire les images applicatives.

Dans Jenkins, créer un credential de type `Secret file` pour le JSON Google Drive :

```text
ID: gdrive-dvc-sa
Kind: Secret file
File: dit-librairie-service-account.json
```

Le `Jenkinsfile` utilise ce credential pour configurer DVC localement pendant le build.

## Notes utiles

- Le catalogue est prérempli avec des livres IT de démonstration.
- Les migrations sont exécutées automatiquement au démarrage des services Django.
- Si les dépendances Python ou Docker changent, relancer Docker Compose avec `--build`.
- Si seul le frontend change en mode `dev`, un `Ctrl+F5` suffit généralement dans le navigateur.
- Ne jamais commiter `.env`, `.dvc/config.local`, `secrets/*.json`, `models/model.pkl`, `metrics/metrics.json` ou les CSV téléchargés par DVC.

## Réinitialiser complètement la base

```powershell
docker compose --profile dev down -v
docker compose --profile dev up --build
```

Cela recrée MySQL, relance les migrations et recharge les comptes par défaut.
