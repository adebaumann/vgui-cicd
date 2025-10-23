from django.core.management.base import BaseCommand
from diagramm_proxy.diagram_cache import clear_cache


class Command(BaseCommand):
    help = 'Clear cached diagrams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            help='Diagram type to clear (e.g., plantuml, mermaid)',
        )

    def handle(self, *args, **options):
        diagram_type = options.get('type')
        if diagram_type:
            self.stdout.write(f'Clearing cache for {diagram_type}...')
            clear_cache(diagram_type)
        else:
            self.stdout.write('Clearing all diagram caches...')
            clear_cache()
        self.stdout.write(self.style.SUCCESS('Cache cleared successfully'))
