# 💬 Endpoints Messages et Actions - Fiches de Consultation

## Vue d'ensemble

Cette documentation couvre les endpoints de messagerie et d'actions spécialisées pour les fiches de consultation : gestion des messages, relance IA, et envoi WhatsApp.

---

## 📬 Messagerie sur les Fiches

### 1. **Lister les messages d'une fiche**
```http
GET /api/v1/fiche-consultation/{id}/messages/
```

**Permissions** : Patient propriétaire, médecin assigné, ou Staff/Admin

**Réponse** :
```json
[
    {
        "id": 1,
        "author": {
            "id": 2,
            "username": "patient_jean",
            "first_name": "Jean",
            "last_name": "Dupont",
            "role": "patient"
        },
        "content": "Bonjour docteur, j'ai des questions sur mon traitement. Les douleurs persistent malgré la prise des médicaments prescrits.",
        "created_at": "2025-09-16T14:30:00Z",
        "fiche": 15
    },
    {
        "id": 2,
        "author": {
            "id": 3,
            "username": "dr_martin",
            "first_name": "Jean",
            "last_name": "Martin",
            "role": "medecin"
        },
        "content": "Bonjour Jean, pouvez-vous me préciser depuis combien de temps vous prenez le traitement et à quelle fréquence ?",
        "created_at": "2025-09-16T15:15:00Z",
        "fiche": 15
    }
]
```

**Filtrage** (paramètres optionnels) :
- `author` : Filtrer par ID de l'auteur
- `created_at__gte` : Messages après une date (ISO 8601)
- `created_at__lte` : Messages avant une date (ISO 8601)

**Exemple avec filtres** :
```
GET /api/v1/fiche-consultation/15/messages/?author=3&created_at__gte=2025-09-16T00:00:00Z
```

### 2. **Ajouter un message à une fiche**
```http
POST /api/v1/fiche-consultation/{id}/messages/
```

**Permissions** : Patient propriétaire, médecin assigné, ou Staff/Admin

**Payload** :
```json
{
    "content": "Merci pour votre réponse. Je prends le traitement depuis 3 jours, 2 fois par jour comme prescrit. Cependant, les douleurs abdominales sont toujours présentes, surtout le matin à jeun."
}
```

**Champs** :
- **content** (obligatoire, string) : Contenu du message (max 2000 caractères)

**Réponse** :
```json
{
    "id": 3,
    "author": {
        "id": 2,
        "username": "patient_jean",
        "first_name": "Jean",
        "last_name": "Dupont",
        "role": "patient"
    },
    "content": "Merci pour votre réponse. Je prends le traitement depuis 3 jours...",
    "created_at": "2025-09-16T16:45:00Z",
    "fiche": 15
}
```

**Effet automatique** :
- L'auteur est automatiquement défini comme l'utilisateur authentifié
- La date de création est automatiquement définie
- La fiche est liée automatiquement

---

## 🔄 Relancer l'Analyse IA

### **Relancer l'analyse IA d'une fiche**
```http
POST /api/v1/fiche-consultation/{id}/relancer/
```

**Permissions** : Médecin ou Staff/Admin

**Payload** (optionnel) :
```json
{
    "force_reanalysis": true,
    "include_messages": true,
    "analysis_type": "complete"
}
```

**Champs optionnels** :
- **force_reanalysis** (boolean, défaut: true) : Force une nouvelle analyse même si une analyse récente existe
- **include_messages** (boolean, défaut: true) : Inclut les messages dans l'analyse IA
- **analysis_type** (string, défaut: "complete") : Type d'analyse ("complete", "diagnostic_only", "recommendation_only")

**Réponse** :
```json
{
    "message": "Analyse IA relancée avec succès",
    "task_id": "celery-task-uuid-123456",
    "status": "pending",
    "estimated_completion": "2025-09-16T17:05:00Z",
    "fiche_id": 15,
    "analysis_type": "complete",
    "include_messages": true
}
```

