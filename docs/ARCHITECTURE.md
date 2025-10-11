# 🏛️ Architecture MediAI - Documentation Technique

## Vue d'Ensemble

MediAI est construit sur une **architecture en couches (Layered Architecture)** avec séparation claire des responsabilités, suivant les principes **SOLID** et les **design patterns** industriels.

---

## 🎯 Principes Architecturaux

### 1. Separation of Concerns (SoC)
Chaque module a une responsabilité unique et bien définie.

### 2. Dependency Inversion Principle (DIP)
Les modules de haut niveau ne dépendent pas des modules de bas niveau. Les deux dépendent d'abstractions.

### 3. Single Source of Truth (SSOT)
PostgreSQL est la source unique de vérité. Redis sert uniquement de cache.

### 4. Fail-Safe Design
En cas d'échec d'un service externe (IA, WhatsApp), l'application continue de fonctionner.

---

## 📐 Architecture en Couches

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  REST API    │  │   WebViews   │  │   Admin UI   │      │
│  │  (DRF)       │  │  (Templates) │  │   (Django)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│    Serializers      Context         ModelAdmin              │
│    Permissions      Forms            Actions                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Services   │  │   Managers   │  │    Tasks     │      │
│  │              │  │              │  │   (Celery)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│  Business Rules    Query Logic      Async Jobs              │
│  Calculations      Aggregations     Notifications           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   DATA ACCESS LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Models     │  │  Migrations  │  │  Validators  │      │
│  │  (ORM)       │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│   Django ORM         Schema         Data Rules              │
│   QuerySets          Versions        Constraints            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │  External    │      │
│  │              │  │              │  │   APIs       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│   Persistence         Cache            OpenAI, Twilio       │
│   Transactions        Sessions         Anthropic, Google    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Structure du Projet

```
agent_medical_ia/
├── agent_medical_ia/              # Configuration globale
│   ├── settings.py                # Settings Django
│   ├── urls.py                    # URL routing principal
│   ├── celery.py                  # Configuration Celery
│   ├── asgi.py                    # ASGI config
│   └── wsgi.py                    # WSGI config
│
├── authentication/                # Module authentification
│   ├── models.py                  # CustomUser, UserProfile
│   ├── api_views.py               # ViewSets API
│   ├── serializers.py             # DRF Serializers
│   ├── permissions.py             # Permissions custom
│   ├── jwt_views.py               # JWT endpoints
│   └── tests/                     # Tests auth
│
├── chat/                          # Module principal
│   ├── models.py                  # Modèles métier
│   │   ├── FicheConsultation
│   │   ├── Conversation
│   │   ├── MessageIA
│   │   ├── Appointment
│   │   ├── FicheMessage
│   │   ├── FicheReference
│   │   └── ...
│   │
│   ├── api_views.py               # ViewSets REST API
│   │   ├── FicheConsultationViewSet
│   │   ├── ConversationViewSet
│   │   ├── AppointmentViewSet
│   │   └── ...
│   │
│   ├── serializers.py             # Serializers DRF
│   ├── permissions.py             # Permissions métier
│   ├── tasks.py                   # Celery tasks
│   ├── llm_config.py              # Configuration IA
│   ├── notification_service.py    # Service notifications
│   │
│   ├── services/                  # Business logic (à créer)
│   │   ├── __init__.py
│   │   ├── fiche_service.py
│   │   ├── appointment_service.py
│   │   └── ia_service.py
│   │
│   ├── repositories/              # Data access (à créer)
│   │   ├── __init__.py
│   │   ├── fiche_repository.py
│   │   └── appointment_repository.py
│   │
│   ├── utils/                     # Utilitaires
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── helpers.py
│   │   └── exceptions.py
│   │
│   ├── constants.py               # Constantes globales
│   │
│   └── tests/                     # Tests organisés
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_api_appointments.py
│       ├── test_services.py
│       └── ...
│
├── staticfiles/                   # Fichiers statiques collectés
├── docs/                          # Documentation
├── .github/workflows/             # CI/CD pipelines
├── requirements.txt               # Dépendances prod
├── requirements-dev.txt           # Dépendances dev
├── pytest.ini                     # Config pytest
├── pyproject.toml                 # Config outils (black, mypy, etc.)
├── .flake8                        # Config flake8
├── .pre-commit-config.yaml        # Pre-commit hooks
└── docker-compose.yml             # Services Docker
```

---

## 🔄 Flux de Données

### 1. Flux de Création de Fiche

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │ POST /api/v1/fiche-consultation/
       │ {nom, prenom, symptomes, ...}
       ↓
