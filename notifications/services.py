from django.contrib.auth.models import User
from .models import Notification


def create_notification(recipient, title, message, notification_type='system', link=''):
    if not recipient:
        return None

    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )


def notify_staff(title, message, notification_type='system', link=''):
    staff_users = User.objects.filter(is_staff=True, is_active=True)

    for user in staff_users:
        create_notification(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
