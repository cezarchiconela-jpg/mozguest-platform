from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Verifica se o +258 Guest está preparado para produção.'

    def add_arguments(self, parser):
        parser.add_argument('--strict', action='store_true', help='Falha quando encontrar avisos críticos.')

    def handle(self, *args, **options):
        strict = options['strict']
        errors = []
        warnings = []

        def require(condition, message):
            if not condition:
                errors.append(message)

        def warn(condition, message):
            if not condition:
                warnings.append(message)

        require(not settings.DEBUG, 'DJANGO_DEBUG deve estar False em produção.')
        require(bool(settings.SECRET_KEY) and settings.SECRET_KEY != 'guest258-local-dev-key-only', 'DJANGO_SECRET_KEY deve ser forte e diferente da chave local.')
        require(bool(settings.ALLOWED_HOSTS), 'DJANGO_ALLOWED_HOSTS deve estar definido.')
        require(bool(settings.CSRF_TRUSTED_ORIGINS), 'DJANGO_CSRF_TRUSTED_ORIGINS deve estar definido.')
        require(settings.SESSION_COOKIE_SECURE, 'SESSION_COOKIE_SECURE deve estar True em HTTPS.')
        require(settings.CSRF_COOKIE_SECURE, 'CSRF_COOKIE_SECURE deve estar True em HTTPS.')
        warn(settings.SECURE_SSL_REDIRECT, 'DJANGO_SECURE_SSL_REDIRECT está False. Confirmar se o proxy/Render faz HTTPS obrigatório.')
        warn(settings.SECURE_HSTS_SECONDS > 0, 'SECURE_HSTS_SECONDS está 0. Activar HSTS após confirmar domínio HTTPS.')

        engine = settings.DATABASES['default']['ENGINE']
        warn('postgresql' in engine, f'Base de dados actual não parece PostgreSQL: {engine}')

        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        except Exception as exc:
            errors.append(f'Falha ao ligar à base de dados: {exc.__class__.__name__}: {exc}')

        storage_backend = getattr(settings, 'GUEST258_STORAGE_BACKEND', 'local')
        if storage_backend == 'local':
            warn(getattr(settings, 'DJANGO_SERVE_MEDIA', False) is False, 'Uploads estão em storage local. Em Render, usar Persistent Disk ou storage S3 compatível.')
        elif storage_backend in {'s3', 's3_compatible'}:
            require(bool(getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')), 'AWS_STORAGE_BUCKET_NAME obrigatório quando GUEST258_STORAGE_BACKEND=s3.')
            require(bool(getattr(settings, 'AWS_ACCESS_KEY_ID', '')), 'AWS_ACCESS_KEY_ID obrigatório quando GUEST258_STORAGE_BACKEND=s3.')
            require(bool(getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')), 'AWS_SECRET_ACCESS_KEY obrigatório quando GUEST258_STORAGE_BACKEND=s3.')

        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        warn('console' not in email_backend, 'EMAIL_BACKEND ainda está em console. Configurar SMTP real antes do lançamento.')
        warn(bool(getattr(settings, 'DEFAULT_FROM_EMAIL', '')), 'DEFAULT_FROM_EMAIL deve estar definido.')

        payment_mode = getattr(settings, 'GUEST258_PAYMENT_GATEWAY_MODE', 'sandbox')
        if payment_mode == 'live':
            warn(bool(getattr(settings, 'GUEST258_GATEWAY_CALLBACK_TOKEN', '')), 'GUEST258_GATEWAY_CALLBACK_TOKEN deve estar definido em live.')
            warn(bool(getattr(settings, 'MPESA_INITIATE_URL', '') or getattr(settings, 'EMOLA_INITIATE_URL', '')), 'Nenhum endpoint de gateway real configurado.')
        else:
            warn(False, 'GUEST258_PAYMENT_GATEWAY_MODE está em sandbox. Não movimenta dinheiro real.')

        self.stdout.write(self.style.MIGRATE_HEADING('+258 GUEST PRODUCTION CHECK'))
        self.stdout.write(f'Versão: {getattr(settings, "GUEST258_VERSION", "unknown")}')
        self.stdout.write(f'Ambiente: {getattr(settings, "GUEST258_ENVIRONMENT", "unknown")}')
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'Database engine: {engine}')
        self.stdout.write(f'Storage: {storage_backend}')
        self.stdout.write('')

        if errors:
            self.stdout.write(self.style.ERROR('ERROS CRÍTICOS:'))
            for item in errors:
                self.stdout.write(self.style.ERROR(f' - {item}'))
        else:
            self.stdout.write(self.style.SUCCESS('Sem erros críticos.'))

        if warnings:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('AVISOS:'))
            for item in warnings:
                self.stdout.write(self.style.WARNING(f' - {item}'))
        else:
            self.stdout.write(self.style.SUCCESS('Sem avisos relevantes.'))

        if errors or (strict and warnings):
            raise CommandError('A verificação de produção encontrou pontos a corrigir.')
