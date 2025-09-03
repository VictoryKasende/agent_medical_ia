# API d'Authentification - Agent Medical IA

Ce guide vous explique comment utiliser l'API d'authentification pour enregistrer et authentifier vos utilisateurs dans l'application Agent Medical IA.

## 📋 Vue d'ensemble

L'API utilise l'authentification JWT (JSON Web Tokens) et supporte deux types d'utilisateurs :
- **Patient** : Utilisateurs standard
- **Médecin** : Professionnels de santé

**Base URL** : `https://votre-domaine.com/api/v1/auth/`

## 🔑 Endpoints disponibles

### 1. Enregistrement d'un utilisateur

**POST** `/api/v1/auth/users/register/`

Crée un nouveau compte utilisateur (patient ou médecin).

#### Données requises :
```json
{
  "username": "nom_utilisateur",
  "password": "mot_de_passe_minimum_4_caracteres",
  "email": "email@exemple.com",
  "role": "patient",  // ou "medecin"
  "first_name": "Prénom",
  "last_name": "Nom"
}
```

#### Exemple de requête :
```bash
curl -X POST https://votre-domaine.com/api/v1/auth/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jean_dupont",
    "password": "motdepasse123",
    "email": "jean.dupont@email.com",
    "role": "patient",
    "first_name": "Jean",
    "last_name": "Dupont"
  }'
```

#### Réponse (201 Created) :
```json
{
  "id": 1,
  "username": "jean_dupont",
  "email": "jean.dupont@email.com",
  "role": "patient",
  "first_name": "Jean",
  "last_name": "Dupont"
}
```

---

### 2. Connexion (Obtenir un token)

**POST** `/api/v1/auth/token/`

Authentifie un utilisateur et retourne les tokens JWT.

#### Données requises :
```json
{
  "username": "nom_utilisateur",
  "password": "mot_de_passe"
}
```

#### Exemple de requête :
```bash
curl -X POST https://votre-domaine.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jean_dupont",
    "password": "motdepasse123"
  }'
```

#### Réponse (200 OK) :
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### 3. Rafraîchir le token

**POST** `/api/v1/auth/refresh/`

Renouvelle le token d'accès en utilisant le refresh token.

#### Données requises :
```json
{
  "refresh": "votre_refresh_token"
}
```

#### Exemple de requête :
```bash
curl -X POST https://votre-domaine.com/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

#### Réponse (200 OK) :
```json
{
  "access": "nouveau_access_token"
}
```

---

### 4. Vérifier un token

**POST** `/api/v1/auth/verify/`

Vérifie la validité d'un token d'accès.

#### Données requises :
```json
{
  "token": "votre_access_token"
}
```

---

### 5. Profil utilisateur

**GET** `/api/v1/auth/users/me/`

Récupère les informations du profil de l'utilisateur connecté.

#### Exemple de requête :
```bash
curl -X GET https://votre-domaine.com/api/v1/auth/users/me/ \
  -H "Authorization: Bearer votre_access_token"
```

#### Réponse (200 OK) :
```json
{
  "id": 1,
  "username": "jean_dupont",
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@email.com",
  "role": "patient",
  "phone": null,
  "is_active": true,
  "date_joined": "2025-09-02T10:00:00Z",
  "patient_profile": null,
  "medecin_profile": null
}
```

---

### 6. Modifier le profil

**PATCH** `/api/v1/auth/users/me/`

Modifie les informations du profil (champs autorisés : first_name, last_name, email).

#### Exemple de requête :
```bash
curl -X PATCH https://votre-domaine.com/api/v1/auth/users/me/ \
  -H "Authorization: Bearer votre_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jean-Claude",
    "email": "jean-claude.dupont@email.com"
  }'
```

---

### 7. Déconnexion

**POST** `/api/v1/auth/logout/`

Déconnecte l'utilisateur (blacklist le refresh token si configuré).

#### Exemple de requête :
```bash
curl -X POST https://votre-domaine.com/api/v1/auth/logout/ \
  -H "Authorization: Bearer votre_access_token"
```

---

## 🔒 Authentification des requêtes

Pour accéder aux endpoints protégés, incluez le token d'accès dans l'en-tête Authorization :

```
Authorization: Bearer votre_access_token
```

## ⚡ Exemple d'implémentation côté client

### JavaScript/Fetch

```javascript
class AuthAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  // Enregistrement
  async register(userData) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/users/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });
    return response.json();
  }

  // Connexion
  async login(username, password) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/token/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      this.token = data.access;
      return data;
    }
    throw new Error('Erreur de connexion');
  }

  // Récupérer le profil
  async getProfile() {
    const response = await fetch(`${this.baseURL}/api/v1/auth/users/me/`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
      }
    });
    return response.json();
  }

  // Rafraîchir le token
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch(`${this.baseURL}/api/v1/auth/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken })
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      this.token = data.access;
      return data;
    }
    throw new Error('Impossible de rafraîchir le token');
  }

  // Déconnexion
  async logout() {
    await fetch(`${this.baseURL}/api/v1/auth/logout/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      }
    });
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.token = null;
  }
}

// Utilisation
const auth = new AuthAPI('https://votre-domaine.com');

// Exemple d'enregistrement
auth.register({
  username: 'nouveau_user',
  password: 'motdepasse123',
  email: 'user@email.com',
  role: 'patient',
  first_name: 'Prénom',
  last_name: 'Nom'
});
```

### Python/Requests

```python
import requests

class AuthAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None

    def register(self, user_data):
        """Enregistrer un nouvel utilisateur"""
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/users/register/",
            json=user_data
        )
        return response.json()

    def login(self, username, password):
        """Se connecter et obtenir les tokens"""
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/token/",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            return data
        else:
            raise Exception('Erreur de connexion')

    def get_profile(self):
        """Récupérer le profil utilisateur"""
        response = self.session.get(
            f"{self.base_url}/api/v1/auth/users/me/"
        )
        return response.json()

    def logout(self):
        """Se déconnecter"""
        self.session.post(f"{self.base_url}/api/v1/auth/logout/")
        self.token = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']

# Utilisation
auth = AuthAPI('https://votre-domaine.com')

# Enregistrement
user_data = {
    'username': 'nouveau_user',
    'password': 'motdepasse123',
    'email': 'user@email.com',
    'role': 'patient',
    'first_name': 'Prénom',
    'last_name': 'Nom'
}
auth.register(user_data)

# Connexion
auth.login('nouveau_user', 'motdepasse123')

# Récupérer le profil
profile = auth.get_profile()
print(profile)
```

## 📝 Codes d'erreur courants

- **400 Bad Request** : Données invalides ou manquantes
- **401 Unauthorized** : Token invalide ou expiré
- **403 Forbidden** : Permissions insuffisantes
- **404 Not Found** : Utilisateur non trouvé
- **409 Conflict** : Email ou username déjà utilisé

## 🔐 Sécurité

1. **Tokens JWT** : Les tokens d'accès ont une durée de vie limitée
2. **HTTPS uniquement** : Utilisez toujours HTTPS en production
3. **Stockage sécurisé** : Stockez les tokens de manière sécurisée côté client
4. **Validation** : Les mots de passe doivent faire au minimum 4 caractères

## 📊 Gestion des rôles

- **patient** : Accès standard aux fonctionnalités patient
- **medecin** : Accès aux fonctionnalités médicales avancées

Les permissions sont automatiquement gérées selon le rôle de l'utilisateur.

---

*Pour plus d'informations, consultez la documentation Swagger à `/api/docs/`*
