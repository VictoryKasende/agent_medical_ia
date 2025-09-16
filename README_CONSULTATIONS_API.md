# 📄 API Fiches de Consultation – Documentation Complète

## Vue d'ensemble

Cette API permet de gérer tout le cycle de vie d'une fiche de consultation médicale : création, modification, validation, rejet, messagerie, attribution à un médecin, relance IA, et envoi WhatsApp.

## 🔐 Authentification

Toutes les requêtes nécessitent un token JWT dans l'en-tête :
```http
Authorization: Bearer <votre_token>
Content-Type: application/json
```

---

## 📋 Endpoints CRUD

### 1. **Lister les fiches de consultation**
```http
GET /api/v1/fiche-consultation/
```

**Paramètres de filtrage** (optionnels) :
- `status` : Filtrer par statut (`en_analyse`, `analyse_terminee`, `valide_medecin`, `rejete_medecin`)
- `medecin` : ID du médecin assigné
- `date_consultation` : Format YYYY-MM-DD
- `is_patient_distance` : `true`/`false` pour les consultations à distance

**Exemple d'URL** :
```
GET /api/v1/fiche-consultation/?status=en_analyse&medecin=3&date_consultation=2025-09-16
```

**Réponse** :
```json
{
    "count": 25,
    "next": "http://api/v1/fiche-consultation/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "nom": "Kabasele",
            "postnom": "Jean",
            "prenom": "Pierre",
            "numero_dossier": "CONS-20250916-001",
            "status": "en_analyse",
            "status_display": "En analyse",
            "date_consultation": "2025-09-16",
            "medecin_validateur": null,
            "assigned_medecin": {
                "id": 3,
                "username": "dr_martin",
                "first_name": "Jean",
                "last_name": "Martin"
            }
        }
    ]
}
```

### 2. **Créer une fiche de consultation**
```http
POST /api/v1/fiche-consultation/
```

**Champs obligatoires** :
```json
{
    "nom": "Kabasele",
    "postnom": "Jean", 
    "prenom": "Pierre",
    "date_naissance": "1990-05-12",
    "age": 35,
    "telephone": "+243123456789",
    "etat_civil": "Célibataire",
    "occupation": "Comptable",
    "avenue": "Avenue Kabasele",
    "quartier": "Gombe",
    "commune": "Gombe",
    "contact_nom": "Marie Kabasele",
    "contact_telephone": "+243987654321",
    "contact_adresse": "Avenue Kabasele, Gombe",
    "etat": "Conservé",
    "capacite_physique": "Top",
    "capacite_psychologique": "Moyen",
    "febrile": "Non",
    "coloration_bulbaire": "Normale",
    "coloration_palpebrale": "Normale",
    "tegument": "Normal"
}
```

**Champs optionnels** (exemples) :
```json
{
    "sexe": "M",
    "motif_consultation": "Douleurs abdominales",
    "histoire_maladie": "Douleurs depuis 3 jours...",
    "temperature": 37.5,
    "poids": 70.5,
    "tension_arterielle": "120/80",
    "pouls": 75,
    "hypertendu": false,
    "diabetique": false,
    "allergie_medicamenteuse": false,
    "is_patient_distance": false
}
```

**Réponse** :
```json
{
    "id": 15,
    "nom": "Kabasele",
    "numero_dossier": "CONS-20250916-015",
    "status": "en_analyse",
    "date_consultation": "2025-09-16",
    "heure_debut": "14:30:00",
    "user": 2,
    "created_at": "2025-09-16T14:30:00Z"
}
```

### 3. **Voir une fiche spécifique**
```http
GET /api/v1/fiche-consultation/{id}/
```

**Réponse complète** avec tous les champs du modèle.

### 4. **Modifier une fiche**
```http
PUT /api/v1/fiche-consultation/{id}/     # Remplace tous les champs
PATCH /api/v1/fiche-consultation/{id}/   # Modifie seulement les champs fournis
```

**Exemple PATCH** :
```json
{
    "motif_consultation": "Mise à jour du motif",
    "temperature": 38.2
}
```

### 5. **Supprimer une fiche**
```http
DELETE /api/v1/fiche-consultation/{id}/
```

---

## 🏥 Actions Avancées

### 1. **Assigner un médecin**
```http
POST /api/v1/fiche-consultation/{id}/assign-medecin/
```

**Payload** :
```json
{
    "medecin_id": 3
}
```

**Permissions** : Staff/Admin uniquement

### 2. **Messagerie sur la fiche**

**Lister les messages** :
```http
GET /api/v1/fiche-consultation/{id}/messages/
```

