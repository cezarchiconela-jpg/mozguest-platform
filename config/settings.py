import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

GUEST258_VERSION = os.environ.get('GUEST258_VERSION', '2.4.1')
PLATFORM_DISPLAY_NAME = os.environ.get('PLATFORM_DISPLAY_NAME', '+258 Guest')
PLATFORM_PUBLIC_DOMAIN = os.environ.get('PLATFORM_PUBLIC_DOMAIN', '258guest.co.mz')
PLATFORM_SLOGAN = os.environ.get('PLATFORM_SLOGAN', 'Reserve estadias com confiança em Moçambique.')
GUEST258_ENVIRONMENT = os.environ.get('GUEST258_ENVIRONMENT', 'local' if os.environ.get('DJANGO_DEBUG', '').lower() in {'1','true','yes','on'} else 'production')

# Carrega variáveis de ambiente do ficheiro .env quando existir.
# Isto facilita o teste local no Windows/PowerShell e não prejudica o Render,
# porque as variáveis configuradas no servidor continuam a ter prioridade.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ===============================
# CORE SETTINGS - +258 GUEST
# ===============================

DEBUG = env_bool('DJANGO_DEBUG', env_bool('DEBUG', False))

SECRET_KEY = (
    os.environ.get('DJANGO_SECRET_KEY')
    or os.environ.get('SECRET_KEY')
)

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'guest258-local-dev-key-only'
    else:
        raise ImproperlyConfigured(
            'DJANGO_SECRET_KEY/SECRET_KEY deve estar definido quando DEBUG=False.'
        )


# ===============================
# HOSTS / CSRF - RENDER READY
# ===============================

_default_hosts = '127.0.0.1,localhost' if DEBUG else ''
_allowed_hosts = (
    os.environ.get('DJANGO_ALLOWED_HOSTS')
    or os.environ.get('ALLOWED_HOSTS')
    or _default_hosts
)

ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',') if host.strip()]

# Permite o host usado pelo Django Test Client durante validações locais.
if DEBUG and 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        'DJANGO_ALLOWED_HOSTS/ALLOWED_HOSTS deve estar definido quando DEBUG=False.'
    )

_csrf_trusted_origins = (
    os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS')
    or os.environ.get('CSRF_TRUSTED_ORIGINS')
    or ''
)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in _csrf_trusted_origins.split(',')
    if origin.strip()
]

# Ajuda em produção: se o programador só definir ALLOWED_HOSTS, criamos origens HTTPS.
if not DEBUG and not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS if '*' not in host]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'properties',
    'bookings',
    'reviews',
    'dashboard',
    'support',
    'pages',
    'messaging',
    'payments',
    'monetization',
    'communications.apps.CommunicationsConfig',
    'notifications.apps.NotificationsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    try:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
                ssl_require=env_bool('DB_SSL_REQUIRE', False)
            )
        }
    except ImportError as exc:
        raise ImportError('Instale dj-database-url para usar DATABASE_URL em produção.') from exc
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ===============================
# PASSWORD POLICY - UX FRIENDLY
# ===============================
# A +258 Guest deve facilitar o cadastro de clientes/proprietários.
# Por defeito aceitamos palavras-passe simples com mínimo de 4 caracteres.
# Se quiser endurecer a regra no futuro, defina GUEST258_SIMPLE_PASSWORDS=False.
if env_bool('GUEST258_SIMPLE_PASSWORDS', True):
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {'min_length': 4},
        },
    ]
else:
    AUTH_PASSWORD_VALIDATORS = [
        {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
        {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
        {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
        {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    ]

LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Africa/Maputo'
USE_I18N = True
USE_TZ = True

STATIC_URL = os.environ.get('DJANGO_STATIC_URL', '/static/')
STATIC_ROOT = Path(os.environ.get('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles'))
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = os.environ.get('DJANGO_MEDIA_URL', '/media/')
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', BASE_DIR / 'media'))
GUEST258_STORAGE_BACKEND = os.environ.get('GUEST258_STORAGE_BACKEND', 'local').strip().lower()
DJANGO_SERVE_MEDIA = env_bool('DJANGO_SERVE_MEDIA', DEBUG and GUEST258_STORAGE_BACKEND == 'local')

# Django 6 usa STORAGES. Mantemos static files com WhiteNoise e deixamos os uploads
# preparados para ficheiro local, disco persistente ou armazenamento S3 compatível.
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': str(MEDIA_ROOT),
            'base_url': MEDIA_URL,
        },
    },
}

if GUEST258_STORAGE_BACKEND in {'s3', 's3_compatible'}:
    # Exige django-storages e boto3 no ambiente de produção. Pode ser usado com AWS S3,
    # Cloudflare R2, Wasabi, Backblaze B2 ou serviços compatíveis com endpoint S3.
    INSTALLED_APPS.append('storages')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', '') or None
    AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', '') or None
    AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN', '') or None
    AWS_QUERYSTRING_AUTH = env_bool('AWS_QUERYSTRING_AUTH', False)
    AWS_DEFAULT_ACL = os.environ.get('AWS_DEFAULT_ACL', 'private')
    AWS_S3_FILE_OVERWRITE = env_bool('AWS_S3_FILE_OVERWRITE', False)
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': os.environ.get('AWS_S3_CACHE_CONTROL', 'max-age=86400')}
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage'}
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    DJANGO_SERVE_MEDIA = False
else:
    AWS_ACCESS_KEY_ID = ''
    AWS_SECRET_ACCESS_KEY = ''
    AWS_STORAGE_BUCKET_NAME = ''
    AWS_S3_ENDPOINT_URL = ''
    AWS_S3_CUSTOM_DOMAIN = ''

# Limites defensivos de upload. As validações detalhadas continuam nos formulários,
# mas estes limites evitam uploads excessivos antes de chegarem à aplicação.
GUEST258_MAX_UPLOAD_MB = int(os.environ.get('GUEST258_MAX_UPLOAD_MB', '8'))
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', str(GUEST258_MAX_UPLOAD_MB * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', str(GUEST258_MAX_UPLOAD_MB * 1024 * 1024)))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
]

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '+258 Guest <no-reply@258guest.co.mz>')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# ===============================
# COMMUNICATION / SUPPORT - +258 GUEST
# ===============================

