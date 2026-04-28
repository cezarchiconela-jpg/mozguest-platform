from urllib.parse import quote
from django.conf import settings
from django.core.mail import send_mail


def send_system_email(to_email, subject, message):
    """
    Envia e-mail simples do sistema.
    Em desenvolvimento, aparece no terminal porque usamos console backend.
    """
    if not to_email:
        return False

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'MozGuest <no-reply@mozguest.co.mz>'),
            recipient_list=[to_email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


def build_whatsapp_url(phone, message):
    """
    Gera link WhatsApp com mensagem formatada.
    Exemplo:
    https://wa.me/258840000000?text=Mensagem
    """
    if not phone:
        return ''

    clean_phone = str(phone).replace('+', '').replace(' ', '').replace('-', '')

    if clean_phone.startswith('0'):
        clean_phone = '258' + clean_phone[1:]

    encoded_message = quote(message)

    return f'https://wa.me/{clean_phone}?text={encoded_message}'


def booking_whatsapp_message(booking):
    return (
        f'Olá, tenho interesse/questão sobre a reserva #{booking.id} na MozGuest.%0A'
        f'Alojamento: {booking.property.name}%0A'
        f'Quarto/Unidade: {booking.room.name}%0A'
        f'Cliente: {booking.customer_name}%0A'
        f'Data de entrada: {booking.checkin_date}'
    )
