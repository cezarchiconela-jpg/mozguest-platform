import re
from urllib.parse import quote
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def communication_enabled():
    return getattr(settings, 'GUEST258_EMAIL_NOTIFICATIONS_ENABLED', True)


def get_user_display_name(user):
    if not user:
        return 'Utilizador +258 Guest'
    full_name = getattr(user, 'get_full_name', lambda: '')()
    return full_name or getattr(user, 'username', '') or getattr(user, 'email', '') or 'Utilizador +258 Guest'


def build_absolute_url(path_or_url='', request=None):
    """Gera URL absoluta quando existir domínio público ou request."""
    path_or_url = str(path_or_url or '')
    if path_or_url.startswith(('http://', 'https://')):
        return path_or_url

    if request is not None:
        try:
            return request.build_absolute_uri(path_or_url or '/')
        except Exception:
            pass

    base_url = getattr(settings, 'GUEST258_PUBLIC_BASE_URL', '').strip().rstrip('/')
    if not base_url:
        return path_or_url

    if not path_or_url.startswith('/'):
        path_or_url = '/' + path_or_url
    return base_url + path_or_url


def send_system_email(to_email, subject, message):
    """
    Envia e-mail simples do sistema.
    Em desenvolvimento, aparece no terminal quando usamos console backend.
    """
    if not communication_enabled() or not to_email:
        return False

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', '+258 Guest <no-reply@258guest.co.mz>'),
            recipient_list=[to_email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


def send_system_email_many(to_emails, subject, message):
    sent = 0
    for email in to_emails or []:
        if send_system_email(email, subject, message):
            sent += 1
    return sent


def send_support_team_email(subject, message):
    """Envia aviso para os e-mails operacionais configurados em GUEST258_SUPPORT_EMAILS."""
    recipients = getattr(settings, 'GUEST258_SUPPORT_EMAILS', [])
    return send_system_email_many(recipients, subject, message)


def normalize_mozambique_phone(phone):
    """
    Normaliza números para links WhatsApp.
    Aceita formatos como 84xxxxxxx, 084xxxxxxx, +25884xxxxxxx ou 25884xxxxxxx.
    """
    if not phone:
        return ''

    clean_phone = re.sub(r'\D+', '', str(phone))

    if clean_phone.startswith('00258'):
        clean_phone = clean_phone[2:]

    if clean_phone.startswith('0') and len(clean_phone) >= 9:
        clean_phone = '258' + clean_phone[1:]
    elif len(clean_phone) == 9 and clean_phone[:2] in {'82', '83', '84', '85', '86', '87'}:
        clean_phone = '258' + clean_phone

    return clean_phone


def build_whatsapp_url(phone, message):
    """
    Gera link WhatsApp com mensagem formatada.
    Exemplo: https://wa.me/258840000000?text=Mensagem
    """
    clean_phone = normalize_mozambique_phone(phone)
    if not clean_phone:
        return ''

    encoded_message = quote(str(message or ''))

    return f'https://wa.me/{clean_phone}?text={encoded_message}'


def format_money(value):
    try:
        return f'{float(value):,.2f} MT'.replace(',', ' ')
    except Exception:
        return f'{value or 0} MT'


def booking_summary_lines(booking):
    return [
        f'Reserva: #{booking.id}',
        f'Alojamento: {booking.property.name}',
        f'Quarto/Unidade: {booking.room.name}',
        f'Cliente: {booking.customer_name}',
        f'Telefone: {booking.customer_phone}',
        f'Entrada: {booking.checkin_date} {booking.checkin_time or ""}'.strip(),
        f'Saída: {booking.checkout_date or "A confirmar"} {booking.checkout_time or ""}'.strip(),
        f'Pessoas: {booking.number_of_guests}',
        f'Valor estimado: {format_money(booking.estimated_amount)}',
        f'Estado: {booking.get_status_display()}',
    ]


def booking_whatsapp_message(booking):
    return 'Olá, estou a contactar pela +258 Guest.\n\n' + '\n'.join(booking_summary_lines(booking))


def booking_email_message(booking, intro='', action_link=''):
    lines = []
    if intro:
        lines.append(intro)
        lines.append('')
    lines.extend(booking_summary_lines(booking))
    if action_link:
        lines.append('')
        lines.append(f'Abrir no +258 Guest: {action_link}')
    lines.append('')
    lines.append('Nota: mantenha a comunicação principal dentro da +258 Guest para segurança e histórico da reserva.')
    return '\n'.join(lines)


def support_email_message(ticket, intro='', action_link=''):
    lines = []
    if intro:
        lines.append(intro)
        lines.append('')
    lines.extend([
        f'Pedido de suporte: #{ticket.id}',
        f'Assunto: {ticket.subject}',
        f'Categoria: {ticket.get_category_display()}',
        f'Prioridade: {ticket.get_priority_display()}',
        f'Estado: {ticket.get_status_display()}',
        f'Criado por: {get_user_display_name(ticket.created_by)}',
    ])
    if ticket.booking:
        lines.extend([
            '',
            f'Reserva relacionada: #{ticket.booking.id}',
            f'Alojamento: {ticket.booking.property.name}',
        ])
    if ticket.admin_response:
        lines.extend(['', 'Resposta da administração:', ticket.admin_response])
    if action_link:
        lines.extend(['', f'Abrir no +258 Guest: {action_link}'])
    return '\n'.join(lines)


def support_whatsapp_url(message='Olá, preciso de apoio da equipa +258 Guest.'):
    phone = getattr(settings, 'GUEST258_SUPPORT_WHATSAPP', '')
    return build_whatsapp_url(phone, message)
