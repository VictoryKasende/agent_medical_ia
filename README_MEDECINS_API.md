# 👨‍⚕️ API Médecins - Documentation

## Vue d'ensemble

L'API médecins permet aux patients authentifiés de consulter la liste des médecins disponibles sur la plateforme, leurs spécialités et leurs informations de contact pour faciliter la prise de rendez-vous.

## 🔐 Permissions

**Accès réservé** : Patients authentifiés uniquement
- Les médecins ne peuvent pas voir la liste d'autres médecins
- Seuls les patients peuvent consulter ces endpoints pour choisir leur médecin

## 📋 Endpoints Disponibles

### 1. **Lister tous les médecins**
```http
GET /api/v1/auth/medecins/
```

**Description** : Récupère la liste complète des médecins inscrits sur la plateforme.

**Paramètres de filtrage** (optionnels) :
- `available` : Filtrer par disponibilité (`true`/`false`)
- `specialty` : Filtrer par spécialité (recherche insensible à la casse)

**Exemples d'utilisation** :
```bash
# Tous les médecins
GET /api/v1/auth/medecins/

# Seulement les médecins disponibles
GET /api/v1/auth/medecins/?available=true

# Médecins spécialisés en cardiologie
GET /api/v1/auth/medecins/?specialty=cardiologie

# Cardiologues disponibles
GET /api/v1/auth/medecins/?available=true&specialty=cardiologie
```

**Réponse JSON** :
```json
{
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 3,
            "username": "dr_martin",
            "first_name": "Jean",
            "last_name": "Martin",
            "email": "dr.martin@hopital.com",
            "role": "medecin",
            "phone": "+243123456789",
            "patient_profile": null,
            "medecin_profile": {
                "id": 1,
                "specialty": "Cardiologie",
                "phone_number": "+243987654321",
                "address": "Cabinet Médical, Av. Kabasele, Kinshasa",
                "is_available": true
            }
        },
        {
            "id": 5,
            "username": "dr_louise",
            "first_name": "Marie",
            "last_name": "Louise",
            "email": "dr.louise@clinique.cd",
            "role": "medecin",
            "phone": "+243111222333",
            "patient_profile": null,
            "medecin_profile": {
                "id": 2,
                "specialty": "Pédiatrie",
                "phone_number": "+243444555666",
                "address": "Clinique Pédiatrique, Bd. Lumumba, Kinshasa",
                "is_available": false
            }
        }
    ]
}
```

### 2. **Voir un médecin spécifique**
```http
GET /api/v1/auth/medecins/{id}/
```

**Description** : Récupère les détails complets d'un médecin par son ID.

**Exemple** :
```bash
GET /api/v1/auth/medecins/3/
```

**Réponse JSON** :
```json
{
    "id": 3,
    "username": "dr_martin",
    "first_name": "Jean",
    "last_name": "Martin",
    "email": "dr.martin@hopital.com",
    "role": "medecin",
    "phone": "+243123456789",
    "patient_profile": null,
    "medecin_profile": {
        "id": 1,
        "specialty": "Cardiologie",
        "phone_number": "+243987654321",
        "address": "Cabinet Médical, Av. Kabasele, Kinshasa",
        "is_available": true
    }
}
```

### 3. **Lister uniquement les médecins disponibles**
```http
GET /api/v1/auth/medecins/available/
```

**Description** : Raccourci pour obtenir seulement les médecins marqués comme disponibles (`is_available=true`).

**Équivalent à** : `GET /api/v1/auth/medecins/?available=true`

**Utilisation recommandée** : Interface de sélection de médecin pour prise de rendez-vous.

## 💻 Exemples d'Implémentation

### Frontend - Sélecteur de médecins

```javascript
// Récupérer tous les médecins disponibles
const getAvailableDoctors = async () => {
    const response = await fetch('/api/v1/auth/medecins/available/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        }
    });
    
    if (response.ok) {
        const doctors = await response.json();
        return doctors.results || doctors;
    }
    throw new Error('Erreur lors du chargement des médecins');
};

// Affichage dans une interface de sélection
const displayDoctorSelector = (doctors) => {
    const doctorSelect = document.getElementById('doctor-select');
    
    doctors.forEach(doctor => {
        const option = document.createElement('option');
        option.value = doctor.id;
        option.textContent = `Dr ${doctor.first_name} ${doctor.last_name} - ${doctor.medecin_profile?.specialty || 'Généraliste'}`;
        doctorSelect.appendChild(option);
    });
};

// Recherche par spécialité
const searchDoctorsBySpecialty = async (specialty) => {
    const response = await fetch(`/api/v1/auth/medecins/?available=true&specialty=${encodeURIComponent(specialty)}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        }
    });
    
    return await response.json();
};
```

### Interface utilisateur - Composant React

```jsx
import React, { useState, useEffect } from 'react';