┌──────────────────────┐
│  FicheConsultation   │
│     ViewSet          │
│  (api_views.py)      │
└──────┬───────────────┘
       │ 1. Validation (serializer)
       │ 2. perform_create()
       ↓
┌──────────────────────┐
│  FicheConsultation   │
│      Model           │
│   (models.py)        │
└──────┬───────────────┘
       │ 3. save() → PostgreSQL
       │ 4. Signal post_save
       ↓
┌──────────────────────┐
│  Celery Task         │
│  analyse_symptomes   │
│    (tasks.py)        │
└──────┬───────────────┘
       │ 5. Async task
       │ 6. Appel IA (GPT-4, Claude, Gemini)
       ↓
┌──────────────────────┐
│  IA Service          │
│  (llm_config.py)     │
└──────┬───────────────┘
       │ 7. Traitement réponses IA
       │ 8. Update fiche.diagnostic_ia
       ↓
┌──────────────────────┐
│  PostgreSQL          │
│  (Database)          │
└──────────────────────┘
```

### 2. Flux de Notification WhatsApp

```
┌─────────────┐
│  Médecin    │
│  (Frontend) │
└──────┬──────┘
       │ POST /api/v1/fiche-consultation/{id}/send-whatsapp/
       ↓
┌──────────────────────┐
│  send_whatsapp       │
│    Action            │
│  (api_views.py)      │
└──────┬───────────────┘
       │ 1. Check permissions (IsMedecin)
       │ 2. Appel service
       ↓
┌──────────────────────┐
│  notification_       │
│   service.py         │
└──────┬───────────────┘
       │ 3. Check cache (idempotence)
       │ 4. Format message template
       ↓
┌──────────────────────┐
│  Redis Cache         │
│  (Déduplication)     │
└──────┬───────────────┘
       │ 5. Cache miss → proceed
       ↓
┌──────────────────────┐
│  Twilio API          │
│  (WhatsApp)          │
└──────┬───────────────┘
       │ 6. Send message
       │ 7. Return SID
       ↓
┌──────────────────────┐
│  Cache result        │
│  (Redis)             │
└──────┬───────────────┘
       │ 8. Store SID in cache (TTL: 1h)
       │ 9. Response to client
       ↓
┌──────────────────────┐
│  Client Response     │
│  {success: true,     │
│   message_sid: ...}  │
└──────────────────────┘
```

### 3. Flux de Rendez-vous

```
┌─────────────┐
│  Patient    │
└──────┬──────┘
       │ POST /api/v1/appointments/
       │ {medecin, requested_start, ...}
       ↓
┌──────────────────────┐
│  AppointmentViewSet  │
│  perform_create()    │
└──────┬───────────────┘
       │ 1. Auto-fill patient=request.user
       │ 2. Validate dates (end > start)
       │ 3. Save to DB
       ↓
┌──────────────────────┐
│  Appointment Model   │
│  status='pending'    │
└──────┬───────────────┘
       │ 4. Notification médecin (optionnel)
       ↓
┌─────────────┐
│  Médecin    │
└──────┬──────┘
       │ POST /api/v1/appointments/{id}/confirm/
       │ {confirmed_start, confirmed_end}
       ↓
┌──────────────────────┐
│  confirm Action      │
└──────┬───────────────┘
       │ 5. Check permissions (IsMedecin)
       │ 6. Update status='confirmed'
       │ 7. Set confirmed_start/end
       ↓
┌──────────────────────┐
│  Notification        │
│  Patient             │
└──────────────────────┘
```

---

## 🎨 Design Patterns Utilisés

### 1. **ViewSet Pattern** (DRF)
```python
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    CRUD complet + actions custom.
    Sépare les responsabilités (list, create, update, delete, custom).
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        # Action custom
        pass
```

### 2. **Service Layer Pattern**
```python
# services/notification_service.py
def send_consultation_notification(fiche, force_resend=False):
    """
    Business logic centralisée.
    Réutilisable depuis views, tasks, management commands.
    """
    # Logic here
    pass
```

### 3. **Repository Pattern** (à implémenter)
```python
# repositories/fiche_repository.py
class FicheRepository:
    """Abstraction de l'accès aux données."""
    
    @staticmethod
    def get_by_status(status):
        return FicheConsultation.objects.filter(status=status)
    
    @staticmethod
    def get_patient_fiches(user):
        return FicheConsultation.objects.filter(user=user)
```

### 4. **Strategy Pattern** (IA Multi-modèles)
```python
# llm_config.py
class LLMStrategy:
    def analyze(self, prompt): ...

class GPT4Strategy(LLMStrategy):
    def analyze(self, prompt):
        # OpenAI specific
        pass

class ClaudeStrategy(LLMStrategy):
    def analyze(self, prompt):
        # Anthropic specific
        pass
