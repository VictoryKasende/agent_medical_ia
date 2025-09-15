# MEDIAI - Système Intelligent de Consultation Médicale Assistée par IA

MEDIAI est une plateforme de gestion des consultations médicales intégrant l’IA générative (LLMs : GPT, Gemini, Claude) pour assister le personnel soignant dans la collecte, l’analyse, la synthèse et la validation des données. La plateforme facilite aussi la communication avec les patients (WhatsApp) et expose une API REST documentée.

## 1) Présentation rapide

- Automatiser et assister le processus de consultation à l’aide de LLMs
- Améliorer la qualité et la rapidité des diagnostics
- Communication patient ↔ personnel médical
- Consultations sur place et à distance

## 2) Architecture

- Django project: `agent_medical_ia/`
- Apps:
  - `authentication/` — Authentification, inscription, rôles, API JWT et annuaire médecins
  - `chat/` — Fiches de consultation, IA, conversations, rendez-vous, messagerie
- Routage principal:
  - `''` → `chat.urls` (HTML)
  - `admin/` → Django Admin
  - `auth/` → `authentication.urls` (HTML)
  - API v1: `api/v1/` (chat) et `api/v1/auth/` (auth)

## 3) API v1 — Endpoints clés

Tous les endpoints sont paginés (PageNumberPagination) si applicable. Authentification: JWT Bearer.

### 3.1 Auth & Utilisateurs (`/api/v1/auth/`)

- POST `token/` — Obtenir un access/refresh token
- POST `refresh/` — Rafraîchir le token
- POST `verify/` — Vérifier un token
- POST `logout/` — Invalider le refresh (si blacklist activée)
- GET `me/` — Profil courant (héritage)
- POST `users/register/` — Inscription publique (optionnel)
- ViewSet `users/` — CRUD (list/destroy admin seulement, retrieve/update par le propriétaire)
- ViewSet `users/me/` — GET/PATCH du profil courant

Annuaire médecins (accès patient uniquement):
- GET `medecins/` — Lister les médecins
  - Filtres: `?available=true|false`, `?specialty=<texte>`
- GET `medecins/available/` — Lister uniquement les médecins disponibles

Convenience non-versionné (optionnel) :
- POST `/api/auth/jwt/token/`, POST `/api/auth/jwt/refresh/`

### 3.2 Consultations (`/api/v1/fiche-consultation/`)

- CRUD des fiches de consultation
- Filtres:
  - `?status=a,b` — un ou plusieurs statuts
  - `?is_patient_distance=true` — vue « distance » (serializer léger)
  - `?assigned_only=true` — pour un médecin, ne voir que ses fiches
- Actions sur une fiche:
  - POST `{id}/validate/` — valider la fiche (médecin/staff)
  - POST `{id}/reject/` — rejeter (payload `{ "commentaire": "..." }`)
  - POST `{id}/relancer/` — relancer l’analyse IA
  - POST `{id}/send-whatsapp/` — envoi d’un template (placeholder)
  - POST `{id}/assign-medecin/` — assigner un médecin (médecin/staff)
  - GET/POST `{id}/messages/` — fil de messages médecin/patient lié à la fiche

Consultations à distance — alias déprécié (lecture seule) :
- GET `/api/v1/consultations-distance/` → utiliser `GET /api/v1/fiche-consultation/?is_patient_distance=true`

### 3.3 Rendez-vous (`/api/v1/appointments/`)

- CRUD des rendez-vous (patient crée; médecins/staff voient tout)
- Actions:
  - POST `{id}/assign/` — assigner un médecin (médecin/staff)
  - POST `{id}/confirm/` — confirmer un créneau (médecin)
  - POST `{id}/decline/` — refuser (médecin)
  - POST `{id}/cancel/` — annuler (patient/medecin/staff)

### 3.4 Conversations & Messages (`/api/v1/conversations/`, `/api/v1/messages/`)

- Conversations: CRUD + `{id}/messages/` (GET/POST)
- Messages IA: lecture seule (`/messages/`)

### 3.5 IA asynchrone (`/api/ia/`)

- POST `analyse/` — démarrer une analyse (202 + cache_key)
- GET `status/{task_id}/` — statut de tâche
- GET `result/` — récupérer un résultat via `cache_key`

### 3.6 Documentation OpenAPI

- Schéma: `GET /api/schema/` (JSON)
- Swagger UI: `GET /api/docs/`
- Redoc: `GET /api/redoc/`

## 4) Fonctionnalités principales

- Fiches de consultation avec pipeline IA (asynchrone via Celery)
- Validation médicale et messagerie liée à la fiche
- Annuaire médecins avec disponibilité (`medecin_profile.is_available`) et spécialité
- Rendez-vous patient ↔ médecin (assignation, confirmation, annulation)

## 5) Démarrage rapide

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Variables d’environnement (ex. WhatsApp/Twilio) si activées :

```bash
# Linux/macOS
export TWILIO_ACCOUNT_SID=...
export TWILIO_AUTH_TOKEN=...
export TWILIO_WHATSAPP_NUMBER=whatsapp:+1xxxxxxxxxx
# PowerShell
$env:TWILIO_ACCOUNT_SID="..."
$env:TWILIO_AUTH_TOKEN="..."
$env:TWILIO_WHATSAPP_NUMBER="whatsapp:+1xxxxxxxxxx"
```

## 6) Notes et statuts

- Statuts (`chat/constants.py`): `en_analyse`, `analyse_terminee`, `valide_medecin`, `rejete_medecin`
- Pagination: paramètres `page`, `page_size`
- L’alias `/api/v1/consultations-distance/` est déprécié et sera retiré ultérieurement



