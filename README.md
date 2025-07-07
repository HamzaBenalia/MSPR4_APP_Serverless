# 🔐 COFRAP User Authentication System (PoC)

## 🌍 Présentation

Ce projet est un **Proof of Concept (PoC)** développé pour la **COFRAP** (Compagnie Française de Réalisation d'Applicatifs Professionnels), entreprise spécialisée dans les applicatifs Web de gestion d'entreprise.

Dans un contexte de **renforcement de la sécurité des comptes utilisateurs** sur l'infrastructure cloud de la COFRAP, cette solution a pour but de :

- Générer automatiquement des mots de passe complexes,
- Activer une authentification double facteur (2FA) obligatoire,
- Assurer la rotation automatique des mots de passe et secrets 2FA tous les 6 mois,
- Authentifier un utilisateur via mot de passe et 2FA,
- Détecter et gérer les comptes expirés.

---

## 🧩 Fonctionnalités Implémentées

| Fonction | Description |
|---------|-------------|
| 🔑 Génération de mot de passe (`generate-password`) | Génère un mot de passe complexe (24 caractères, maj/min, chiffres, spéciaux) + QRCode à usage unique |
| 🕵️ Génération de secret 2FA (`generate-2fa`) | Crée un secret TOTP 2FA + QRCode associé |
| ✅ Authentification utilisateur (`authenticate-user`) | Authentifie un utilisateur avec son mot de passe + code 2FA et gère l'expiration |

---

## 🛠️ Stack Technique

| Composant | Technologie |
|----------|-------------|
| Langage | Python 3.x |
| Base de données | PostgreSQL (via Docker) |
| 2FA | `pyotp`, `qrcode` |
| Chiffrement | `cryptography` (Fernet) |
| Déploiement FaaS | OpenFaaS (via Minikube) |
| Test unitaire | `unittest`, `pytest`, `unittest.mock` |
| Interface utilisateur | HTML/CSS simple (autre équipe en charge de la sécurité frontend) |

---

## 🗃️ Modèle de Données

Une seule table `users` :

| Champ | Type | Description |
|-------|------|-------------|
| `id` | INT | Identifiant utilisateur |
| `username` | TEXT | Login de l'utilisateur |
| `password` | TEXT | Mot de passe chiffré (Fernet) |
| `mfa` | TEXT | Secret TOTP chiffré |
| `gen_date` | TIMESTAMP | Date de création des identifiants |
| `expired` | BOOLEAN | Statut d’expiration (true/false) |

---

## 🚀 Installation et Lancement

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/cofrap-auth-system.git
cd cofrap-auth-system
```

### 2. Configuration

Créer un fichier `.env` avec :

```
FERNET_KEY=VOTRE_CLE_FERNET
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 3. Lancer la base PostgreSQL (via Docker)

```bash
docker run --name cofrap-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
```

Créer la table `users` manuellement ou via script SQL fourni (`db/schema.sql`).

### 4. Déploiement avec OpenFaaS (via Minikube)

- Lancer Minikube :
```bash
minikube start --driver=docker
```

- Installer OpenFaaS :
```bash
arkade install openfaas
```

- Déployer les fonctions :
```bash
faas-cli deploy -f stack.yml
```

---

## 🧪 Tests

### Test unitaire local de la vérification d’expiration :

```bash
python3 test_handler.py
```

> ✅ Vérifie qu’un compte avec identifiants vieux de plus de 6 mois est bien marqué comme expiré.

---

## 🧾 Exemple de flux utilisateur

1. Un utilisateur appelle la fonction `generate-password`
2. Un mot de passe et un QR Code sont générés et stockés chiffrés
3. Ensuite, `generate-2fa` génère le QR Code et le secret 2FA
4. À la connexion, l’utilisateur utilise `authenticate-user` :
   - Vérification mot de passe + code TOTP
   - Expiration vérifiée (6 mois)
   - Si expiré, relance de `generate-password` + `generate-2fa`

---

## 🔒 Sécurité

- Chiffrement des données sensibles via Fernet (`cryptography`)
- QRCode unique pour le mot de passe initial
- Authentification 2FA obligatoire (TOTP)
- Rotation obligatoire tous les 6 mois
- Projet conforme aux bonnes pratiques recommandées par la COFRAP

---

## 📦 À venir

- Intégration continue avec GitHub Actions
- Documentation OpenAPI pour les fonctions
- Sécurisation du frontend par l’équipe partenaire

---

## 👨‍💻 Auteur

Projet développé par l’équipe COFRAP PoC - 2025  
 
**Langage principal : Python** 🐍

---

## 📄 Licence

Ce projet est sous licencev HENA.
