from .models import AuditLog


def _request_ip(request):
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit(action, actor=None, target=None, message='', metadata=None, request=None):
    """Cria um registo de auditoria sem interromper o fluxo principal caso falhe."""
    try:
        target_model = ''
        target_id = ''
        target_repr = ''
        if target is not None:
            target_model = target.__class__.__name__
            target_id = str(getattr(target, 'pk', '') or '')
            target_repr = str(target)[:255]

        if request is not None:
            actor = actor or getattr(request, 'user', None)

        if actor is not None and not getattr(actor, 'is_authenticated', False):
            actor = None

        return AuditLog.objects.create(
            actor=actor,
            action=action or 'other',
            target_model=target_model,
            target_id=target_id,
            target_repr=target_repr,
            message=message or '',
            metadata=metadata or {},
            ip_address=_request_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''),
        )
    except Exception:
        return None
