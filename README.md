<<<<<<< HEAD
# MEDIAI - Système Intelligent de Consultation Médicale Assistée par IA

MEDIAI est une plateforme de gestion des consultations médicales intégrant l’intelligence artificielle générative (LLMs tels que GPT, Gemini, Claude) pour assister le personnel soignant dans la collecte, l’analyse, la synthèse et la validation des données médicales. Le système facilite aussi la communication avec les patients via WhatsApp.

## 1) Présentation générale

- **Objectifs**
  - Automatiser et assister le processus de consultation médicale à l’aide de LLMs
  - Améliorer la qualité et la rapidité des diagnostics
  - Faciliter la communication patient ↔ personnel médical
  - Offrir une solution accessible à distance pour les consultations.

## 2) Architecture & Organisation du projet

- Django project: `agent_medical_ia/`
- Applications:
  - `authentication/` — Authentification, inscription, rôles, redirections
  - `chat/` — Fiches de consultation, intégration LLM, conversations, dashboards, WhatsApp
- Routage principal:
  - `''` → `chat.urls`
  - `admin/` → Django Admin
  - `auth/` → `authentication.urls`

## 3) Fonctionnalités

### 3.1 Authentification & Rôles

- Connexion/Déconnexion/Inscription: `auth/login/`, `auth/logout/`, `auth/register/`
- Rôles et accès: patient, médecin (groupe `medecin`), superuser (admin)
- Redirections par rôle après login

### 3.2 Gestion des utilisateurs

- Création de comptes patients (self-service)
- Création/gestion du personnel via `admin/`
- Redirections post-inscription selon rôle

### 3.3 Fiche de consultation

- Création d’une fiche: `consultation/`
- Présentiel: liste/édition/détail/impression
  - `consultation/patient/`
  - `consultation/patient/<id>/modifier/`
  - `consultation/patient/<id>/modifier/statut`
  - `consultation/patient/<id>/details/`
  - `consultation/<pk>/print/`
- Distant: liste/édition
  - `consultation/patient-distant/`
  - `consultation/patient-distant/<id>/modifier/`
- Signature médecin (base64) lors de la validation

### 3.4 Intégration LLM & IA

- Transformation de la fiche → texte structuré riche
- Déclenchement d’analyse IA (Celery) à la création/relance
- Polling des résultats: `diagnostic-result/`
- Relance analyse: `relancer-analyse/<fiche_id>/`

### 3.5 Conversations & Historique

- CRUD minimal de conversation:
  - Créer: `conversation/` (POST)
  - Lire/Supprimer/Renommer: `conversation/<id>/` (GET/DELETE/PUT)
- Historique UI partiel (AJAX): `chat-history-partial/`

### 3.6 Diagnostic & Validation médicale

- Lecture des synthèses IA
- Édition médecin: diagnostic, traitement, examens, recommandations
- Validation (statut → `analyse_terminee`)
- Impression de la conclusion (`consultation/<pk>/print/`)

### 3.7 Communication Patient (WhatsApp)

- Envoi de template WhatsApp à la validation et à la demande:
  - Envoi auto après mise à jour fiche
  - Manuel: `send-whatsapp/<consultation_id>/` (POST)
- Templates avec variables (identité, date, diagnostic, traitement, recommandations, validateur)

### 3.8 Dashboards

  - Présentiel: `consultation/patient/`
  - Distant: `consultation/patient-distant/` (listing HTML conservé pour usage interne). L'ancien couple `consultations-distance/` + `api/consultations-distance/` a été supprimé (fusion via API DRF).


### Nettoyage final API (Étape 8)

Les routes HTML et alias legacy liés à `consultations-distance` ont été retirés.
La source unique pour les consultations à distance côté API est:
`GET /api/v1/fiche-consultation/?is_patient_distance=true`