GUEST258_SUPPORT_WHATSAPP = os.environ.get('GUEST258_SUPPORT_WHATSAPP', '')
GUEST258_SUPPORT_EMAILS = [
    email.strip()
    for email in os.environ.get('GUEST258_SUPPORT_EMAILS', '').split(',')
    if email.strip()
]
GUEST258_PUBLIC_BASE_URL = os.environ.get('GUEST258_PUBLIC_BASE_URL', '')
GUEST258_EMAIL_NOTIFICATIONS_ENABLED = env_bool('GUEST258_EMAIL_NOTIFICATIONS_ENABLED', True)


# ===============================
# PAYMENT INSTRUCTIONS - +258 GUEST
# ===============================

GUEST258_MPESA_NUMBER = os.environ.get('GUEST258_MPESA_NUMBER', '')
GUEST258_EMOLA_NUMBER = os.environ.get('GUEST258_EMOLA_NUMBER', '')
GUEST258_BANK_DETAILS = os.environ.get('GUEST258_BANK_DETAILS', '')
GUEST258_PAYMENT_NOTE = os.environ.get(
    'GUEST258_PAYMENT_NOTE',
    'Use a referência da reserva no pagamento e envie o comprovativo em imagem legível.'
)

SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', not DEBUG)
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0' if DEBUG else '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', not DEBUG)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = os.environ.get('SECURE_REFERRER_POLICY', 'same-origin')
X_FRAME_OPTIONS = 'DENY'

# Administradores técnicos para alertas internos por e-mail. Exemplo:
# DJANGO_ADMINS=Operacao +258 Guest:ops@258guest.co.mz,Suporte:suporte@258guest.co.mz
def env_admins(name: str):
    items = []
    for raw in os.environ.get(name, '').split(','):
        raw = raw.strip()
        if not raw:
            continue
        if ':' in raw:
            label, email = raw.split(':', 1)
            items.append((label.strip(), email.strip()))
        else:
            items.append(('+258 Guest Admin', raw))
    return items

ADMINS = env_admins('DJANGO_ADMINS')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

LOG_DIR = Path(os.environ.get('DJANGO_LOG_DIR', BASE_DIR / 'logs'))
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}:{lineno} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'guest258.log'),
            'maxBytes': int(os.environ.get('DJANGO_LOG_MAX_BYTES', '1048576')),
            'backupCount': int(os.environ.get('DJANGO_LOG_BACKUP_COUNT', '5')),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'] if LOG_DIR.exists() else ['console'],
        'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'file'] if LOG_DIR.exists() else ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'guest258': {
            'handlers': ['console', 'file'] if LOG_DIR.exists() else ['console'],
            'level': os.environ.get('GUEST258_LOG_LEVEL', os.environ.get('DJANGO_LOG_LEVEL', 'INFO')),
            'propagate': False,
        },
    },
}

# ===============================
# PAYMENT GATEWAY - +258 GUEST v1.9
# ===============================
# sandbox: permite testar sem dinheiro real; live: exige credenciais/endpoints oficiais.
GUEST258_PAYMENT_GATEWAY_MODE = os.environ.get('GUEST258_PAYMENT_GATEWAY_MODE', 'sandbox').strip().lower()
GUEST258_GATEWAY_CALLBACK_TOKEN = os.environ.get('GUEST258_GATEWAY_CALLBACK_TOKEN', '')

# Configuração genérica M-Pesa. Ajustar payload em payments/gateways.py quando houver documentação oficial.
MPESA_INITIATE_URL = os.environ.get('MPESA_INITIATE_URL', '')
MPESA_QUERY_URL = os.environ.get('MPESA_QUERY_URL', '')
MPESA_TOKEN = os.environ.get('MPESA_TOKEN', '')
MPESA_API_KEY = os.environ.get('MPESA_API_KEY', '')
MPESA_SERVICE_PROVIDER_CODE = os.environ.get('MPESA_SERVICE_PROVIDER_CODE', '')

# Configuração genérica e-Mola/Agregador. Ajustar payload em payments/gateways.py quando houver documentação oficial.
EMOLA_INITIATE_URL = os.environ.get('EMOLA_INITIATE_URL', '')
EMOLA_QUERY_URL = os.environ.get('EMOLA_QUERY_URL', '')
EMOLA_TOKEN = os.environ.get('EMOLA_TOKEN', '')
EMOLA_API_KEY = os.environ.get('EMOLA_API_KEY', '')
EMOLA_SERVICE_PROVIDER_CODE = os.environ.get('EMOLA_SERVICE_PROVIDER_CODE', '')
