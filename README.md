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