Actions disponibles sur une fiche (récap):
- `POST /api/v1/fiche-consultation/{id}/validate/`
- `POST /api/v1/fiche-consultation/{id}/reject/` (payload: `{ "commentaire": "..." }`)
- `POST /api/v1/fiche-consultation/{id}/relancer/`
- `POST /api/v1/fiche-consultation/{id}/send-whatsapp/`

Statuts (`chat/constants.py`): `en_analyse`, `analyse_terminee`, `valide_medecin`, `rejete_medecin`.

Pagination: standard DRF (PageNumberPagination), paramètres `page` & `page_size`.
### 3.9 Asynchrone, Cache & Utilitaires

- Tâches Celery: `analyse_symptomes_task` (+ relance)
- Cache résultat IA (clé md5 → `diagnostic_<hash>`)
- Suivi des tâches: `check-task-status/<task_id>/`
- `transaction.on_commit` pour lancer l’analyse après persistance

### 3.10 Sécurité & Contrôles d’accès

- `LoginRequiredMixin`, `user_passes_test(is_medecin|is_patient)`
- Filtrage des vues sensibles par rôle/groupe

## 4) Scénarios d’utilisation

### Cas 1 : Consultation sur place

1. Saisie de la fiche par le soignant
2. Envoi vers LLM (tâche asynchrone), réception + synthèse IA
3. Analyse/édition/validation par le médecin
4. Impression de la conclusion
5. Envoi du message au patient via WhatsApp

### Cas 2 : Consultation à distance

1. Saisie de la fiche par le patient en ligne
2. Pipeline identique (LLM → synthèse → validation)
3. Retour au patient via la plateforme et/ou WhatsApp

## 5) Endpoints principaux (rappel)

- Racine analyse (médecin): `''`
- Auth: `auth/login/`, `auth/logout/`, `auth/register/`
- Fiches: `consultation/`, `consultation/patient/`, `consultation/patient-distant/`, `consultation/<pk>/print/`
- Conversations: `conversation/`, `conversation/<id>/`
- Dashboards: `dashboard/`, `dashboard/patient/`, `dashboard/medecin/`, `dashboard/proche/`
- IA/Async: `diagnostic-result/`, `check-task-status/<task_id>/`, `relancer-analyse/<fiche_id>/`
- Distant: `consultations-distance/`, `api/consultations-distance/`
- WhatsApp: `send-whatsapp/<consultation_id>/`

## 6) Roadmap — 25% restants

### Rôles & ACL
- Ajouter le rôle « Personnel soignant » distinct (groupes/permissions) et écrans associés
- Paramétrer des ACL fines sur vues et actions (édition, validation, impression)

### Multi-LLM & Config
- Activer la sélection dynamique du fournisseur LLM (GPT, Gemini, Claude) par contexte
- Exposer la configuration dans `llm_config.py` et via variables d’environnement
- Journaliser les appels et latences pour observabilité

### Pièces jointes & Résultats complémentaires
- Support d’upload (PDF, images, comptes rendus) rattachés à une fiche
- Affichage et persistance dans l’historique du dossier

### WhatsApp bidirectionnel & Consentement
- Webhooks inbound (réponses patient) et rattachement au dossier/conversation
- Paramètres de consentement patient + mentions légales
- Journalisation/audit des messages

### Portail patient & UX
- Espace patient pour consulter l’historique, téléchargements, messages
- Améliorer les vues distancielles (fils d’événements, statuts en temps réel)

### Sécurité & Conformité
- Politique de rétention des données, RGPD/HIPAA selon contexte
- Traçabilité (audit log) des actions clés (création, modification, validation, envoi)

## 7) Démarrage rapide (extrait)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Pour l’envoi WhatsApp (Twilio), définir dans l’environnement:

```bash
export TWILIO_ACCOUNT_SID=...
export TWILIO_AUTH_TOKEN=...
export TWILIO_WHATSAPP_NUMBER=whatsapp:+1xxxxxxxxxx
```

## 8) État d’avancement

- Estimation: ~75% livré
- Cible: finalisation des items de la Roadmap sur la semaine du 19 juin 2025


## 9) Transformation en API REST (plan documenté)