**Réponse** :
```json
[
    {
        "id": 1,
        "author": {
            "id": 2,
            "username": "patient1",
            "role": "patient"
        },
        "content": "J'ai des questions sur mon traitement",
        "created_at": "2025-09-16T15:00:00Z"
    },
    {
        "id": 2,
        "author": {
            "id": 3,
            "username": "dr_martin",
            "role": "medecin"
        },
        "content": "Je vais vous répondre dans quelques minutes",
        "created_at": "2025-09-16T15:05:00Z"
    }
]
```

**Ajouter un message** :
```http
POST /api/v1/fiche-consultation/{id}/messages/
```

**Payload** :
```json
{
    "content": "Voici ma question concernant le traitement..."
}
```

### 3. **Rejeter une consultation**
```http
POST /api/v1/fiche-consultation/{id}/reject/
```

**Payload** :
```json
{
    "commentaire_rejet": "Informations insuffisantes pour établir un diagnostic. Veuillez compléter l'anamnèse."
}
```

**Permissions** : Médecin assigné ou Staff
**Effet** : Statut passe à `rejete_medecin`

### 4. **Valider une consultation**
```http
POST /api/v1/fiche-consultation/{id}/validate/
```

**Payload** :
```json
{
    "diagnostic": "Gastrite aiguë",
    "traitement": "Oméprazole 20mg 2x/jour pendant 7 jours",
    "examen_complementaire": "Échographie abdominale si persistance des symptômes",
    "recommandations": "Éviter les aliments épicés, repos, hydratation"
}
```

**Permissions** : Médecin assigné
**Effet** : Statut passe à `valide_medecin`, `date_validation` est définie

### 5. **Relancer l'analyse IA**
```http
POST /api/v1/fiche-consultation/{id}/relancer/
```

**Effet** : Déclenche une nouvelle analyse IA asynchrone avec Celery

### 6. **Envoyer via WhatsApp**
```http
POST /api/v1/fiche-consultation/{id}/send-whatsapp/
```

**Payload** (optionnel) :
```json
{
    "message_template": "custom",
    "additional_info": "Information supplémentaire"
}
```

---

## 🔐 Permissions Détaillées

| Action | Patient | Médecin | Staff/Admin |
|--------|---------|---------|-------------|
| Créer fiche | ✅ Ses fiches | ❌ | ✅ |
| Voir fiche | ✅ Ses fiches | ✅ Toutes | ✅ Toutes |
| Modifier fiche | ✅ Ses fiches | ✅ Toutes | ✅ Toutes |
| Supprimer fiche | ✅ Ses fiches | ❌ | ✅ Toutes |
| Assigner médecin | ❌ | ❌ | ✅ |
| Messages | ✅ Ses fiches | ✅ Toutes | ✅ Toutes |
| Valider | ❌ | ✅ Assignées | ✅ |
| Rejeter | ❌ | ✅ Assignées | ✅ |
| Relancer IA | ❌ | ✅ | ✅ |
| WhatsApp | ❌ | ✅ | ✅ |

---

## 🔄 Workflow Complet

### 1. **Création par le patient**
```python
import requests

token = "patient_token"
headers = {"Authorization": f"Bearer {token}"}

data = {
    "nom": "Dupont",
    "postnom": "Jean",
    "prenom": "Pierre",
    # ... champs obligatoires
}

response = requests.post(
    "https://api.example.com/api/v1/fiche-consultation/",
    json=data,
    headers=headers
)
fiche = response.json()
print(f"Fiche créée: {fiche['numero_dossier']}")
```

### 2. **Attribution par l'admin**
```python
admin_headers = {"Authorization": f"Bearer {admin_token}"}

response = requests.post(
    f"https://api.example.com/api/v1/fiche-consultation/{fiche['id']}/assign-medecin/",
    json={"medecin_id": 3},
    headers=admin_headers
)
```

### 3. **Échange de messages**
```python
# Patient ajoute un message
patient_message = {
    "content": "J'ai oublié de mentionner que j'ai des antécédents familiaux de diabète"
}

requests.post(
    f"https://api.example.com/api/v1/fiche-consultation/{fiche['id']}/messages/",
    json=patient_message,
    headers=headers
)

# Médecin répond
medecin_headers = {"Authorization": f"Bearer {medecin_token}"}
medecin_message = {
    "content": "Merci pour cette information importante. Je vais en tenir compte dans mon diagnostic."
}

requests.post(
    f"https://api.example.com/api/v1/fiche-consultation/{fiche['id']}/messages/",
    json=medecin_message,
    headers=medecin_headers
)
```

### 4. **Validation par le médecin**
```python
validation_data = {
    "diagnostic": "Pré-diabète avec syndrome métabolique",
    "traitement": "Metformine 500mg 2x/jour",
    "examen_complementaire": "Glycémie à jeun dans 3 mois",
    "recommandations": "Régime alimentaire, exercice physique 30min/jour"
}

requests.post(
    f"https://api.example.com/api/v1/fiche-consultation/{fiche['id']}/validate/",
    json=validation_data,
    headers=medecin_headers
)
```

