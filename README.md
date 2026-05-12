# DIT Librairie

Application de bibliothèque numérique en microservices avec :
- frontend HTML/CSS/JavaScript
- services Django pour `livres`, `utilisateurs`, `emprunts`, `statistiques`
- service FastAPI pour les recommandations
- MySQL via Docker Compose

## Installation

Pré-requis :
- Docker Desktop
- Docker Compose

Depuis la racine du projet :

```powershell
Copy-Item .env.example .env
```

## Lancement

### Développement

```powershell
docker compose --profile dev up --build
```

Le profil `dev` est celui à utiliser pour travailler sur le projet :
- le code local est monté dans les conteneurs
- les fichiers frontend sont pris directement depuis `services/frontend`
- Django et FastAPI rechargent plus facilement pendant le développement

### Production locale

```powershell
docker compose --profile prod up --build
```

## URLs utiles

- Frontend : `http://localhost:8080`
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
- le frontend
- l’admin Django `utilisateurs`
- l’admin Django `livres`
- l’admin Django `emprunts`

Identifiants :
- nom d’utilisateur : `ditadmin`
- email : `admin@dit.local`
- mot de passe : `AdminDIT123!`

### Manager

Utilisable pour :
- le frontend

Identifiants :
- identifiant : `manager1`
- email : `manager1@dit.local`
- mot de passe : `manager`

Ce compte a le rôle `gestionnaire`.

## Créer un compte manager

L’inscription publique ne permet de créer que des comptes `étudiant` et `professeur`.

Pour créer un nouveau manager :
1. connecte-toi à `http://localhost:8002/admin/` avec le compte admin
2. ouvre `Utilisateur bibliotheque`
3. clique sur `Add`
4. remplis les informations du compte
5. mets `type_utilisateur = gestionnaire`
6. définis un mot de passe dans `mot_de_passe`
7. enregistre

Le nouveau manager pourra ensuite se connecter sur le frontend avec :
- son email
- ou son numéro de carte

## Notes utiles

- Le catalogue est prérempli avec des livres IT de démonstration.
- Les migrations sont exécutées automatiquement au démarrage des services Django.
- Si tu modifies les dépendances Python ou Docker, relance avec `--build`.
- Si tu modifies uniquement le frontend en mode `dev`, un `Ctrl+F5` suffit en général.

## Réinitialiser complètement la base

```powershell
docker compose --profile dev down -v
docker compose --profile dev up --build
```

Cela recrée MySQL, relance les migrations et recharge les comptes par défaut.
