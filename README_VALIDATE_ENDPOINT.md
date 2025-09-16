# 📋 Endpoint Validation de Consultation

## Vue d'ensemble

L'endpoint `POST /api/v1/fiche-consultation/{id}/validate/` permet aux médecins de valider une fiche de consultation en ajoutant leur diagnostic, traitement et recommandations.

---

## 🔗 Endpoint

```http
POST /api/v1/fiche-consultation/{id}/validate/
```

**Permissions** : Médecin assigné à la fiche ou Staff/Admin

---

## 📝 Payload requis

```json
{
    "diagnostic": "Gastrite aiguë",
    "traitement": "Oméprazole 20mg 2x/jour pendant 7 jours",
    "examen_complementaire": "Échographie abdominale si persistance des symptômes",
    "recommandations": "Éviter les aliments épicés, repos, hydratation"
}
```

### Champs
- **diagnostic** (obligatoire) : Diagnostic médical établi
- **traitement** (optionnel) : Prescription médicamenteuse
- **examen_complementaire** (optionnel) : Examens supplémentaires à réaliser
- **recommandations** (optionnel) : Conseils et recommandations pour le patient

---

## 🔄 Effet de la validation

1. **Statut** : Passe de `en_analyse` ou `analyse_terminee` à `valide_medecin`
2. **Date** : `date_validation` est automatiquement définie
3. **Médecin** : `medecin_validateur` est défini comme l'utilisateur actuel
4. **Données** : Les champs diagnostic/traitement/recommandations sont sauvegardés

---

## 📤 Réponse

```json
{
    "id": 15,
    "status": "valide_medecin",
    "status_display": "Validé par médecin",
    "diagnostic": "Gastrite aiguë",
    "traitement": "Oméprazole 20mg 2x/jour pendant 7 jours",
    "examen_complementaire": "Échographie abdominale si persistance",
    "recommandations": "Éviter épices, repos, hydratation",
    "medecin_validateur": {
        "id": 3,
        "username": "dr_martin",
        "first_name": "Jean",
        "last_name": "Martin"
    },
    "date_validation": "2025-09-16T16:30:00Z"
}
```

---

## 🧪 Exemples d'utilisation

### JavaScript
```javascript
const validateConsultation = async (ficheId, validationData) => {
    const response = await fetch(`/api/v1/fiche-consultation/${ficheId}/validate/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${medecin_token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(validationData)
    });
    
    if (!response.ok) {
        throw new Error('Erreur lors de la validation');
    }
    
    return await response.json();
};

// Utilisation
const result = await validateConsultation(15, {
    diagnostic: "Hypertension artérielle grade 1",
    traitement: "Amlodipine 5mg 1x/jour",
    recommandations: "Surveillance tension, réduction sel"
});
```

### Python
```python
import requests

headers = {"Authorization": f"Bearer {medecin_token}"}
data = {
    "diagnostic": "Bronchite aiguë",
    "traitement": "Amoxicilline 500mg 3x/jour pendant 7 jours",
    "recommandations": "Repos, hydratation, éviter tabac"
}

response = requests.post(
    f"https://api.example.com/api/v1/fiche-consultation/15/validate/",
    json=data,
    headers=headers
)

if response.status_code == 200:
    print("Consultation validée avec succès")
    print(response.json())
```

### cURL
```bash
curl -X POST https://api.example.com/api/v1/fiche-consultation/15/validate/ \
  -H "Authorization: Bearer $MEDECIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "diagnostic": "Migraine commune",
    "traitement": "Paracétamol 1g si douleur",
    "recommandations": "Éviter stress, sommeil régulier"
  }'
```

---

## ⚠️ Erreurs possibles

- **403 Forbidden** : Médecin non assigné ou pas de permissions
- **404 Not Found** : Fiche inexistante
- **400 Bad Request** : Champ diagnostic manquant
- **409 Conflict** : Fiche déjà validée

### Exemples d'erreurs JSON
```json
// Champ diagnostic manquant (400)
{
    "diagnostic": ["Ce champ est obligatoire."]
}

// Permission refusée (403)
{
    "detail": "Vous n'êtes pas assigné à cette fiche de consultation."
}

// Fiche déjà validée (409)
{
    "detail": "Cette fiche de consultation a déjà été validée."
}
```

---

## 📋 Prérequis

1. La fiche doit exister
2. L'utilisateur doit être médecin
3. Le médecin doit être assigné à cette fiche (ou être admin)
4. Le champ `diagnostic` est obligatoire
5. La fiche ne doit pas déjà être validée

---

## 🔍 Workflow type

1. **Médecin consulte la fiche** : `GET /api/v1/fiche-consultation/{id}/`
2. **Analyse les informations** : Examen clinique, anamnèse, antécédents
3. **Établit son diagnostic** : Diagnostic principal et éventuels diagnostics différentiels
4. **Valide avec traitement** : `POST /api/v1/fiche-consultation/{id}/validate/`
5. **Envoi au patient** : `POST /api/v1/fiche-consultation/{id}/send-whatsapp/`

---

## 🎯 Conseils d'usage

### Pour les développeurs frontend
```javascript
// Interface de validation médecin
const ValidationForm = ({ ficheId }) => {
    const [diagnostic, setDiagnostic] = useState('');
    const [traitement, setTraitement] = useState('');
    const [recommandations, setRecommandations] = useState('');
    
    const handleValidate = async () => {
        try {
            await validateConsultation(ficheId, {
                diagnostic,
                traitement,
                recommandations
            });
            
            alert('Consultation validée avec succès !');
            // Rediriger ou rafraîchir
        } catch (error) {
            alert('Erreur lors de la validation : ' + error.message);
        }
    };
    
    return (
        <form onSubmit={handleValidate}>
            <textarea 
                placeholder="Diagnostic (obligatoire)"
                value={diagnostic}
                onChange={(e) => setDiagnostic(e.target.value)}
                required
            />
            <textarea 
                placeholder="Traitement"
                value={traitement}
                onChange={(e) => setTraitement(e.target.value)}
            />
            <textarea 
                placeholder="Recommandations"
                value={recommandations}
                onChange={(e) => setRecommandations(e.target.value)}
            />
            <button type="submit">Valider la consultation</button>
        </form>
    );
};
```

### Validation côté client
```javascript
const validateForm = (data) => {
    const errors = {};
    
    if (!data.diagnostic?.trim()) {
        errors.diagnostic = 'Le diagnostic est obligatoire';
    }
    
    if (data.diagnostic?.length > 1000) {
        errors.diagnostic = 'Le diagnostic ne peut dépasser 1000 caractères';
    }
    
    return errors;
};
```

---

## 🔔 Notifications recommandées

Après validation, il est recommandé de :
1. **Notifier le patient** par email/SMS/WhatsApp
2. **Mettre à jour l'interface** médecin (liste des fiches en attente)
3. **Logger l'action** pour audit et traçabilité
4. **Déclencher l'envoi automatique** de la fiche au patient

---

Cet endpoint finalise le processus de consultation en permettant au médecin d'établir son diagnostic officiel et ses recommandations pour le patient.