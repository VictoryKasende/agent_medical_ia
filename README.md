# MEDIAI - Système Intelligent de Consultation Médicale Assistée par IA

MEDIAI est une plateforme de gestion des consultations médicales intégrant l’intelligence artificielle générative (LLMs tels que GPT, Gemini, Claude) pour assister le personnel soignant dans la collecte, l’analyse, la synthèse et la validation des données médicales. Le système facilite aussi la communication avec les patients via WhatsApp.

## 1) Présentation générale

- **Objectifs**
  - Automatiser et assister le processus de consultation médicale à l’aide de LLMs
  - Améliorer la qualité et la rapidité des diagnostics
  - Faciliter la communication patient ↔ personnel médical
  - Offrir une solution accessible à distance pour les consultations

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

- Redirection: `dashboard/` (selon rôle/groupe)
- Patient: `dashboard/patient/`
- Médecin: `dashboard/medecin/`
- Proche aidant: `dashboard/proche/`
- Vues dédiées présentiel/distanciel:
  - Présentiel: `consultation/patient/`
  - Distant: `consultation/patient-distant/`, `consultations-distance/`, `api/consultations-distance/`

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


