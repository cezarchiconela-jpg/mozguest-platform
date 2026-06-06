from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notification_list(request):
    status = request.GET.get('estado', '').strip()
    notification_type = request.GET.get('tipo', '').strip()
    q = request.GET.get('q', '').strip()

    notifications = Notification.objects.filter(recipient=request.user)

    if status == 'nao_lidas':
        notifications = notifications.filter(is_read=False)
    elif status == 'lidas':
        notifications = notifications.filter(is_read=True)
    else:
        status = ''

    valid_types = {choice[0] for choice in Notification.NOTIFICATION_TYPES}
    if notification_type in valid_types:
        notifications = notifications.filter(notification_type=notification_type)
    else:
        notification_type = ''

    if q:
        notifications = notifications.filter(
            Q(title__icontains=q) | Q(message__icontains=q) | Q(link__icontains=q)
        )

    all_notifications = Notification.objects.filter(recipient=request.user)
    unread_qs = all_notifications.filter(is_read=False)
    urgent_unread_count = unread_qs.filter(notification_type__in=['booking', 'payment']).count()

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'status': status,
        'notification_type': notification_type,
        'q': q,
        'type_choices': Notification.NOTIFICATION_TYPES,
        'total_count': all_notifications.count(),
        'unread_count_page': unread_qs.count(),
        'booking_count': all_notifications.filter(notification_type='booking').count(),
        'payment_count': all_notifications.filter(notification_type='payment').count(),
        'property_count': all_notifications.filter(notification_type='property').count(),
        'review_count': all_notifications.filter(notification_type='review').count(),
        'system_count': all_notifications.filter(notification_type='system').count(),
        'urgent_unread_count': urgent_unread_count,
        'latest_unread': unread_qs[:5],
    })


@login_required
def notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if notification.link:
        return redirect(notification.link)

    return redirect('notification_list')


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect('notification_list')
