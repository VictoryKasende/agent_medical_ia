# API IA et Conversations - Guide Synthétique

## 🤖 Endpoints IA (Intelligence Artificielle)

### 1. Démarrer une analyse IA
**POST** `/api/ia/analyse/`

**Permissions** : Médecin uniquement (`IsMedecin`)

Lance une analyse asynchrone des symptômes avec l'IA médicale.

#### Données requises :
```json
{
  "symptomes": "Description des symptômes du patient",
  "conversation_id": 123  // Optionnel, sinon nouvelle conversation
}
```

#### Réponse (202 Accepted) :
```json
{
  "task_id": null,
  "cache_key": "diagnostic_abc123def456",
  "status": "pending"
}
```

#### Si déjà en cache :
```json
{
  "already_cached": true,
  "cache_key": "diagnostic_abc123def456", 
  "status": "done",
  "response": "Diagnostic IA complet..."
}
```

---

### 2. Vérifier le statut d'une tâche
**GET** `/api/ia/status/{task_id}/`

**Permissions** : Médecin uniquement

Vérifie l'état d'exécution d'une tâche Celery.

#### Réponse :
```json
{
  "task_id": "celery-task-id-12345",
  "state": "SUCCESS",  // PENDING, SUCCESS, FAILURE
  "info": "Information supplémentaire ou erreur"
}
```

---

### 3. Récupérer le résultat d'analyse
**GET** `/api/ia/result/?cache_key=diagnostic_abc123def456`

**Permissions** : Médecin uniquement

Récupère le résultat d'une analyse IA terminée.

#### Paramètres :
- `cache_key` (requis) : Clé retournée lors du démarrage

#### Réponse si terminé :
```json
{
  "status": "done",
  "response": "Diagnostic détaillé de l'IA médicale...",
  "cache_key": "diagnostic_abc123def456"
}
```

#### Réponse si en cours :
```json
{
  "status": "pending",
  "response": "",
  "cache_key": "diagnostic_abc123def456"
}
```

---

## 💬 Endpoints Conversations

### 1. Lister les conversations
**GET** `/api/v1/conversations/`

**Permissions** : Authentifié (patients voient seulement les leurs)

#### Réponse :
```json
[
  {
    "id": 1,
    "user": 2,
    "fiche": 5,
    "created_at": "2025-09-02T10:00:00Z"
  }
]
```

---

### 2. Créer une conversation
**POST** `/api/v1/conversations/`

**Permissions** : Authentifié

#### Données :
```json
{
  "fiche": 5  // ID de la fiche de consultation (optionnel)
}
```

---

### 3. Détails d'une conversation
**GET** `/api/v1/conversations/{id}/`

**Permissions** : Propriétaire ou médecin/admin

#### Réponse (avec messages) :
```json
{
  "id": 1,
  "user": 2,
  "fiche": 5,
  "created_at": "2025-09-02T10:00:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Patient présente des maux de tête...",
      "timestamp": "2025-09-02T10:01:00Z"
    },
    {
      "id": 2,
      "role": "assistant", 
      "content": "Analyse IA: Possible migraine...",
      "timestamp": "2025-09-02T10:02:00Z"
    }
  ]
}
```

---

### 4. Messages d'une conversation
**GET** `/api/v1/conversations/{id}/messages/`

Liste tous les messages de la conversation.

**POST** `/api/v1/conversations/{id}/messages/`

Ajoute un nouveau message utilisateur.

#### POST - Données :
```json
{
  "content": "Nouveau message utilisateur"
}
```

#### Réponse GET/POST :
```json
[
  {
    "id": 1,
    "conversation": 1,
    "role": "user",  // "user" ou "assistant"
    "content": "Contenu du message",
    "timestamp": "2025-09-02T10:01:00Z"
  }
]
```

---

### 5. Lister tous les messages
**GET** `/api/v1/messages/`

**Permissions** : Patients voient leurs messages, médecins voient tout

#### Réponse :
```json
[
  {
    "id": 1,
    "conversation": 1,
    "role": "user",
    "content": "Message",
    "timestamp": "2025-09-02T10:01:00Z"
  }
]
```

