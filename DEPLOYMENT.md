# 🔧 Configuration et Déploiement - Agent Médical IA

## Variables d'Environnement

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

### Django Core
```env
# Sécurité Django
DJANGO_SECRET_KEY=votre-clé-secrète-très-longue-et-complexe-de-50-caractères-minimum
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com

# Mode développement
DEVELOPMENT_MODE=False
```

### Base de Données
```env
# PostgreSQL (Production recommandée)
DATABASE_URL=postgresql://username:password@localhost:5432/agent_medical_ia

# Ou SQLite (développement uniquement)
# DATABASE_URL=sqlite:///db.sqlite3
```

### Cache et Sessions
```env
# Redis (obligatoire pour les sessions et cache)
REDIS_URL=redis://127.0.0.1:6379/1

# Celery (tâches asynchrones)
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
```

### APIs Intelligence Artificielle
```env
# OpenAI (obligatoire)
OPENAI_API_KEY=sk-votre-clé-openai-ici

# Google Gemini (obligatoire)
GOOGLE_API_KEY=votre-clé-google-gemini-ici

# Anthropic Claude (optionnel)
ANTHROPIC_API_KEY=sk-ant-votre-clé-claude-ici
```

### Notifications (Twilio)
```env
# SMS et WhatsApp via Twilio (optionnel)
TWILIO_ACCOUNT_SID=votre-account-sid-twilio
TWILIO_AUTH_TOKEN=votre-auth-token-twilio
TWILIO_PHONE_NUMBER=+33123456789
TWILIO_WHATSAPP_NUMBER=+14155238886
```

### Stockage Fichiers
```env
# Stockage local (développement)
MEDIA_ROOT=/chemin/vers/media/
STATIC_ROOT=/chemin/vers/static/

# AWS S3 (production - optionnel)
# AWS_ACCESS_KEY_ID=votre-access-key
# AWS_SECRET_ACCESS_KEY=votre-secret-key
# AWS_STORAGE_BUCKET_NAME=votre-bucket
# AWS_S3_REGION_NAME=eu-west-1
```

## 🐳 Déploiement Docker

### 1. Docker Compose (Recommandé)

Le projet inclut un `docker-compose.yml` configuré. Pour démarrer :

```bash
# Cloner le projet
git clone https://github.com/VictoryKasende/agent_medical_ia.git
cd agent_medical_ia

# Copier et éditer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Construire et démarrer les services
docker-compose up --build -d

# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser

# Collecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput
```

### 2. Services Docker

Le stack inclut :
- **web** : Application Django + Gunicorn
- **db** : PostgreSQL 15
- **redis** : Cache et broker Celery
- **celery** : Worker pour tâches IA asynchrones

## 📦 Installation Manuelle

### Prérequis
- Python 3.11+
- PostgreSQL 15+
- Redis 6+
- Node.js 18+ (pour Tailwind CSS)

### Étapes

```bash
# 1. Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Dépendances Python
pip install -r requirements.txt

# 3. Dépendances système (WeasyPrint)
# Ubuntu/Debian
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

# macOS
brew install pango

# Windows
# Installer GTK+ depuis https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

# 4. Base de données
createdb agent_medical_ia
python manage.py migrate

# 5. Données initiales
python manage.py createsuperuser
python manage.py collectstatic

# 6. Démarrage développement
# Terminal 1 : Redis
redis-server

# Terminal 2 : Celery
celery -A agent_medical_ia worker --loglevel=info

# Terminal 3 : Django
python manage.py runserver
```

## 🔧 Configuration Serveur Web

### Nginx (Production)

```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    
    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;
    
    # SSL/TLS
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Fichiers statiques
    location /static/ {
        alias /path/to/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers média
    location /media/ {
        alias /path/to/media/;
        expires 1M;
    }
    
    # Application Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (si nécessaire)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Taille max upload
    client_max_body_size 50M;
}
```

### Gunicorn (WSGI)

Créer `gunicorn.conf.py` :

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
preload_app = True
reload = False
daemon = False
user = "www-data"
group = "www-data"
```

Commande de démarrage :
```bash
gunicorn agent_medical_ia.wsgi:application -c gunicorn.conf.py
```

## 🔐 Sécurité Production

### Variables Sensibles
- ✅ Utiliser des clés API avec permissions minimales
- ✅ Stocker les secrets dans un gestionnaire sécurisé
- ✅ Activer l'authentification 2FA sur les comptes de service

### Base de Données
- ✅ Utiliser SSL/TLS pour les connexions
- ✅ Restreindre l'accès par IP
- ✅ Sauvegardes automatiques chiffrées

### Application
- ✅ HTTPS obligatoire (redirections)
- ✅ Headers de sécurité (CSP, HSTS, etc.)
- ✅ Rate limiting sur les APIs
- ✅ Logs de sécurité activés

### Monitoring
- ✅ Surveillance des erreurs (Sentry)
- ✅ Métriques système (CPU, RAM, disque)
- ✅ Alertes sur les échecs d'API IA
- ✅ Logs centralisés

## 📊 Base de Données

### Migrations

```bash
# Créer migration pour nouveaux modèles
python manage.py makemigrations chat

# Appliquer migrations
python manage.py migrate

# Migrations manuelles si nécessaire
python manage.py sqlmigrate chat 0001
```

### Sauvegarde

```bash
# Dump PostgreSQL
pg_dump agent_medical_ia > backup_$(date +%Y%m%d).sql

# Restauration
psql agent_medical_ia < backup_20241003.sql
```

## 🧪 Tests

### Tests Unitaires
```bash
# Tous les tests
python manage.py test

# Tests avec couverture
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Tests API
```bash
# Tests spécifiques aux APIs
python manage.py test chat.tests.test_api
```

## 📈 Performance

### Optimisations Django
- ✅ Cache Redis activé
- ✅ Sessions en cache
- ✅ Compression GZip
- ✅ Fichiers statiques optimisés

### Optimisations IA
- ✅ Cache des diagnostics IA
- ✅ Timeout configuré (120s)
- ✅ Retry logique sur les échecs API
- ✅ Parallélisation des modèles

## 🐛 Dépannage

### Erreurs Communes

**WeasyPrint ne s'installe pas :**
```bash
# Installer les dépendances système d'abord
# Puis réessayer pip install weasyprint
```

**Celery ne démarre pas :**
```bash
# Vérifier Redis
redis-cli ping

# Vérifier la configuration
celery -A agent_medical_ia inspect active
```

**Erreurs d'API IA :**
```bash
# Vérifier les clés API
python manage.py shell
>>> from chat.llm_config import gpt4
>>> gpt4.invoke([{"content": "test"}])
```

### Logs

```bash
# Logs Django
tail -f agent_medical.log

# Logs Docker
docker-compose logs -f web
docker-compose logs -f celery

# Logs système
journalctl -u nginx
journalctl -u postgresql
```

## 📱 Endpoints API

Une fois déployé, l'API est accessible via :

- **Documentation** : `/api/docs/`
- **Schema OpenAPI** : `/api/schema/`
- **Fiches consultation** : `/api/v1/fiche-consultation/`
- **Rendez-vous** : `/api/v1/appointments/`
- **Laboratoire** : `/api/v1/lab-results/`
- **Pièces jointes** : `/api/v1/attachments/`
- **Références** : `/api/v1/references/`

---

*Documentation mise à jour le 03/10/2025*