### 5. **Envoi WhatsApp**
```python
requests.post(
    f"https://api.example.com/api/v1/fiche-consultation/{fiche['id']}/send-whatsapp/",
    headers=medecin_headers
)
```

---

## 🧪 Exemples avec différents langages

### JavaScript (Fetch API)
```javascript
// Créer une fiche
const createFiche = async (ficheData) => {
    const response = await fetch('/api/v1/fiche-consultation/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(ficheData)
    });
    
    if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
};

// Valider une fiche
const validateFiche = async (ficheId, validationData) => {
    const response = await fetch(`/api/v1/fiche-consultation/${ficheId}/validate/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(validationData)
    });
    
    return await response.json();
};
```

### cURL
```bash
# Créer une fiche
curl -X POST https://api.example.com/api/v1/fiche-consultation/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Dupont",
    "postnom": "Jean",
    "prenom": "Pierre",
    "date_naissance": "1990-01-01",
    "age": 35,
    "telephone": "+243123456789",
    "etat_civil": "Célibataire",
    "occupation": "Ingénieur",
    "avenue": "Av. Kabasele",
    "quartier": "Gombe",
    "commune": "Gombe",
    "contact_nom": "Marie Dupont",
    "contact_telephone": "+243987654321",
    "contact_adresse": "Av. Kabasele, Gombe",
    "etat": "Conservé",
    "capacite_physique": "Top",
    "capacite_psychologique": "Top",
    "febrile": "Non",
    "coloration_bulbaire": "Normale",
    "coloration_palpebrale": "Normale",
    "tegument": "Normal"
  }'

# Lister avec filtres
curl "https://api.example.com/api/v1/fiche-consultation/?status=en_analyse&medecin=3" \
  -H "Authorization: Bearer $TOKEN"

# Valider une fiche
curl -X POST https://api.example.com/api/v1/fiche-consultation/15/validate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "diagnostic": "Hypertension artérielle grade 1",
    "traitement": "Amlodipine 5mg 1x/jour",
    "recommandations": "Surveillance tension, réduction sel"
  }'
```

---

## ⚠️ Gestion des Erreurs

### Codes de statut HTTP
- **200** : Succès
- **201** : Créé avec succès
- **400** : Données invalides
- **401** : Non authentifié
- **403** : Permissions insuffisantes
- **404** : Ressource non trouvée
- **500** : Erreur serveur

### Exemples d'erreurs
```json
// Champs manquants (400)
{
    "nom": ["Ce champ est obligatoire."],
    "telephone": ["Ce champ est obligatoire."]
}

// Permission refusée (403)
{
    "detail": "Vous n'avez pas les permissions nécessaires pour cette action."
}

// Fiche non trouvée (404)
{
    "detail": "Aucun objet FicheConsultation correspondant."
}
```

---

## 📊 Statuts des Fiches

| Statut | Code | Description |
|--------|------|-------------|
| En analyse | `en_analyse` | Fiche créée, en attente d'analyse IA |
| Analyse terminée | `analyse_terminee` | IA a terminé son analyse |
| Validé médecin | `valide_medecin` | Médecin a validé avec diagnostic |
| Rejeté médecin | `rejete_medecin` | Médecin a rejeté avec motif |

---

## 🔧 Conseils d'Intégration

### 1. **Gestion des erreurs côté client**
```javascript
const handleApiCall = async (apiCall) => {
    try {
        const response = await apiCall();
        return { success: true, data: response };
    } catch (error) {
        if (error.response?.status === 401) {
            // Token expiré, rediriger vers login
            window.location.href = '/login';
        }
        return { success: false, error: error.message };
    }
};
```

### 2. **Polling pour les mises à jour**
```javascript
const pollFicheStatus = async (ficheId) => {
    const poll = setInterval(async () => {
        const response = await fetch(`/api/v1/fiche-consultation/${ficheId}/`);
        const fiche = await response.json();
        
        if (fiche.status !== 'en_analyse') {
            clearInterval(poll);
            // Notifier l'utilisateur
            console.log(`Fiche ${ficheId} mise à jour: ${fiche.status}`);
        }
    }, 5000); // Vérifier toutes les 5 secondes
};
```

### 3. **Cache des données**
```javascript
const ficheCache = new Map();

const getFicheWithCache = async (ficheId) => {
    if (ficheCache.has(ficheId)) {
        return ficheCache.get(ficheId);
    }
    
    const response = await fetch(`/api/v1/fiche-consultation/${ficheId}/`);
    const fiche = await response.json();
    
    ficheCache.set(ficheId, fiche);
    setTimeout(() => ficheCache.delete(ficheId), 300000); // Cache 5 minutes
    
    return fiche;
};
```

Cette documentation couvre tous les aspects d'utilisation de l'API des fiches de consultation, des opérations de base aux intégrations avancées.