**Effet** :
1. Déclenche une tâche Celery asynchrone
2. Le statut de la fiche reste inchangé pendant l'analyse
3. Une fois terminée, le champ `diagnostic_ia` est mis à jour
4. Le statut peut passer à `analyse_terminee` si approprié

**Cas d'usage** :
- Nouvelles informations ajoutées dans les messages
- Correction d'erreurs dans la fiche
- Mise à jour des algorithmes IA
- Diagnostic IA insuffisant ou erroné

---

## 📱 Envoi WhatsApp

### **Envoyer la fiche via WhatsApp**
```http
POST /api/v1/fiche-consultation/{id}/send-whatsapp/
```

**Permissions** : Médecin assigné ou Staff/Admin

**Payload** :
```json
{
    "template_type": "consultation_validee",
    "recipient_phone": "+243123456789",
    "custom_message": "Votre consultation a été validée. Voici vos résultats et recommandations.",
    "include_attachments": true,
    "language": "fr",
    "send_immediately": true
}
```

**Champs** :
- **template_type** (string, défaut: "consultation_validee") : Type de template
  - `"consultation_validee"` : Fiche validée avec diagnostic
  - `"consultation_rejetee"` : Fiche rejetée avec motif
  - `"demande_informations"` : Demande d'informations supplémentaires
  - `"custom"` : Message personnalisé
- **recipient_phone** (string, optionnel) : Numéro de téléphone du destinataire (sinon utilise celui de la fiche)
- **custom_message** (string, optionnel) : Message personnalisé (max 1000 caractères)
- **include_attachments** (boolean, défaut: true) : Inclure les documents PDF/images
- **language** (string, défaut: "fr") : Langue du template ("fr", "en", "sw")
- **send_immediately** (boolean, défaut: true) : Envoyer immédiatement ou programmer

**Réponse** :
```json
{
    "message": "Message WhatsApp envoyé avec succès",
    "whatsapp_message_id": "wamid.gBGGSFcCgTW1dHTrFvr_2Xf-zr0=",
    "recipient": "+243123456789",
    "template_used": "consultation_validee",
    "sent_at": "2025-09-16T17:00:00Z",
    "status": "sent",
    "delivery_status": "delivered",
    "fiche_id": 15
}
```

**Templates disponibles** :

#### Template "consultation_validee"
```
🏥 *Consultation Médicale - Résultats*

Bonjour {patient_name},

Votre consultation du {date} a été validée par Dr {medecin_name}.

📋 *Diagnostic:* {diagnostic}
💊 *Traitement:* {traitement}
📝 *Recommandations:* {recommandations}

Pour toute question, contactez notre service au {contact_phone}.

Bonne santé ! 🌟
```

#### Template "consultation_rejetee"
```
🏥 *Consultation Médicale - Information*

Bonjour {patient_name},

Votre consultation nécessite des informations complémentaires.

❗ *Motif:* {motif_rejet}

Merci de compléter votre dossier ou de nous contacter au {contact_phone}.

Cordialement,
L'équipe médicale
```

**Variables disponibles dans les templates** :
- `{patient_name}` : Nom complet du patient
- `{date}` : Date de consultation
- `{medecin_name}` : Nom du médecin
- `{diagnostic}` : Diagnostic établi
- `{traitement}` : Traitement prescrit
- `{recommandations}` : Recommandations
- `{motif_rejet}` : Motif de rejet (template rejet)
- `{contact_phone}` : Numéro de contact de la clinique

---

## 🧪 Exemples d'utilisation

### Messages - JavaScript
```javascript
// Lister les messages
const getMessages = async (ficheId) => {
    const response = await fetch(`/api/v1/fiche-consultation/${ficheId}/messages/`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
};

// Ajouter un message
const addMessage = async (ficheId, content) => {
    const response = await fetch(`/api/v1/fiche-consultation/${ficheId}/messages/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
    });
    return await response.json();
};

