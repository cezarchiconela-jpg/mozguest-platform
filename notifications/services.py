from django.contrib.auth.models import User
from communications.services import send_system_email
from .models import Notification


def create_notification(recipient, title, message, notification_type='system', link='', send_email=False):
    if not recipient:
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )

    if send_email and getattr(recipient, 'email', ''):
        send_system_email(recipient.email, f'+258 Guest - {title}', message)

    return notification


def notify_staff(title, message, notification_type='system', link='', send_email=False):
    staff_users = User.objects.filter(is_staff=True, is_active=True)

    for user in staff_users:
        create_notification(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            send_email=send_email,
        )
