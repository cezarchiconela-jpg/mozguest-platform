from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification
from .services import send_system_email


@receiver(post_save, sender=Notification)
def notification_email_sender(sender, instance, created, **kwargs):
    """
    Sempre que uma nova notificação é criada, envia também e-mail ao destinatário,
    se o utilizador tiver e-mail cadastrado.
    """
    if not created:
        return

    recipient = instance.recipient

    if not recipient or not recipient.email:
        return

    subject = f'MozGuest - {instance.title}'

    message = f"""
Olá {recipient.get_full_name() or recipient.username},

{instance.message}

Pode aceder à plataforma MozGuest para ver mais detalhes.

Link interno:
{instance.link or '/notificacoes/'}

Obrigado,
Equipa MozGuest
"""

    send_system_email(
        to_email=recipient.email,
        subject=subject,
        message=message
    )