// Interface de chat
const ChatInterface = ({ ficheId }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    
    const sendMessage = async () => {
        if (!newMessage.trim()) return;
        
        const message = await addMessage(ficheId, newMessage);
        setMessages([...messages, message]);
        setNewMessage('');
    };
    
    return (
        <div className="chat-interface">
            <div className="messages">
                {messages.map(msg => (
                    <div key={msg.id} className={`message ${msg.author.role}`}>
                        <strong>{msg.author.first_name}:</strong>
                        <p>{msg.content}</p>
                        <small>{new Date(msg.created_at).toLocaleString()}</small>
                    </div>
                ))}
            </div>
            <div className="message-input">
                <textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Tapez votre message..."
                    maxLength={2000}
                />
                <button onClick={sendMessage}>Envoyer</button>
            </div>
        </div>
    );
};
```

### Relance IA - Python
```python
import requests
import time

def relancer_analyse_ia(fiche_id, token, options=None):
    """Relance l'analyse IA et attend le résultat"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Payload par défaut
    payload = {
        "force_reanalysis": True,
        "include_messages": True,
        "analysis_type": "complete"
    }
    
    if options:
        payload.update(options)
    
    # Lancer l'analyse
    response = requests.post(
        f"https://api.example.com/api/v1/fiche-consultation/{fiche_id}/relancer/",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        task_id = result.get('task_id')
        
        # Polling du statut (optionnel)
        while True:
            fiche_response = requests.get(
                f"https://api.example.com/api/v1/fiche-consultation/{fiche_id}/",
                headers=headers
            )
            fiche = fiche_response.json()
            
            if fiche.get('status') == 'analyse_terminee':
                print("Analyse IA terminée !")
                return fiche.get('diagnostic_ia')
            
            time.sleep(5)  # Attendre 5 secondes
    
    return None

# Utilisation
diagnostic_ia = relancer_analyse_ia(15, medecin_token, {
    "analysis_type": "diagnostic_only",
    "include_messages": True
})
```

### WhatsApp - cURL
```bash
# Envoi automatique avec template par défaut
curl -X POST https://api.example.com/api/v1/fiche-consultation/15/send-whatsapp/ \
  -H "Authorization: Bearer $MEDECIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Envoi personnalisé
curl -X POST https://api.example.com/api/v1/fiche-consultation/15/send-whatsapp/ \
  -H "Authorization: Bearer $MEDECIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_type": "custom",
    "custom_message": "Bonjour, votre consultation est prête. Consultez les résultats en pièce jointe.",
    "include_attachments": true,
    "language": "fr"
  }'
```

---

## ⚠️ Gestion des Erreurs

### Messages
```json
// Contenu trop long (400)
{
    "content": ["Le message ne peut dépasser 2000 caractères."]
}

// Accès refusé (403)
{
    "detail": "Vous n'avez pas accès aux messages de cette fiche."
}
```

### Relance IA
```json
// Analyse déjà en cours (409)
{
    "detail": "Une analyse IA est déjà en cours pour cette fiche."
}

// Fiche non éligible (400)
{
    "detail": "Cette fiche ne peut pas être analysée par l'IA."
}
```

### WhatsApp
```json
// Numéro invalide (400)
{
    "recipient_phone": ["Numéro de téléphone invalide."]
}

// Service indisponible (503)
{
    "detail": "Service WhatsApp temporairement indisponible."
}
```

---

## 🔔 Notifications et Webhooks

### Événements déclenchés
1. **Nouveau message** → Notification en temps réel
2. **Analyse IA terminée** → Mise à jour du statut
3. **WhatsApp envoyé** → Confirmation de livraison
4. **WhatsApp lu** → Accusé de réception

### Configuration recommandée
```javascript
// WebSocket pour messages en temps réel
const socket = new WebSocket('wss://api.example.com/ws/fiche/15/messages/');

socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    // Ajouter le nouveau message à l'interface
    updateChatInterface(message);
};
```

---

Ces endpoints permettent une communication fluide entre patients et médecins, une réanalyse intelligente par IA, et une notification automatique des résultats via WhatsApp.