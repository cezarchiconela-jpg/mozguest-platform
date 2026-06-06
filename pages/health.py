from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@require_GET
@never_cache
def healthz(request):
    """Health check simples para Render/load balancer.

    Não toca na base de dados. Serve para confirmar que o processo Django está vivo.
    """
    return JsonResponse({
        'status': 'ok',
        'service': '+258 Guest',
        'version': getattr(settings, 'GUEST258_VERSION', 'unknown'),
        'environment': getattr(settings, 'GUEST258_ENVIRONMENT', 'unknown'),
    })


@require_GET
@never_cache
def readyz(request):
    """Readiness check com teste de base de dados.

    Útil antes de abrir tráfego real, depois de migrar a base de dados.
    """
    checks = {
        'django': 'ok',
        'database': 'unknown',
        'storage': getattr(settings, 'GUEST258_STORAGE_BACKEND', 'local'),
    }
    status_code = 200
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        checks['database'] = 'ok'
    except Exception as exc:  # pragma: no cover - depende do ambiente
        checks['database'] = f'error: {exc.__class__.__name__}'
        status_code = 503

    return JsonResponse({
        'status': 'ok' if status_code == 200 else 'not_ready',
        'service': '+258 Guest',
        'version': getattr(settings, 'GUEST258_VERSION', 'unknown'),
        'checks': checks,
    }, status=status_code)