---

### 6. Détail d'un message
**GET** `/api/v1/messages/{id}/`

**Permissions** : Propriétaire ou médecin/admin

---

## 🏥 Consultations avec IA intégrée

### Créer une fiche de consultation
**POST** `/api/v1/fiche-consultation/`

Créer une fiche lance automatiquement une analyse IA.

### Actions sur les fiches

#### Valider une consultation
**POST** `/api/v1/fiche-consultation/{id}/validate/`
**Permissions** : Médecin/Admin

#### Rejeter une consultation  
**POST** `/api/v1/fiche-consultation/{id}/reject/`
**Permissions** : Médecin/Admin

```json
{
  "commentaire": "Motif du rejet"
}
```

#### Relancer l'analyse IA
**POST** `/api/v1/fiche-consultation/{id}/relancer/`
**Permissions** : Médecin/Admin

---

## 🔄 Workflow typique

### 1. Analyse directe (Médecin)
```bash
# 1. Démarrer analyse
POST /api/ia/analyse/
{
  "symptomes": "Patient de 45 ans, maux de tête persistants..."
}

# 2. Récupérer résultat  
GET /api/ia/result/?cache_key=diagnostic_abc123def456
```

### 2. Via fiche de consultation
```bash
# 1. Créer fiche (analyse auto)
POST /api/v1/fiche-consultation/
{
  "nom": "Dupont",
  "age": 45,
  "motif_consultation": "Maux de tête",
  ...
}

# 2. Voir la conversation générée
GET /api/v1/conversations/{id}/

# 3. Valider/rejeter
POST /api/v1/fiche-consultation/{id}/validate/
```

## 🛡️ Permissions

- **Patients** : Voient leurs propres conversations et messages
- **Médecins** : Accès complet IA + toutes conversations
- **Admin** : Accès complet

## ⚡ Exemples JavaScript

```javascript
class MedicalAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }

  // Analyse IA directe
  async analyseSymptomes(symptomes, conversationId = null) {
    const response = await fetch(`${this.baseURL}/api/ia/analyse/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        symptomes,
        conversation_id: conversationId
      })
    });
    return response.json();
  }

  // Récupérer résultat
  async getAnalyseResult(cacheKey) {
    const response = await fetch(
      `${this.baseURL}/api/ia/result/?cache_key=${cacheKey}`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );
    return response.json();
  }

  // Conversations
  async getConversations() {
    const response = await fetch(`${this.baseURL}/api/v1/conversations/`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }

  // Messages d'une conversation
  async getMessages(conversationId) {
    const response = await fetch(
      `${this.baseURL}/api/v1/conversations/${conversationId}/messages/`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );
    return response.json();
  }

  // Ajouter un message
  async addMessage(conversationId, content) {
    const response = await fetch(
      `${this.baseURL}/api/v1/conversations/${conversationId}/messages/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
      }
    );
    return response.json();
  }
}

// Utilisation
const api = new MedicalAPI('https://votre-domaine.com', 'votre_token');

// Workflow complet
async function analyseComplete() {
  // 1. Lancer analyse
  const analyse = await api.analyseSymptomes(
    "Patient de 30 ans avec fièvre et toux depuis 3 jours"
  );
  
  // 2. Attendre et récupérer résultat
  let resultat;
  do {
    await new Promise(resolve => setTimeout(resolve, 2000)); // 2s
    resultat = await api.getAnalyseResult(analyse.cache_key);
  } while (resultat.status === 'pending');
  
  console.log('Diagnostic IA:', resultat.response);
}
```

## 📝 Notes importantes

- **Cache** : Les analyses identiques sont mises en cache
- **Asynchrone** : Les analyses IA sont traitées en arrière-plan avec Celery  
- **Throttling** : Limitation du taux de requêtes pour éviter la surcharge
- **Permissions strictes** : Seuls les médecins peuvent utiliser l'IA
- **Intégration automatique** : Créer une fiche lance automatiquement l'analyse IA