const DoctorSelector = ({ onSelectDoctor }) => {
    const [doctors, setDoctors] = useState([]);
    const [filteredDoctors, setFilteredDoctors] = useState([]);
    const [specialtyFilter, setSpecialtyFilter] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDoctors();
    }, []);

    useEffect(() => {
        filterDoctors();
    }, [doctors, specialtyFilter]);

    const loadDoctors = async () => {
        try {
            const response = await fetch('/api/v1/auth/medecins/available/');
            const data = await response.json();
            setDoctors(data.results || data);
        } catch (error) {
            console.error('Erreur chargement médecins:', error);
        } finally {
            setLoading(false);
        }
    };

    const filterDoctors = () => {
        if (!specialtyFilter) {
            setFilteredDoctors(doctors);
            return;
        }
        
        const filtered = doctors.filter(doctor => 
            doctor.medecin_profile?.specialty?.toLowerCase()
                .includes(specialtyFilter.toLowerCase())
        );
        setFilteredDoctors(filtered);
    };

    if (loading) return <div>Chargement des médecins...</div>;

    return (
        <div className="doctor-selector">
            <div className="filter-section">
                <input
                    type="text"
                    placeholder="Filtrer par spécialité..."
                    value={specialtyFilter}
                    onChange={(e) => setSpecialtyFilter(e.target.value)}
                    className="specialty-filter"
                />
            </div>
            
            <div className="doctors-grid">
                {filteredDoctors.map(doctor => (
                    <div key={doctor.id} className="doctor-card">
                        <h3>Dr {doctor.first_name} {doctor.last_name}</h3>
                        <p className="specialty">
                            {doctor.medecin_profile?.specialty || 'Médecine générale'}
                        </p>
                        <p className="contact">
                            📞 {doctor.medecin_profile?.phone_number}
                        </p>
                        <p className="address">
                            📍 {doctor.medecin_profile?.address}
                        </p>
                        <button 
                            onClick={() => onSelectDoctor(doctor)}
                            className="select-button"
                        >
                            Choisir ce médecin
                        </button>
                    </div>
                ))}
            </div>
            
            {filteredDoctors.length === 0 && (
                <p className="no-results">Aucun médecin trouvé pour cette spécialité.</p>
            )}
        </div>
    );
};

export default DoctorSelector;
```

## 📊 Structure des Données

### Profil Médecin (`medecin_profile`)
```json
{
    "id": 1,
    "specialty": "Spécialité médicale",
    "phone_number": "Numéro de téléphone professionnel",
    "address": "Adresse du cabinet/clinique",
    "is_available": "Disponibilité pour nouveaux patients (boolean)"
}
```

### Spécialités Communes
- Médecine générale
- Cardiologie
- Pédiatrie
- Gynécologie
- Dermatologie
- Neurologie
- Psychiatrie
- Chirurgie générale
- Ophtalmologie
- ORL (Oto-rhino-laryngologie)

## 🔍 Cas d'Usage

### 1. **Sélection pour Rendez-vous**
```javascript
// Workflow complet : sélection médecin → création RDV
const bookAppointmentWorkflow = async (appointmentData) => {
    // 1. Charger médecins disponibles
    const doctors = await fetch('/api/v1/auth/medecins/available/').then(r => r.json());
    
    // 2. Patient sélectionne un médecin
    const selectedDoctor = doctors.results[0]; // Exemple
    
    // 3. Créer le rendez-vous
    const appointment = await fetch('/api/v1/chat/appointments/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ...appointmentData,
            // Le médecin sera assigné par l'admin plus tard
            message_patient: `Demande RDV avec Dr ${selectedDoctor.first_name} ${selectedDoctor.last_name}`
        })
    });
    
    return appointment.json();
};
```

### 2. **Recherche Avancée**
```javascript
// Interface de recherche avancée
const advancedDoctorSearch = async (filters) => {
    const params = new URLSearchParams();
    
    if (filters.available !== undefined) {
        params.append('available', filters.available);
    }
    if (filters.specialty) {
        params.append('specialty', filters.specialty);
    }
    
    const url = `/api/v1/auth/medecins/?${params.toString()}`;
    const response = await fetch(url);
    return await response.json();
};

// Utilisation
const results = await advancedDoctorSearch({
    available: true,
    specialty: 'cardiologie'
});
```

## ⚠️ Notes Importantes

1. **Permissions strictes** : Seuls les patients peuvent accéder à ces endpoints
2. **Données publiques limitées** : Seules les informations professionnelles sont exposées
3. **Disponibilité temps réel** : Le champ `is_available` doit être maintenu à jour par les médecins
4. **Pagination** : La liste peut être paginée pour de gros volumes de médecins
5. **Cache recommandé** : Ces données changent peu, un cache côté client est utile

## 🚀 Intégrations Suggérées

- **Système de rendez-vous** : Sélection du médecin avant création RDV
- **Chat médical** : Choisir le médecin pour une consultation
- **Annuaire public** : Page de présentation des médecins
- **Géolocalisation** : Filtrer par proximité (future amélioration)
- **Avis patients** : System de notation (future amélioration)

Cette API fournit une base solide pour permettre aux patients de découvrir et sélectionner les médecins appropriés pour leurs besoins médicaux.
