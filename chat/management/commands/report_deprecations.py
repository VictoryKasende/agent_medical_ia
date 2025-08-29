from django.core.management.base import BaseCommand
from django.template.loader import get_template
from chat.deprecation import DEPRECATED_TEMPLATES

class Command(BaseCommand):
    help = "Affiche les templates dépréciés et leurs métadonnées"

    def handle(self, *args, **options):
        if not DEPRECATED_TEMPLATES:
            self.stdout.write(self.style.WARNING("Aucun template déprécié enregistré."))
            return
        self.stdout.write(self.style.MIGRATE_HEADING("Templates dépréciés:"))
        for path, meta in DEPRECATED_TEMPLATES.items():
            status = meta.status.upper()
            self.stdout.write(f"- {path} [{status}] -> retrait prévu: {meta.removal_target}")
            self.stdout.write(f"    Remplacement: {meta.replacement}")
            if meta.notes:
                self.stdout.write(f"    Notes: {meta.notes}")
            if meta.tickets:
                self.stdout.write(f"    Tickets: {meta.tickets}")
        self.stdout.write(self.style.SUCCESS("Rapport complété."))