Cette section décrit comment migrer progressivement MEDIAI vers une API REST standardisée, sans inclure de code, avec des étapes claires et actionnables.

### Étape 0 — Pré-requis et dépendances

- Ajouter les dépendances: Django REST Framework, SimpleJWT, drf-spectacular
- Activer DRF, JWT et la génération du schéma OpenAPI dans `settings.py`
- Définir la pagination, les permissions par défaut et la classe de schéma
- Exposer la documentation: routes pour le schéma OpenAPI et l’UI (Swagger)

### Étape 1 — Cadrage et design des endpoints (v1)

- Définir le périmètre v1 et la version de l’API sous `/api/v1/`
- Lister les ressources et opérations requises:
  - Authentification: obtenir/rafraîchir tokens JWT
  - Utilisateurs: inscription et profil « moi »
  - Conversations: créer, lire, renommer, supprimer; lecture des messages
  - Fiches de consultation: CRUD nécessaire, validation, changement de statut
  - IA: déclenchement d’analyse asynchrone et récupération des résultats (polling)
  - Consultations à distance: listing API
  - WhatsApp: envoi de templates; (optionnel) webhook entrant
- Définir les contrats (payloads, codes d’erreur, pagination, filtres)

### Étape 2 — Sérialisation des modèles

- Créer des serializers pour `Conversation`, `MessageIA`, `FicheConsultation`, `CustomUser`
- Définir les champs en lecture seule (ex: dates, validateurs, ids générés)
- Normaliser les formats de dates/horodatages
- Documenter les validations et invariants (ex: transitions de statut autorisées)

### Étape 3 — Permissions et politiques d’accès

- Concevoir des permissions par rôle: `patient`, `medecin`, `admin`
- Restreindre l’accès aux ressources (ex: un patient ne voit que ses fiches)
- Exiger `medecin` pour actions sensibles (validation, envoi WhatsApp)
- Ajouter throttling (anti-abus) pour endpoints critiques

### Étape 4 — ViewSets / APIViews

- Implémenter les endpoints via ViewSets (CRUD) et actions personnalisées
- Ajouter actions spécifiques: ex `validate` pour une fiche, `messages` pour une conversation
- Gérer les réponses standardisées (201/202/400/403/404) et messages d’erreur clairs

### Étape 5 — Routage et versionnement

- Créer des routers dédiés à l’API et les inclure sous `/api/v1/`
- Séparer les URLs HTML existantes des URLs API
- Prévoir la compatibilité ascendante pour `/api/v2` futur

### Étape 6 — IA asynchrone et cache

- Exposer l’endpoint pour déclencher l’analyse (retour 202 + `cache_key`)
- Exposer l’endpoint pour récupérer le résultat via `cache_key`
- Garantir l’exécution asynchrone après transaction (`on_commit`)

### Étape 7 — Authentification & Sécurité

- Basculer l’authentification API sur JWT (access/refresh)
- Isoler et auditer les actions sensibles (validation, envoi messages)
- Activer CORS si front séparé et configurer les origines autorisées

### Étape 8 — Documentation & Contrats

- Publier le schéma OpenAPI et l’UI de doc
- Décrire les exemples de requêtes/réponses et les erreurs attendues
- Documenter l’authentification (Authorization: Bearer <token>)

### Étape 9 — Migration progressive (cohabitation)

- Phase 1: conserver les vues HTML, introduire l’API REST en parallèle
- Phase 2: faire consommer l’API par le front; déprécier les routes HTML obsolètes
- Phase 3: retirer le code legacy UI une fois l’usage de l’API stabilisé

### Étape 10 — Tests, CI et livraison

- Couvrir les endpoints avec des tests d’API (cas succès/erreur/permissions)
- Valider le schéma OpenAPI en CI et publier la doc sur chaque build
- Vérifier les quotas/throttling et les parcours asynchrones (file d’attente)
- Checklist de sortie:
  - JWT opérationnel (login/refresh) et expirations
  - Routers v1 exposés et documentés
  - Sérializers et permissions validés pour `patient`/`medecin`
  - Endpoints IA (analyse/result) stables
  - Webhook WhatsApp (si activé) sécurisé et journalisé
  - Documentation publique `/api/docs/`
  - Plan de rollback et monitoring en production


