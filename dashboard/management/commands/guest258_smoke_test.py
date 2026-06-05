from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse


class Command(BaseCommand):
    help = 'Executa testes rápidos nas páginas principais para validar se a aplicação arranca.'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='testserver', help='Host usado pelo Django Test Client.')

    def handle(self, *args, **options):
        client = Client(HTTP_HOST=options['host'])
        named_urls = [
            'home',
            'login',
            'client_register',
            'owner_register',
            'property_list',
            'about',
            'terms',
            'privacy',
            'healthz',
            'readyz',
        ]
        failures = []
        for name in named_urls:
            try:
                url = reverse(name)
            except Exception as exc:
                failures.append((name, 'reverse', str(exc)))
                continue
            response = client.get(url)
            if response.status_code >= 500:
                failures.append((name, response.status_code, url))
            else:
                self.stdout.write(self.style.SUCCESS(f'{name}: {response.status_code} {url}'))

        if failures:
            for failure in failures:
                self.stdout.write(self.style.ERROR(str(failure)))
            raise CommandError('Smoke test encontrou falhas.')
        self.stdout.write(self.style.SUCCESS('Smoke test concluído sem erros 5xx.'))