```

### 5. **Factory Pattern** (Serializers)
```python
class FicheConsultationViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        """Factory pour choisir le serializer."""
        if self.request.query_params.get('is_patient_distance'):
            return FicheConsultationDistanceSerializer
        return FicheConsultationSerializer
```

---

## 🔐 Sécurité

### 1. **Authentication Flow**

```
Client Request
     ↓
[JWT Token in Header]
     ↓
Django Middleware
     ↓
SimpleJWT Authentication
     ↓
Parse & Validate Token
     ↓
Get User from Token
     ↓
Attach to request.user
     ↓
Permission Classes
     ↓
ViewSet Logic
```

### 2. **Permission Hierarchy**

```python
permissions.AllowAny              # Publique
    ↓
permissions.IsAuthenticated       # Connecté
    ↓
IsPatient / IsMedecin             # Rôle spécifique
    ↓
IsOwnerOrAdmin                    # Propriétaire ou admin
    ↓
Custom Permission Logic           # Business rules
```

### 3. **Input Validation**

```
Client Data
     ↓
DRF Serializer Validation
     ├─ Field-level validation
     ├─ Object-level validation
     └─ Custom validators
     ↓
Business Logic Validation
     ├─ Service layer checks
     └─ Model constraints
     ↓
Database Constraints
     ├─ unique=True
     ├─ null=False
     └─ ForeignKey checks
```

---

## ⚡ Performance

### 1. **Caching Strategy**

```python
# Niveaux de cache
CACHE_LEVELS = {
    'L1': 'Django view cache',        # Vues entières
    'L2': 'Django query cache',       # QuerySets
    'L3': 'Redis cache',              # Données métier
    'L4': 'PostgreSQL query cache',   # DB interne
}

# Exemple d'utilisation
@cache_page(60 * 15)  # 15 minutes
def expensive_view(request):
    pass

# Ou programmatique
from django.core.cache import cache

def get_medecin_availability(medecin_id):
    key = f'availability:{medecin_id}'
    result = cache.get(key)
    if not result:
        result = calculate_availability(medecin_id)
        cache.set(key, result, timeout=300)
    return result
```

### 2. **Database Optimization**

```python
# ❌ BAD: N+1 queries
appointments = Appointment.objects.all()
for appt in appointments:
    print(appt.patient.username)  # 1 query per loop!

# ✅ GOOD: Single query with JOIN
appointments = Appointment.objects.select_related(
    'patient', 'medecin'
).all()

# ✅ GOOD: Prefetch related
fiches = FicheConsultation.objects.prefetch_related(
    'conversations',
    'conversations__messageia_set'
).all()

# ✅ GOOD: Indexes
class Appointment(models.Model):
    patient = models.ForeignKey(db_index=True)
    status = models.CharField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['patient', 'status']),
        ]
```

### 3. **Async Tasks**

```python
# ❌ BAD: Blocking
def validate_fiche(request):
    fiche.status = 'validated'
    fiche.save()
    send_whatsapp_notification(fiche)  # BLOCKS!
    return Response({'status': 'ok'})

# ✅ GOOD: Async
def validate_fiche(request):
    fiche.status = 'validated'
    fiche.save()
    send_whatsapp_notification.delay(fiche.id)  # Async!
    return Response({'status': 'ok'})
```

---

## 📊 Monitoring & Observabilité

### Métriques Clés

```python
# À implémenter avec Prometheus/Grafana
METRICS = {
    'api_requests_total': Counter,
    'api_request_duration_seconds': Histogram,
    'api_errors_total': Counter,
    'celery_tasks_total': Counter,
    'celery_task_duration_seconds': Histogram,
    'whatsapp_notifications_sent': Counter,
    'ia_analyses_total': Counter,
}
```

### Health Checks

```python
# /api/health/
def health_check(request):
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
        'external_apis': check_external_apis(),
    }
    status = 200 if all(checks.values()) else 503
    return JsonResponse({
        'status': 'healthy' if all(checks.values()) else 'unhealthy',
        'checks': checks
    }, status=status)
```

---

## 🚀 Évolutions Futures

### Phase 2
- [ ] WebSocket pour notifications temps réel
- [ ] GraphQL API en complément REST
- [ ] Microservices (IA, Notifications)
- [ ] Event Sourcing pour audit trail
- [ ] CQRS pattern pour séparation read/write

### Phase 3
- [ ] Machine Learning pour prédictions
- [ ] Blockchain pour traçabilité
- [ ] Multi-tenant architecture
- [ ] Kubernetes deployment

---

**Dernière mise à jour**: 2025-10-07  
**Version**: 1.0.0  
**Auteur**: Victory Kasende
