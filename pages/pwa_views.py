from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404


def service_worker(request):
    service_worker_path = Path(settings.BASE_DIR) / 'static' / 'service-worker.js'
    if not service_worker_path.exists():
        raise Http404('Service worker não encontrado.')

    response = FileResponse(open(service_worker_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response
