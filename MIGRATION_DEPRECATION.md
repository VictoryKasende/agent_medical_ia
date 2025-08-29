# Stratégie de Dépréciation des Templates Legacy

Ce document décrit le processus progressif de retrait des templates HTML legacy au profit d'une consommation API (DRF) + front dynamique.

## Objectifs
- Réduire progressivement le couplage logique entre vues Django server‑side et représentation des données.
- Offrir de la **cohabitation sécurisée** grâce au feature flag `API_COHAB_ENABLED`.
- Communiquer clairement aux développeurs quelles pages sont en voie de retrait.

## Outils Mis en Place
1. **Registre central** : `chat/deprecation.py` expose `DEPRECATED_TEMPLATES`.
2. **Context processor** : `chat.context_processors.deprecation_banner` injecte `deprecation_info` si la page visitée est marquée.
3. **Bannière UI** : ajout dans `header.html` d'un bandeau d'avertissement responsive.
4. **Commande de reporting** : `python manage.py report_deprecations` liste l'état courant.
5. **Progressive enhancement** : les templates marqués continuent de fonctionner (fallback SSR) mais consomment déjà l'API.

## Cycle de Vie d'une Dépréciation
| Étape | Statut | Description | Action | Durée indicative |
|-------|--------|-------------|--------|------------------|
| 1 | planned | Ciblée pour migration | Ajouter au registre (status=planned) | 1 semaine préparation |
| 2 | active | Bandeau visible, API disponible | Marquer `active`, instrumenter usage | 2–4 semaines |
| 3 | soft-removed | Redirection activable via flag | Retirer liens navigation principaux | 1–2 semaines |
| 4 | removed | Template supprimé | Nettoyage code + docs | définitif |

## Ajout d'un Nouveau Template à Déprécier
1. Ajouter une entrée dans `DEPRECATED_TEMPLATES` (status=planned).
2. Dès que l'alternative API est prête, passer `status="active"`.
3. Instrumenter (option : middleware métrique / logs) si besoin.
4. Avant retrait, changer en `status="soft-removed"` et prévoir redirection.
5. Supprimer fichiers + références (status="removed").

## Bonnes Pratiques
- Toujours conserver un **fallback SSR** tant que `active`.
- Ne pas retirer brutalement une page sans communication (PR description + CHANGELOG).
- Regrouper les retraits physiques dans une PR dédiée pour faciliter les revues.

## Templates Marqués (Initial)
- `chat/consultations_distance.html` : cible retrait `2025-10-01`. Remplacement: `/api/v1/consultations-distance/` + composant JS.

## Étapes Suivantes Possibles
- Ajouter une métrique (compteur Redis) des hits par template déprécié.
- Créer une commande `enforce_soft_removal` qui désactive automatiquement après la date cible.
- Intégrer un test CI qui échoue si la date cible est dépassée et le fichier existe toujours.

---
_Mise à jour : 2025-08-29_
