"""Central registry for legacy HTML template deprecation.

Each entry documents:
- removal_target: date (string YYYY-MM-DD) or version when we expect removal
- replacement: suggested new SPA/endpoint or DRF route
- status: planned | active | removed
- tickets: optional references (JIRA/GitHub) for tracking
- notes: rationale / migration hints

This lightweight module avoids scattering ad‑hoc warnings across views.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass(frozen=True)
class TemplateDeprecation:
    name: str
    removal_target: str
    replacement: str
    status: str = "active"
    tickets: Optional[str] = None
    notes: str = ""


DEPRECATED_TEMPLATES: Dict[str, TemplateDeprecation] = {
    # Première vague: pages dont les données seront servies par l'API + front dynamique
    "chat/consultations_distance.html": TemplateDeprecation(
        name="Consultations distance (liste + détails)",
        removal_target="2025-10-01",
        replacement="/api/v1/consultations-distance/ + composant JS/SPA",
        status="active",
        notes="Progressive enhancement en place; basculer vers rendu 100% API + composant dynamique."
    ),
    # Ajouter ici d'autres templates à mesure que l'on migre
}


def get_deprecation(template_name: str) -> Optional[TemplateDeprecation]:
    return DEPRECATED_TEMPLATES.get(template_name)
