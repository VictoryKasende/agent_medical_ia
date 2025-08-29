from django.core.management.base import BaseCommand
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer
from pathlib import Path

class Command(BaseCommand):
    help = "Exporte le schéma OpenAPI (JSON & YAML) dans le dossier docs/."

    def add_arguments(self, parser):
        parser.add_argument('--filename', default='openapi', help='Nom de base du fichier (sans extension)')

    def handle(self, *args, **options):
        base_name = options['filename']
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        json_bytes = OpenApiJsonRenderer().render(schema, renderer_context={})
        yaml_bytes = OpenApiYamlRenderer().render(schema, renderer_context={})

        docs_dir = Path('docs')
        docs_dir.mkdir(parents=True, exist_ok=True)

        json_path = docs_dir / f'{base_name}.json'
        yaml_path = docs_dir / f'{base_name}.yaml'

        json_path.write_bytes(json_bytes)
        yaml_path.write_bytes(yaml_bytes)

        self.stdout.write(self.style.SUCCESS(f'Schéma OpenAPI exporté: {json_path} & {yaml_path}'))
