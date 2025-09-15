# 🏥 API Consultations Médicales - Guide Complet

Guide détaillé pour utiliser l'API de consultations médicales avec analyse IA intégrée dans Agent Medical IA.

## 📚 Table des matières

- [🔍 Vue d'ensemble](#-vue-densemble)
- [🔐 Authentification](#-authentification) 
- [📋 Endpoints Consultations](#-endpoints-consultations)
- [🤖 Workflow avec IA](#-workflow-avec-ia)
- [💬 Conversations et Messages](#-conversations-et-messages)
- [👥 Gestion des Utilisateurs](#-gestion-des-utilisateurs)
- [📱 Exemples d'implémentation](#-exemples-dimplémentation)
- [⚠️ Gestion d'erreurs](#-gestion-derreurs)

## 🔍 Vue d'ensemble

### Fonctionnalités principales
- ✅ **Création automatique** de fiches de consultation
- ⚙️ **Analyse IA asynchrone** des symptômes avec Celery
- 👨‍⚕️ **Validation/Rejet** par les médecins
- 💬 **Conversations IA** avec historique complet
- 📱 **Consultation à distance** avec workflow simplifié
- 📋 **Gestion complète** des dossiers patients

### Statuts des consultations
- `en_analyse` - Analyse IA en cours
- `analyse_terminee` - IA a terminé l'analyse
- `valide_medecin` - Validée par un médecin
- `rejete_medecin` - Rejetée par un médecin

### Rôles utilisateurs
- **Patient** : Peut voir ses propres consultations
- **Médecin** : Peut valider/rejeter, accès complet IA
- **Admin** : Accès complet à tout le système

## 🔐 Authentification

Toutes les requêtes nécessitent un token JWT valide :

```javascript
headers: {
  'Authorization': 'Bearer <votre_token_jwt>',
  'Content-Type': 'application/json'
}
```

## 📋 Endpoints Consultations

**Base URL** : `/api/v1/fiche-consultation/`

### 1. 🔍 Lister les consultations

**GET** `/api/v1/fiche-consultation/`

**Paramètres de requête :**
- `status` : Filtrer par statut(s) - ex: `?status=en_analyse,valide_medecin`
- `is_patient_distance=true` : Vue simplifiée pour consultations à distance

**Exemples de requêtes :**

```javascript
// Toutes les consultations
const response = await fetch('/api/v1/fiche-consultation/', {
  headers: { 'Authorization': 'Bearer ' + token }
});

// Consultations en analyse uniquement
const response = await fetch('/api/v1/fiche-consultation/?status=en_analyse', {
  headers: { 'Authorization': 'Bearer ' + token }
});

// Vue consultations à distance (serializer léger)
const response = await fetch('/api/v1/fiche-consultation/?is_patient_distance=true', {
  headers: { 'Authorization': 'Bearer ' + token }
});
```

**Réponse normale :**
```json
[
  {
    "id": 1,
    "numero_dossier": "CONS-20250909-001",
    "nom": "Dupont",
    "postnom": "Jean",
    "prenom": "Claude",
    "age": 45,
    "sexe": "M",
    "telephone": "+243900000000",
    "date_consultation": "2025-09-09",
    "status": "analyse_terminee",
    "status_display": "Analyse terminée",
    "motif_consultation": "Maux de tête persistants",
    "histoire_maladie": "Céphalées depuis 3 jours...",
    "temperature": 37.2,
    "tension_arterielle": "120/80",
    "pouls": 75,
    "spo2": 98,
    "diagnostic_ia": "Diagnostic IA complet...",
    "medecin_validateur": null,
    "date_validation": null,
    "created_at": "2025-09-09T10:30:00Z"
  }
]
```

**Réponse vue distance (allégée) :**
```json
[
  {
    "id": 1,
    "nom": "Dupont",
    "prenom": "Claude",
    "age": 45,
    "telephone": "+243900000000",
    "status": "analyse_terminee",
    "status_display": "Analyse terminée",
    "motif_consultation": "Maux de tête persistants",
    "temperature": 37.2,
    "febrile": "Oui",
    "febrile_bool": true,
    "diagnostic_ia": "Diagnostic IA..."
  }
]
```

---

### 2. 📄 Créer une consultation

**POST** `/api/v1/fiche-consultation/`

⚠️ **Important** : La création lance automatiquement une analyse IA asynchrone !

**Données requises (exemple minimal) :**
```json
{
  "nom": "Dupont",
  "postnom": "Jean", 
  "prenom": "Claude",
  "date_naissance": "1980-01-15",
  "age": 45,
  "sexe": "M",
  "telephone": "+243900000000",
  "etat_civil": "Marié(e)",
  "occupation": "Enseignant",
  "avenue": "Avenue de la Paix",
  "quartier": "Gombe",
  "commune": "Kinshasa",
  "contact_nom": "Marie Dupont",
  "contact_telephone": "+243900000001",
  "contact_adresse": "Même adresse",
  "motif_consultation": "Maux de tête persistants depuis 3 jours",
  "histoire_maladie": "Patient se plaint de céphalées intenses...",
  "temperature": 37.2,
  "tension_arterielle": "120/80",
  "pouls": 75,
  "spo2": 98,
  "etat": "Conservé",
  "febrile": "Oui"
}
```

**Données complètes disponibles :**

```json
{
  // === INFORMATIONS PATIENT ===
  "nom": "string",
  "postnom": "string", 
  "prenom": "string",
  "date_naissance": "YYYY-MM-DD",
  "age": 45,
  "sexe": "M|F",
  "telephone": "string",
  "etat_civil": "Célibataire|Marié(e)|Divorcé(e)|Veuf(ve)",
  "occupation": "string",
  
  // === ADRESSE ===
  "avenue": "string",
  "quartier": "string", 
  "commune": "string",
  
  // === CONTACT D'URGENCE ===
  "contact_nom": "string",
  "contact_telephone": "string",
  "contact_adresse": "string",
  
  // === PRÉSENCE LORS CONSULTATION ===
  "patient": true,
  "proche": false,
  "soignant": false,
  "medecin": false,
  "autre": false,
  "proche_lien": "string|null",
  "soignant_role": "string|null",
  "autre_precisions": "string|null",
  
  // === SIGNES VITAUX ===
  "temperature": 37.2,
  "spo2": 98,
  "poids": 70.5,
  "tension_arterielle": "120/80",
  "pouls": 75,
  "frequence_respiratoire": 18,
  
  // === ANAMNÈSE ===
  "motif_consultation": "string",
  "histoire_maladie": "string",
  
  // === MÉDICAMENTS ===
  "maison_medicaments": false,
  "pharmacie_medicaments": false,
  "centre_sante_medicaments": false,
  "hopital_medicaments": false,
  "medicaments_non_pris": false,
  "details_medicaments": "string|null",
  
  // === SYMPTÔMES ===
  "cephalees": true,
  "vertiges": false,
  "palpitations": false,
  "troubles_visuels": false,
  "nycturie": false,
  
  // === ANTÉCÉDENTS MÉDICAUX ===
  "hypertendu": false,
  "diabetique": false,
  "epileptique": false,
  "trouble_comportement": false,
  "gastritique": false,
  
  // === MODE DE VIE ===
  "tabac": "non|rarement|souvent|tres_souvent",
  "alcool": "non|rarement|souvent|tres_souvent",
  "activite_physique": "non|rarement|souvent|tres_souvent",
  "activite_physique_detail": "string|null",
  "alimentation_habituelle": "string|null",
  
  // === ALLERGIES ===
  "allergie_medicamenteuse": false,
  "medicament_allergique": "string|null",
  
  // === ANTÉCÉDENTS FAMILIAUX ===
  "familial_drepanocytaire": false,
  "familial_diabetique": false,
  "familial_obese": false,
  "familial_hypertendu": false,
  "familial_trouble_comportement": false,
  "lien_pere": false,
  "lien_mere": false,
  "lien_frere": false,
  "lien_soeur": false,
  
  // === TRAUMATISMES ===
  "evenement_traumatique": "oui|non|inconnu",
  "trauma_divorce": false,
  "trauma_perte_parent": false,
  "trauma_deces_epoux": false,
  "trauma_deces_enfant": false,
  
  // === EXAMEN CLINIQUE ===
  "etat": "Conservé|Altéré",
  "par_quoi": "string|null",
  "capacite_physique": "Top|Moyen|Bas",
  "capacite_physique_score": "string|null",
  "capacite_psychologique": "Top|Moyen|Bas",
  "capacite_psychologique_score": "string|null",
  "febrile": "Oui|Non",
  "coloration_bulbaire": "Normale|Anormale",
  "coloration_palpebrale": "Normale|Anormale",
  "tegument": "Normal|Anormal",
  
  // === EXAMENS PAR RÉGION ===
  "tete": "string|null",
  "cou": "string|null",
  "paroi_thoracique": "string|null",
  "poumons": "string|null",
  "coeur": "string|null",
  "epigastre_hypochondres": "string|null",
  "peri_ombilical_flancs": "string|null",
  "hypogastre_fosses_iliaques": "string|null",
  "membres": "string|null",
  "colonne_bassin": "string|null",
  "examen_gynecologique": "string|null",
  
  // === EXPÉRIENCE PATIENT ===
  "preoccupations": "string|null",
  "comprehension": "string|null",
  "attentes": "string|null",
  "engagement": "string|null",
  
  // === CONSULTATION À DISTANCE ===
  "is_patient_distance": false,
  
  // === DIAGNOSTIC ET TRAITEMENT ===
  "diagnostic": "string|null",
  "traitement": "string|null",
  "examen_complementaire": "string|null",
  "recommandations": "string|null"
}
```

**Réponse (201 Created) :**
```json
{
  "id": 1,
  "numero_dossier": "CONS-20250909-001",
  "status": "en_analyse",
  "status_display": "En cours d'analyse",
  // ... tous les champs fournis
}
```

---

### 3. 📖 Récupérer une consultation

**GET** `/api/v1/fiche-consultation/{id}/`

**Réponse :**
```json
{
  "id": 1,
  // ... tous les détails complets de la consultation
  "diagnostic_ia": "Analyse complète de l'IA...",
  "medecin_validateur": {
    "id": 2,
    "username": "dr_martin",
    "first_name": "Pierre",
    "last_name": "Martin"
  }
}
```

---

### 4. ✏️ Modifier une consultation

**PUT/PATCH** `/api/v1/fiche-consultation/{id}/`

⚠️ **Note** : Le champ `status` est en lecture seule. Utilisez les actions pour changer le statut.

---

### 5. 🗑️ Supprimer une consultation

**DELETE** `/api/v1/fiche-consultation/{id}/`

---

## 🤖 Actions Spéciales (Workflow IA)

### ✅ Valider une consultation

**POST** `/api/v1/fiche-consultation/{id}/validate/`

**Permissions** : Médecin ou Admin uniquement

**Conditions** : Status doit être `analyse_terminee`, `en_analyse` ou `valide_medecin`

```javascript
const response = await fetch(`/api/v1/fiche-consultation/${id}/validate/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  }
});
```

**Réponse (200 OK) :**
```json
{
  "id": 1,
  "status": "valide_medecin",
  "status_display": "Validé par médecin",
  "medecin_validateur": 2,
  "date_validation": "2025-09-09T15:30:00Z",
  // ... autres champs
}
```

---

### ❌ Rejeter une consultation

**POST** `/api/v1/fiche-consultation/{id}/reject/`

**Permissions** : Médecin ou Admin uniquement

**Conditions** : Status doit être `analyse_terminee` ou `en_analyse`

**Données requises :**
```json
{
  "commentaire": "Motif détaillé du rejet (obligatoire)"
}
```

**Exemple :**
```javascript
const response = await fetch(`/api/v1/fiche-consultation/${id}/reject/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    commentaire: "Informations insuffisantes pour établir un diagnostic"
  })
});
```

**Réponse (200 OK) :**
```json
{
  "id": 1,
  "status": "rejete_medecin",
  "status_display": "Rejeté par médecin",
  "commentaire_rejet": "Informations insuffisantes...",
  "medecin_validateur": 2,
  "date_validation": "2025-09-09T15:30:00Z"
}
```

---

### 🔄 Relancer l'analyse IA

**POST** `/api/v1/fiche-consultation/{id}/relancer/`

**Permissions** : Médecin ou Admin uniquement

Relance l'analyse IA pour une consultation.

```javascript
const response = await fetch(`/api/v1/fiche-consultation/${id}/relancer/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  }
});
```

**Réponse (202 Accepted) :**
```json
{
  "detail": "Analyse relancée",
  "status": "en_analyse"
}
```

---

### 📱 Envoyer template WhatsApp

**POST** `/api/v1/fiche-consultation/{id}/send-whatsapp/`

**Permissions** : Médecin ou Admin uniquement

**Note** : Actuellement un placeholder de simulation.

**Réponse (200 OK) :**
```json
{
  "detail": "Template WhatsApp envoyé (simulation)",
  "fiche": 1
}
```

---

## 💬 Conversations et Messages

### Lister les conversations

**GET** `/api/v1/conversations/`

**Permissions** : Patients voient leurs conversations, médecins voient tout

**Réponse :**
```json
[
  {
    "id": 1,
    "nom": null,
    "titre": "Patient présente des maux...",
    "user": {
      "id": 2,
      "username": "patient1",
      "first_name": "Jean",
      "last_name": "Dupont",
      "role": "patient"
    },
    "fiche": 1,
    "fiche_numero": "CONS-20250909-001",
    "created_at": "2025-09-09T10:30:00Z",
    "updated_at": "2025-09-09T10:35:00Z",
    "messages_count": 3,
    "first_message": "Patient Jean Dupont, 45 ans..."
  }
]
```

### Détails d'une conversation avec messages

**GET** `/api/v1/conversations/{id}/`

**Réponse :**
```json
{
  "id": 1,
  "nom": null,
  "titre": "Patient présente des maux...",
  "user": { /* détails utilisateur */ },
  "fiche": 1,
  "created_at": "2025-09-09T10:30:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Patient Jean Dupont, 45 ans. Motif: Maux de tête...",
      "timestamp": "2025-09-09T10:30:00Z"
    },
    {
      "id": 2,
      "role": "gpt4",
      "content": "Analyse GPT-4: Basé sur les symptômes...",
      "timestamp": "2025-09-09T10:31:00Z"
    },
    {
      "id": 3,
      "role": "claude",
      "content": "Analyse Claude: Diagnostic différentiel...",
      "timestamp": "2025-09-09T10:32:00Z"
    },
    {
      "id": 4,
      "role": "synthese",
      "content": "Synthèse finale des analyses IA...",
      "timestamp": "2025-09-09T10:35:00Z"
    }
  ]
}
```

### Messages d'une conversation

**GET** `/api/v1/conversations/{id}/messages/`

Liste les messages d'une conversation.

**POST** `/api/v1/conversations/{id}/messages/`

Ajoute un message utilisateur.

**Données POST :**
```json
{
  "content": "Nouveau message de l'utilisateur"
}
```

### Rôles des messages
- `user` : Message de l'utilisateur/médecin
- `gpt4` : Réponse de GPT-4
- `claude` : Réponse de Claude 3
- `gemini` : Réponse de Gemini Pro
- `synthese` : Synthèse finale des analyses

---

## 👥 Gestion des Utilisateurs

### Lister les utilisateurs

**GET** `/api/v1/users/`

**Permissions** : Médecin ou Admin uniquement

**Réponse :**
```json
[
  {
    "id": 1,
    "username": "dr_martin",
    "first_name": "Pierre",
    "last_name": "Martin",
    "email": "p.martin@hopital.cd",
    "role": "medecin",
    "is_staff": true
  }
]
```

---

## 🔄 Workflow complet d'une consultation

### 1. Création et analyse automatique
```javascript
// 1. Créer une consultation
const consultation = await fetch('/api/v1/fiche-consultation/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    nom: "Dupont",
    prenom: "Jean",
    age: 45,
    motif_consultation: "Maux de tête",
    // ... autres champs requis
  })
});

