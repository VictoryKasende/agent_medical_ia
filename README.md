# 🏥 MediAI - Système de Consultation Médicale Intelligente

[![CI/CD](https://github.com/VictoryKasende/agent_medical_ia/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/VictoryKasende/agent_medical_ia/actions)
[![codecov](https://codecov.io/gh/VictoryKasende/agent_medical_ia/branch/main/graph/badge.svg)](https://codecov.io/gh/VictoryKasende/agent_medical_ia)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Django 4.2](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Plateforme moderne de gestion de consultations médicales avec intelligence artificielle intégrée.**

MediAI est une API REST Django permettant la gestion complète des consultations médicales, l'analyse intelligente des symptômes, et la coordination patient-médecin avec notifications en temps réel.

---

## 📋 Table des Matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Utilisation](#-utilisation)
- [API Documentation](#-api-documentation)
- [Tests](#-tests)
- [Déploiement](#-déploiement)
- [Contribution](#-contribution)
- [Sécurité](#-sécurité)
- [License](#-license)

---

## ✨ Fonctionnalités

### 🎯 Fonctionnalités Principales (P0)

- **Gestion des Fiches de Consultation**
  - Création et modification de fiches patient
  - Validation et rejet par médecin
  - Historique complet des consultations
  - Export PDF des fiches

- **Intelligence Artificielle**
  - Analyse automatique des symptômes (GPT-4, Claude, Gemini)
  - Génération de diagnostics préliminaires
  - Suggestions de traitements
  - Système de conversation IA multi-modèles

- **Gestion des Rendez-vous**
  - Demande de rendez-vous patient → médecin
  - Confirmation/déclinaison par médecin
  - Modes: Présentiel & Distanciel
  - Notifications WhatsApp automatiques

- **Authentification & Autorisation**
  - JWT Authentication (2h expiration)
  - Rôles: Patient, Médecin, Admin
  - Permissions granulaires par endpoint
  - Session-based auth pour interface web

### 🚀 Fonctionnalités Avancées (P1)

- **Gestion Médecin**
  - Disponibilités & exceptions
  - Export calendrier ICS
  - Agenda centralisé
  - Profils médecins enrichis

- **Communication**
  - Notifications WhatsApp (Twilio)
  - Messagerie fiche-médecin
  - Alertes en temps réel

- **Export de Données**
  - Formats: PDF, CSV, Excel, Parquet
  - Export asynchrone (Celery)
  - Jobs d'export traçables

- **Références Médicales**
  - Attachement de références bibliographiques
  - Résultats de laboratoire
  - Pièces jointes multiples

---

## 🏗️ Architecture

### Stack Technique

```
┌─────────────────────────────────────────────┐
│           Frontend (React/Vue)              │
│        http://localhost:5173                │
└──────────────────┬──────────────────────────┘
                   │ HTTPS/WSS
┌──────────────────▼──────────────────────────┐
│         Django REST API (v4.2.25)           │
│    - DRF (REST Framework)                   │
│    - JWT Authentication                     │
│    - OpenAPI/Swagger Docs                   │
│    - CORS Enabled                           │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴───────────┬──────────────┐
        │                      │              │
┌───────▼────────┐  ┌─────────▼────┐  ┌─────▼────────┐
│   PostgreSQL   │  │    Redis      │  │   Celery     │
│   (Database)   │  │   (Cache)     │  │  (Tasks)     │
│   Port: 5432   │  │  Port: 6379   │  │              │
└────────────────┘  └───────────────┘  └──────────────┘
```

### Architecture en Couches

```
├── Presentation Layer (API/Views)
│   ├── REST API Endpoints (DRF ViewSets)
│   ├── Authentication (JWT)
│   └── Serializers (Data Validation)
│
├── Business Logic Layer (Services)
│   ├── notification_service.py (WhatsApp/SMS)
│   ├── llm_config.py (IA Multi-modèles)
│   └── tasks.py (Celery Async Tasks)
│
├── Data Access Layer (Models/Repository)
│   ├── Models (Django ORM)
│   ├── Migrations
│   └── Managers (Custom QuerySets)
│
└── Infrastructure Layer
    ├── PostgreSQL (Persistent Storage)
    ├── Redis (Caching & Message Broker)
    └── Celery (Async Task Queue)
```

### Applications Django

- **`authentication/`**: Gestion utilisateurs, JWT, permissions
- **`chat/`**: Fiches, conversations IA, rendez-vous, messages
- **`agent_medical_ia/`**: Configuration globale, celery, URLs

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommandé)

### Installation Standard

1. **Cloner le repository**
   ```bash
   git clone https://github.com/VictoryKasende/agent_medical_ia.git
   cd agent_medical_ia
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Pour le développement
   ```

4. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos configurations
   ```

5. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

6. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

7. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

### Installation avec Docker (Recommandé)

1. **Lancer tous les services**
   ```bash
   docker-compose up -d
   ```

2. **Appliquer les migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Créer un superutilisateur**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Accéder à l'application**
   - API: http://localhost:8000
   - Swagger: http://localhost:8000/api/schema/swagger-ui/
   - Admin: http://localhost:8000/admin/

---

## ⚙️ Configuration

### Variables d'Environnement Essentielles

```bash
# Django Core
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/mediai_db

# Redis & Celery
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# External APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# JWT
JWT_ACCESS_TOKEN_LIFETIME=120  # minutes
JWT_REFRESH_TOKEN_LIFETIME=1440  # minutes (24h)

# CORS (Frontend)
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

Pour la configuration complète, voir [CONFIGURATION.md](docs/CONFIGURATION.md).

---

## 📚 API Documentation

### Documentation Interactive

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI JSON**: http://localhost:8000/api/schema/

### Endpoints Principaux

#### Authentication
```bash
POST /api/v1/auth/token/           # Obtenir JWT tokens
POST /api/v1/auth/refresh/         # Rafraîchir access token
POST /api/v1/auth/users/register/  # Inscription
GET  /api/v1/auth/me/              # Profil utilisateur
```

#### Fiches de Consultation
```bash
GET    /api/v1/fiche-consultation/            # Liste fiches
POST   /api/v1/fiche-consultation/            # Créer fiche
GET    /api/v1/fiche-consultation/{id}/       # Détail fiche
PATCH  /api/v1/fiche-consultation/{id}/       # Modifier fiche
POST   /api/v1/fiche-consultation/{id}/validate/   # Valider (médecin)
POST   /api/v1/fiche-consultation/{id}/reject/     # Rejeter (médecin)
POST   /api/v1/fiche-consultation/{id}/relancer/   # Relancer analyse IA
POST   /api/v1/fiche-consultation/{id}/send-whatsapp/  # Envoyer WhatsApp
```

#### Rendez-vous
```bash
GET    /api/v1/appointments/           # Liste rendez-vous
POST   /api/v1/appointments/           # Créer rendez-vous
GET    /api/v1/appointments/{id}/      # Détail rendez-vous
POST   /api/v1/appointments/{id}/confirm/   # Confirmer (médecin)
POST   /api/v1/appointments/{id}/decline/   # Décliner (médecin)
POST   /api/v1/appointments/{id}/cancel/    # Annuler
GET    /api/v1/appointments/mon-agenda/     # Agenda médecin
```

#### Conversations IA
```bash
GET    /api/v1/conversations/                  # Liste conversations
POST   /api/v1/conversations/                  # Nouvelle conversation
GET    /api/v1/conversations/{id}/messages/    # Messages conversation
POST   /api/v1/conversations/{id}/messages/    # Ajouter message
```

Pour plus de détails, consultez:
- [README_AUTH_API.md](README_AUTH_API.md)
- [README_CONSULTATIONS_API.md](README_CONSULTATIONS_API.md)
- [README_IA_CONVERSATIONS.md](README_IA_CONVERSATIONS.md)
- [README_MEDECINS_API.md](README_MEDECINS_API.md)

---

## 🧪 Tests

### Exécuter les Tests

```bash
# Tous les tests
pytest

# Tests avec coverage
pytest --cov

# Tests spécifiques
pytest chat/tests/test_models.py
pytest chat/tests/test_api_appointments.py

# Tests par marqueur
pytest -m unit          # Tests unitaires seulement
pytest -m integration   # Tests d'intégration seulement

# Tests avec rapport HTML
pytest --cov --cov-report=html
# Ouvrir htmlcov/index.html
```

### Structure des Tests

```
chat/tests/
├── __init__.py
├── conftest.py                 # Fixtures pytest
├── test_models.py              # Tests unitaires modèles
├── test_api_appointments.py    # Tests API rendez-vous
├── test_api_fiches.py          # Tests API fiches
├── test_services.py            # Tests services métier
└── test_permissions.py         # Tests permissions
```

### Qualité du Code

```bash
# Formatage
black chat/ authentication/

# Tri des imports
isort chat/ authentication/

# Linting
flake8 chat/ authentication/

# Type checking
mypy chat/ authentication/

# Sécurité
bandit -r chat/ authentication/
safety check

# Tout en une fois (pre-commit)
pre-commit run --all-files
```

---

## 🚢 Déploiement

### Déploiement Docker

```bash
# Build et démarrage
docker-compose -f docker-compose.prod.yml up -d --build

# Migrations
docker-compose exec web python manage.py migrate

# Collectstatic
docker-compose exec web python manage.py collectstatic --noinput

# Créer admin
docker-compose exec web python manage.py createsuperuser
```

### Déploiement Manuel

Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour:
- Configuration Nginx
- Configuration Gunicorn
- SSL/HTTPS
- Monitoring
- Backups

---

## 🤝 Contribution

Nous accueillons les contributions ! Veuillez suivre ces étapes:

1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Installer** pre-commit hooks: `pre-commit install`
4. **Faire** vos modifications
5. **Exécuter** les tests: `pytest`
6. **Commiter** vos changements (`git commit -m 'Add: Amazing Feature'`)
7. **Pusher** vers la branche (`git push origin feature/AmazingFeature`)
8. **Ouvrir** une Pull Request

### Standards de Code

- **Style**: PEP 8, Black formatter (120 chars)
- **Imports**: isort avec profile black
- **Docstrings**: Google style
- **Types**: Type hints pour toutes les fonctions publiques
- **Tests**: Coverage > 80%
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/)

---

## 🔒 Sécurité

### Rapporter une Vulnérabilité

Si vous découvrez une vulnérabilité de sécurité, veuillez NE PAS créer d'issue publique.
Envoyez un email à: security@mediai.com

### Best Practices Implémentées

- ✅ JWT avec expiration courte (2h)
- ✅ Permissions granulaires par endpoint
- ✅ CORS configuration stricte
- ✅ Rate limiting (optionnel)
- ✅ SQL Injection protection (Django ORM)
- ✅ XSS protection
- ✅ CSRF protection
- ✅ Secrets dans variables d'environnement
- ✅ HTTPS only en production

---

## 📄 License

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 👥 Équipe

- **Victory Kasende** - Développeur Principal - [@VictoryKasende](https://github.com/VictoryKasende)

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/VictoryKasende/agent_medical_ia/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VictoryKasende/agent_medical_ia/discussions)

---

## 🙏 Remerciements

- Django & Django REST Framework
- OpenAI GPT-4, Anthropic Claude, Google Gemini
- Twilio WhatsApp API
- PostgreSQL, Redis, Celery
- Et tous les contributeurs !

---

<div align="center">

**Fait avec ❤️ pour améliorer l'accès aux soins de santé**

[⬆ Retour en haut](#-mediai---système-de-consultation-médicale-intelligente)

</div>