=======
# 🏥 Agent Médical IA - Plateforme de Télémédecine

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-Latest-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)

**Agent Médical IA** est une plateforme de télémédecine moderne intégrant l'intelligence artificielle pour assister les professionnels de santé dans leurs consultations à distance. La plateforme offre un workflow complet de consultation, de l'analyse IA jusqu'à la validation médicale.

## 📋 Table des Matières

- [🚀 Fonctionnalités](#-fonctionnalités)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Technologies](#️-technologies)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🚀 Démarrage](#-démarrage)
- [📊 Modèles de Données](#-modèles-de-données)
- [🔀 Workflow](#-workflow)
- [🤖 Intégration IA](#-intégration-ia)
- [🐳 Docker](#-docker)
- [🔒 Sécurité](#-sécurité)
- [📱 Interface Utilisateur](#-interface-utilisateur)
- [🧪 Tests](#-tests)
- [📈 Monitoring](#-monitoring)
- [🤝 Contribution](#-contribution)
- [📄 Licence](#-licence)

## 🚀 Fonctionnalités

### 🏥 **Consultation Médicale Complète**
- ✅ **Fiche de consultation digitale** avec plus de 100+ champs médicaux
- ✅ **Anamnèse détaillée** (motifs, histoire de la maladie, antécédents)
- ✅ **Signes vitaux** (température, SpO2, tension artérielle, pouls, etc.)
- ✅ **Examen clinique par régions anatomiques**
- ✅ **Antécédents personnels et familiaux**
- ✅ **Perceptions et attentes du patient**

### 🤖 **Intelligence Artificielle Multi-Modèles**
- ✅ **GPT-4** (OpenAI) - Analyse approfondie
- ✅ **Claude 3** (Anthropic) - Raisonnement médical
- ✅ **Gemini Pro** (Google) - Synthèse diagnostique
- ✅ **Diagnostic IA automatique** basé sur les symptômes
- ✅ **Recommandations thérapeutiques** personnalisées

### 👥 **Gestion Multi-Utilisateurs**
- ✅ **Patients** - Création de compte et téléconsultation
- ✅ **Médecins** - Validation des diagnostics IA
- ✅ **Authentification sécurisée** avec rôles différenciés
- ✅ **Profils personnalisés** selon le type d'utilisateur

### 📋 **Workflow Médical**
- ✅ **États de consultation** : 
  - `en_analyse` → `analyse_terminee` → `valide_medecin` / `rejete_medecin`
- ✅ **Signature électronique** des médecins
- ✅ **Historique complet** des consultations
- ✅ **Numérotation automatique** des dossiers

### 💬 **Système de Chat IA**
- ✅ **Conversations temps réel** avec les IA médicales
- ✅ **Historique des échanges** par consultation
- ✅ **Messages structurés** par rôle (utilisateur, IA, synthèse)

## 🏗️ Architecture

```
agent_medical_ia/
├── 🏥 agent_medical_ia/          # Configuration Django principale
│   ├── settings.py               # Paramètres (DB, Redis, Celery)
│   ├── urls.py                   # Routage principal
│   ├── celery.py                 # Configuration Celery
│   └── wsgi.py                   # WSGI pour production
├── 🔐 authentication/            # Gestion des utilisateurs
│   ├── models.py                 # CustomUser
│   ├── views.py                  # Login/Register
│   ├── forms.py                  # Formulaires d'auth
│   └── urls.py                   # Routes auth
├── 💬 chat/                      # Module principal consultation
│   ├── models.py                 # FicheConsultation, Conversation, MessageIA
│   ├── views.py                  # Logique de consultation
│   ├── forms.py                  # Formulaires médicaux
│   ├── tasks.py                  # Tâches Celery (IA)
│   ├── llm_config.py             # Configuration des IA
│   ├── templates/chat/           # Templates HTML
│   │   ├── register.html         # Inscription patient
│   │   ├── login.html            # Connexion
│   │   └── consultation.html     # Interface consultation
│   └── static/chat/              # CSS, JS, Images
├── 🐳 Docker/                    # Conteneurisation
│   ├── Dockerfile                # Image Django
│   ├── docker-compose.yml        # Orchestration
│   └── entrypoint.sh             # Script de démarrage
├── 📊 staticfiles/               # Fichiers statiques collectés
├── 📋 requirements.txt           # Dépendances Python
└── 🚀 manage.py                  # CLI Django
```

## 🛠️ Technologies

### **Backend**
- **Django 5.2** - Framework web Python
- **PostgreSQL 15** - Base de données relationnelle
- **Redis** - Cache et broker de messages
- **Celery** - Traitement asynchrone
- **Gunicorn** - Serveur WSGI pour production

### **Intelligence Artificielle**
- **LangChain** - Framework pour applications IA
- **OpenAI GPT-4** - Modèle de langage avancé
- **Anthropic Claude 3** - IA conversationnelle
- **Google Gemini Pro** - Modèle multimodal

### **Frontend**
- **HTML5/CSS3** - Structure et style
- **Tailwind CSS** - Framework CSS utilitaire
- **JavaScript (Vanilla)** - Interactivité côté client
- **Font Awesome** - Icônes

### **Infrastructure**
- **Docker & Docker Compose** - Conteneurisation
- **Python 3.11** - Langage principal
- **Git** - Contrôle de version

### **Outils Supplémentaires**
- **Pillow** - Traitement d'images (signatures)
- **python-dotenv** - Gestion des variables d'environnement
- **psycopg2** - Connecteur PostgreSQL
- **django-redis** - Cache Redis pour Django

## 📦 Installation

### **Prérequis**
- Python 3.11+
- PostgreSQL 15+
- Redis
- Git
- Docker (optionnel)

### **1. Cloner le Projet**
```bash
git clone https://github.com/VictoryKasende/agent_medical_ia.git
cd agent_medical_ia
```

### **2. Environnement Virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### **3. Installer les Dépendances**
```bash
pip install -r requirements.txt
```

### **4. Base de Données**
```bash
# Créer la base PostgreSQL
createdb agent_medical_ia

# Migrations Django
python manage.py makemigrations
python manage.py migrate
```

### **5. Superutilisateur**
```bash
python manage.py createsuperuser
```

### **6. Fichiers Statiques**
```bash
python manage.py collectstatic
```

## ⚙️ Configuration

### **Variables d'Environnement**
Créez un fichier `.env` à la racine :

```env
# Django
DJANGO_SECRET_KEY=votre-clé-secrète-très-longue-et-complexe
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Base de données
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_medical_ia
DEVELOPMENT_MODE=True

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1

# IA APIs (optionnel)
OPENAI_API_KEY=sk-votre-clé-openai
ANTHROPIC_API_KEY=sk-ant-votre-clé-claude
GOOGLE_API_KEY=votre-clé-gemini
```

### **Configuration Django**
Le fichier `settings.py` est configuré pour :
- ✅ **Multi-environnements** (dev/prod)
- ✅ **PostgreSQL** avec fallback SQLite
- ✅ **Cache Redis**
- ✅ **Celery** pour tâches asynchrones
- ✅ **Gestion des médias** (signatures)
- ✅ **Sécurité CSRF**

## 🚀 Démarrage

### **Développement Local**

**1. Démarrer Redis**
```bash
redis-server
```

**2. Démarrer Celery (terminal séparé)**
```bash
celery -A agent_medical_ia worker --loglevel=info
```

**3. Démarrer Django**
```bash
python manage.py runserver
```

**4. Accéder à l'Application**
- 🌐 **Frontend** : http://127.0.0.1:8000
- 🔧 **Admin Django** : http://127.0.0.1:8000/admin
- 📝 **Inscription** : http://127.0.0.1:8000/auth/register
- 🔑 **Connexion** : http://127.0.0.1:8000/auth/login

## 📊 Modèles de Données

### **🏥 FicheConsultation**
Modèle principal contenant toutes les informations médicales :

```python
class FicheConsultation(models.Model):
    # Identité patient
    nom = CharField(max_length=100)
    prenom = CharField(max_length=100)
    date_naissance = DateField()
    sexe = CharField(choices=[('M', 'Masculin'), ('F', 'Féminin')])
    
    # Signes vitaux
    temperature = FloatField()
    tension_arterielle = CharField()
    pouls = IntegerField()
    
    # Workflow
    status = CharField(choices=[
        ('en_analyse', 'En cours d\'analyse'),
        ('analyse_terminee', 'Analyse terminée'),
        ('valide_medecin', 'Validé par médecin'),
        ('rejete_medecin', 'Rejeté par médecin')
    ])
    
    # Résultats
    diagnostic_ia = TextField()
    diagnostic = TextField()  # Validation médecin
    signature_medecin = ImageField()
```

### **💬 Conversation**
Gestion des échanges avec l'IA :

```python
class Conversation(models.Model):
    user = ForeignKey(CustomUser)
    fiche = ForeignKey(FicheConsultation)
    created_at = DateTimeField(auto_now_add=True)
```

### **🤖 MessageIA**
Messages individuels dans les conversations :

```python
class MessageIA(models.Model):
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('gpt4', 'GPT-4'),
        ('claude', 'Claude 3'),
        ('gemini', 'Gemini Pro'),
        ('synthese', 'Synthèse Finale')
    ]
    
    conversation = ForeignKey(Conversation)
    role = CharField(choices=ROLE_CHOICES)
    content = TextField()
    timestamp = DateTimeField(auto_now_add=True)
```

## 🔀 Workflow

### **Processus de Consultation**

```mermaid
graph TD
    A[Patient s'inscrit] --> B[Création compte]
    B --> C[Connexion]
    C --> D[Remplissage fiche médicale]
    D --> E[Soumission consultation]
    E --> F[Analyse IA Multi-Modèles]
    F --> G[Diagnostic IA généré]
    G --> H[Attente validation médecin]
    H --> I{Médecin valide?}
    I -->|Oui| J[Consultation validée]
    I -->|Non| K[Retour patient + corrections]
    J --> L[Signature électronique]
    L --> M[Dossier finalisé]
```

### **États de la Consultation**

1. **`en_analyse`** - IA traite les données
2. **`analyse_terminee`** - Diagnostic IA prêt
3. **`valide_medecin`** - Médecin approuve
4. **`rejete_medecin`** - Médecin rejette

## 🤖 Intégration IA

### **Configuration Multi-Modèles**
```python
# llm_config.py
LLM_MODELS = {
    'gpt4': {
        'provider': 'openai',
        'model': 'gpt-4',
        'speciality': 'analyse_generale'
    },
    'claude': {
        'provider': 'anthropic', 
        'model': 'claude-3-sonnet',
        'speciality': 'raisonnement_medical'
    },
    'gemini': {
        'provider': 'google',
        'model': 'gemini-pro',
        'speciality': 'synthese_diagnostique'
    }
}
```

### **Tâches Asynchrones**
```python
# tasks.py
@shared_task
def analyze_consultation_with_ai(fiche_id):
    """Analyse une consultation avec tous les modèles IA"""
    fiche = FicheConsultation.objects.get(id=fiche_id)
    
    # Analyse avec GPT-4
    gpt4_result = call_gpt4_api(fiche.to_dict())
    
    # Analyse avec Claude
    claude_result = call_claude_api(fiche.to_dict())
    
    # Synthèse avec Gemini
    gemini_synthesis = call_gemini_api({
        'gpt4': gpt4_result,
        'claude': claude_result,
        'patient_data': fiche.to_dict()
    })
    
    # Sauvegarde du diagnostic IA
    fiche.diagnostic_ia = gemini_synthesis
    fiche.status = 'analyse_terminee'
    fiche.save()
```

## 🐳 Docker

### **Docker Compose**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: agent_medical_ia
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data/

  redis:
    image: redis:latest

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A agent_medical_ia worker --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
```

### **Démarrage Docker**
```bash
# Construction et démarrage
docker-compose up --build

# En arrière-plan
docker-compose up -d

# Migrations
docker-compose exec web python manage.py migrate

# Création superuser
docker-compose exec web python manage.py createsuperuser
```

## 🔒 Sécurité

### **Authentification**
- ✅ **CustomUser** avec rôles (patient/médecin)
- ✅ **Validation des mots de passe** (longueur minimale)
- ✅ **Sessions Django** sécurisées
- ✅ **Protection CSRF** sur tous les formulaires

### **Données Médicales**
- ✅ **Chiffrement** des données sensibles
- ✅ **Signatures électroniques** pour validation
- ✅ **Audit trail** complet des modifications
- ✅ **Conformité RGPD** (consentement, droit à l'oubli)

### **API**
- ✅ **Authentification** requise pour toutes les routes
- ✅ **Validation** des données entrantes
- ✅ **Rate limiting** sur les appels IA
- ✅ **Logs** détaillés des actions

## 📱 Interface Utilisateur

### **Design Responsive**
- ✅ **Tailwind CSS** - Design moderne et responsive
- ✅ **Font Awesome** - Icônes médicales
- ✅ **JavaScript vanilla** - Interactions fluides
- ✅ **Progressive Web App** ready

### **Formulaires Intelligents**
- ✅ **Validation temps réel** côté client
- ✅ **Auto-complétion** des champs médicaux
- ✅ **Sauvegarde automatique** des brouillons
- ✅ **Indicateurs visuels** de progression

### **Accessibilité**
- ✅ **ARIA labels** pour screen readers
- ✅ **Navigation clavier** complète
- ✅ **Contrastes** respectant WCAG 2.1
- ✅ **Tailles de police** ajustables

## 🧪 Tests

### **Structure des Tests**
```bash
# Tests unitaires
python manage.py test

# Tests avec couverture
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### **Types de Tests**
- ✅ **Models** - Validation des données
- ✅ **Views** - Logique métier
- ✅ **Forms** - Validation formulaires
- ✅ **Integration** - Workflow complet
- ✅ **IA** - Mocks des APIs externes

## 📈 Monitoring

### **Logs**
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'agent_medical.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'chat': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### **Métriques**
- ✅ **Consultations par jour**
- ✅ **Temps d'analyse IA**
- ✅ **Taux de validation médecin**
- ✅ **Performance des modèles IA**

## 🤝 Contribution

### **Guide de Contribution**
1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrir** une Pull Request

### **Standards**
- ✅ **PEP 8** pour le code Python
- ✅ **Docstrings** pour toutes les fonctions
- ✅ **Tests** pour les nouvelles fonctionnalités
- ✅ **Type hints** pour la documentation

### **Structure des Commits**
```
feat: add new IA model integration
fix: resolve consultation form validation
docs: update API documentation
test: add unit tests for MessageIA model
```

## 📄 Licence

Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 📞 Support & Contact

- **Développeur Principal** : Victory Kasende
- **Email** : [votre-email@domain.com]
- **GitHub** : [@VictoryKasende](https://github.com/VictoryKasende)
- **Documentation** : [Wiki du projet](https://github.com/VictoryKasende/agent_medical_ia/wiki)

---

## 🏆 Remerciements

- **Django Community** pour le framework exceptionnel
- **OpenAI, Anthropic, Google** pour leurs APIs IA
- **Contributors** du projet open source
- **Communauté médicale** pour les retours et validations

---

*Développé avec ❤️ pour révolutionner la télémédecine avec l'IA*
>>>>>>> master