// Status initial: "en_analyse"
// L'IA démarre automatiquement l'analyse
```

### 2. Surveillance du statut
```javascript
// 2. Vérifier périodiquement le statut
const checkStatus = async (id) => {
  const response = await fetch(`/api/v1/fiche-consultation/${id}/`);
  const data = await response.json();
  
  if (data.status === 'analyse_terminee') {
    console.log('IA terminée:', data.diagnostic_ia);
    return data;
  }
  
  // Réessayer dans 5 secondes
  setTimeout(() => checkStatus(id), 5000);
};
```

### 3. Validation par médecin
```javascript
// 3. Médecin valide ou rejette
// Validation
await fetch(`/api/v1/fiche-consultation/${id}/validate/`, {
  method: 'POST',
  headers: { 'Authorization': 'Bearer ' + token }
});

// OU Rejet
await fetch(`/api/v1/fiche-consultation/${id}/reject/`, {
  method: 'POST',
  headers: { 
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    commentaire: "Informations insuffisantes"
  })
});
```

---

## 📱 Exemples d'implémentation

### Interface Patient - Liste des consultations

```javascript
class PatientConsultations {
  constructor(apiToken) {
    this.token = apiToken;
    this.baseURL = '/api/v1';
  }

  // Récupérer mes consultations
  async getMyConsultations(status = null) {
    let url = `${this.baseURL}/fiche-consultation/`;
    if (status) {
      url += `?status=${status}`;
    }
    
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }

  // Créer une nouvelle consultation
  async createConsultation(data) {
    const response = await fetch(`${this.baseURL}/fiche-consultation/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      const consultation = await response.json();
      console.log('Consultation créée, analyse IA démarrée:', consultation.id);
      return consultation;
    }
    
    throw new Error('Erreur création consultation');
  }

  // Surveiller le statut d'analyse
  async waitForAnalysis(consultationId, maxAttempts = 30) {
    for (let i = 0; i < maxAttempts; i++) {
      const response = await fetch(`${this.baseURL}/fiche-consultation/${consultationId}/`);
      const data = await response.json();
      
      if (data.status === 'analyse_terminee') {
        return data;
      }
      
      if (data.status === 'valide_medecin' || data.status === 'rejete_medecin') {
        return data;
      }
      
      await new Promise(resolve => setTimeout(resolve, 10000)); // 10s
    }
    
    throw new Error('Timeout: analyse trop longue');
  }

  // Voir la conversation IA
  async getConversation(consultationId) {
    const conversations = await fetch(`${this.baseURL}/conversations/`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    }).then(r => r.json());
    
    const conversation = conversations.find(c => c.fiche === consultationId);
    if (!conversation) return null;
    
    const details = await fetch(`${this.baseURL}/conversations/${conversation.id}/`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    return details.json();
  }
}

// Utilisation
const patient = new PatientConsultations('mon_token_jwt');

// Créer et suivre une consultation
const nouvelleConsultation = await patient.createConsultation({
  nom: "Dupont",
  prenom: "Jean",
  age: 45,
  date_naissance: "1980-01-15",
  telephone: "+243900000000",
  motif_consultation: "Maux de tête persistants",
  temperature: 37.2,
  etat: "Conservé",
  febrile: "Oui"
});

// Attendre l'analyse IA
const analysee = await patient.waitForAnalysis(nouvelleConsultation.id);
console.log('Diagnostic IA:', analysee.diagnostic_ia);

// Voir la conversation IA
const conversation = await patient.getConversation(nouvelleConsultation.id);
console.log('Messages IA:', conversation.messages);
```

### Interface Médecin - Gestion des consultations

```javascript
class MedecinDashboard {
  constructor(apiToken) {
    this.token = apiToken;
    this.baseURL = '/api/v1';
  }

  // Consultations en attente de validation
  async getConsultationsEnAttente() {
    const response = await fetch(
      `${this.baseURL}/fiche-consultation/?status=analyse_terminee`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );
    return response.json();
  }

  // Valider une consultation
  async validerConsultation(id) {
    const response = await fetch(`${this.baseURL}/fiche-consultation/${id}/validate/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    if (response.ok) {
      console.log(`Consultation ${id} validée`);
      return response.json();
    }
    
    throw new Error('Erreur validation');
  }

  // Rejeter une consultation
  async rejeterConsultation(id, motif) {
    const response = await fetch(`${this.baseURL}/fiche-consultation/${id}/reject/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ commentaire: motif })
    });
    
    if (response.ok) {
      console.log(`Consultation ${id} rejetée`);
      return response.json();
    }
    
    throw new Error('Erreur rejet');
  }

  // Relancer analyse IA
  async relancerAnalyse(id) {
    const response = await fetch(`${this.baseURL}/fiche-consultation/${id}/relancer/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    return response.json();
  }

  // Dashboard médecin
  async getDashboardData() {
    const [enAttente, validees, rejetees] = await Promise.all([
      this.getConsultationsEnAttente(),
      fetch(`${this.baseURL}/fiche-consultation/?status=valide_medecin`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }).then(r => r.json()),
      fetch(`${this.baseURL}/fiche-consultation/?status=rejete_medecin`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }).then(r => r.json())
    ]);

    return {
      enAttente: enAttente.length,
      validees: validees.length,
      rejetees: rejetees.length,
      consultations: {
        enAttente,
        validees,
        rejetees
      }
    };
  }
}

// Utilisation
const medecin = new MedecinDashboard('token_medecin');

// Dashboard
const dashboard = await medecin.getDashboardData();
console.log('Consultations en attente:', dashboard.enAttente);

// Workflow validation
const consultationsEnAttente = await medecin.getConsultationsEnAttente();
for (const consultation of consultationsEnAttente) {
  console.log(`Consultation ${consultation.id}:`, consultation.diagnostic_ia);
  
  // Décision médecin
  if (/* critères validation */) {
    await medecin.validerConsultation(consultation.id);
  } else {
    await medecin.rejeterConsultation(consultation.id, "Informations incomplètes");
  }
}
```

---

## ⚠️ Gestion d'erreurs

### Codes d'erreur courants

- **400 Bad Request** : Données invalides ou manquantes
- **401 Unauthorized** : Token invalide ou expiré
- **403 Forbidden** : Permissions insuffisantes (ex: patient tentant de valider)
- **404 Not Found** : Consultation non trouvée
- **409 Conflict** : Statut incompatible pour l'action

### Exemples d'erreurs

**Validation impossible (400) :**
```json
{
  "detail": "Statut incompatible pour validation."
}
```

**Commentaire manquant pour rejet (400) :**
```json
{
  "detail": "Le champ commentaire est requis."
}
```

**Permission refusée (403) :**
```json
{
  "detail": "Vous n'avez pas la permission d'effectuer cette action."
}
```

### Gestion d'erreurs JavaScript

```javascript
async function handleConsultationAction(action) {
  try {
    const response = await fetch(action.url, action.options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 400:
          console.error('Données invalides:', error.detail);
          break;
        case 401:
          console.error('Non authentifié - redirection connexion');
          window.location.href = '/login';
          break;
        case 403:
          console.error('Permission refusée:', error.detail);
          break;
        case 404:
          console.error('Consultation non trouvée');
          break;
        default:
          console.error('Erreur serveur:', error);
      }
      
      throw new Error(error.detail || 'Erreur inconnue');
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Erreur requête:', error);
    throw error;
  }
}
```

---

## 📊 Filtres et recherche avancée

### Filtrage par statuts multiples
```javascript
// Consultations terminées ou validées
const url = '/api/v1/fiche-consultation/?status=analyse_terminee,valide_medecin';
```

### Consultation à distance uniquement
```javascript
// Vue allégée pour téléconsultation
const url = '/api/v1/fiche-consultation/?is_patient_distance=true';
```

### Combinaison de filtres
```javascript
// Consultations distance terminées
const url = '/api/v1/fiche-consultation/?is_patient_distance=true&status=analyse_terminee';
```

---

## 🚀 Optimisations et bonnes pratiques

### 1. **Pagination automatique**
L'API utilise la pagination Django REST Framework automatique.

### 2. **Cache des résultats IA**
Les analyses identiques sont automatiquement mises en cache.

### 3. **Traitement asynchrone**
Toutes les analyses IA sont traitées en arrière-plan avec Celery.

### 4. **Sécurité**
- Authentification JWT obligatoire
- Permissions strictes par rôle
- Validation des données côté serveur

### 5. **Performance**
- Requêtes optimisées avec `select_related`
- Serializers adaptés selon le contexte
- Throttling pour éviter la surcharge

---

## 📝 Résumé des endpoints

| Méthode | Endpoint | Description | Permissions |
|---------|----------|-------------|-------------|
| GET | `/api/v1/fiche-consultation/` | Liste consultations | Authentifié |
| POST | `/api/v1/fiche-consultation/` | Créer consultation | Authentifié |
| GET | `/api/v1/fiche-consultation/{id}/` | Détails consultation | Authentifié |
| PUT/PATCH | `/api/v1/fiche-consultation/{id}/` | Modifier consultation | Authentifié |
| DELETE | `/api/v1/fiche-consultation/{id}/` | Supprimer consultation | Authentifié |
| POST | `/api/v1/fiche-consultation/{id}/validate/` | Valider consultation | Médecin/Admin |
| POST | `/api/v1/fiche-consultation/{id}/reject/` | Rejeter consultation | Médecin/Admin |
| POST | `/api/v1/fiche-consultation/{id}/relancer/` | Relancer analyse IA | Médecin/Admin |
| POST | `/api/v1/fiche-consultation/{id}/send-whatsapp/` | Template WhatsApp | Médecin/Admin |
| GET | `/api/v1/conversations/` | Liste conversations | Authentifié |
| GET | `/api/v1/conversations/{id}/` | Détails conversation | Propriétaire/Médecin |
| GET/POST | `/api/v1/conversations/{id}/messages/` | Messages conversation | Propriétaire/Médecin |
| GET | `/api/v1/users/` | Liste utilisateurs | Médecin/Admin |

**Documentation Swagger disponible** : `/api/docs/`

---

*Cette API est conçue pour une utilisation en production avec toutes les mesures de sécurité et performance nécessaires. Pour plus d'informations, consultez la documentation Swagger intégrée.*
