from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.db.models import Sum, Q
from django.shortcuts import redirect, render, get_object_or_404

from properties.models import Property, Room, PropertyPhoto
from accounts.models import OwnerProfile, ClientProfile
from bookings.models import Booking
from reviews.models import Review
from payments.models import Payment, OwnerPayout
from notifications.services import create_notification
from communications.services import send_system_email
from payments.services import ensure_owner_payout_for_payment
from dashboard.services import log_audit


def home(request):
    approved_properties = Property.objects.filter(status='approved')

    featured_properties = approved_properties.filter(
        is_featured=True
    ).prefetch_related('photos', 'rooms')[:6]

    latest_properties = approved_properties.prefetch_related('photos', 'rooms')[:8]

    context = {
        'featured_properties': featured_properties,
        'latest_properties': latest_properties,
        'public_stats_total': approved_properties.count(),
        'public_stats_cities': approved_properties.exclude(city='').values('city').distinct().count(),
        'public_stats_verified': approved_properties.filter(is_verified=True).count(),
    }

    return render(request, 'public/home.html', context)


@login_required
def owner_dashboard(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder ao painel de proprietário.')
        return redirect('home')

    my_properties = Property.objects.filter(owner=request.user).prefetch_related('rooms', 'photos')
    my_rooms = Room.objects.filter(property__owner=request.user)
    my_bookings = Booking.objects.filter(property__owner=request.user)
    my_photos = PropertyPhoto.objects.filter(property__owner=request.user)

    total_properties = my_properties.count()
    approved_properties = my_properties.filter(status='approved').count()
    pending_properties = my_properties.filter(status='pending').count()
    total_rooms = my_rooms.count()
    total_photos = my_photos.count()
    has_priced_room = my_rooms.filter(
        Q(price_hour__isnull=False) |
        Q(price_day__isnull=False) |
        Q(price_night__isnull=False) |
        Q(price_month__isnull=False)
    ).exists()

    setup_checks = [
        total_properties > 0,
        total_rooms > 0,
        total_photos > 0,
        has_priced_room,
        approved_properties > 0,
    ]
    setup_completed = sum(1 for item in setup_checks if item)
    setup_progress = int((setup_completed / len(setup_checks)) * 100)

    context = {
        'total_properties': total_properties,
        'approved_properties': approved_properties,
        'pending_properties': pending_properties,
        'total_rooms': total_rooms,
        'total_photos': total_photos,
        'has_priced_room': has_priced_room,
        'setup_completed': setup_completed,
        'setup_progress': setup_progress,
        'setup_is_complete': setup_completed == len(setup_checks),
        'total_bookings': my_bookings.count(),
        'pending_bookings': my_bookings.filter(status='pending').count(),
        'accepted_bookings': my_bookings.filter(status='accepted').count(),
        'completed_bookings': my_bookings.filter(status='completed').count(),
        'recent_properties': my_properties[:5],
        'recent_bookings': my_bookings[:5],
    }

    return render(request, 'owner/dashboard.html', context)


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_staff_user)
def guest258_admin_dashboard(request):
    properties = Property.objects.select_related('owner').prefetch_related('rooms', 'photos')
    bookings = Booking.objects.select_related('property', 'room', 'client').all()
    reviews = Review.objects.select_related('property').all()
    payments = Payment.objects.select_related('booking', 'booking__property', 'booking__property__owner').all()
    payouts = OwnerPayout.objects.select_related('owner', 'payment', 'payment__booking').all()

    pending_properties = properties.filter(status='pending').count()
    pending_bookings = bookings.filter(status='pending').count()
    submitted_payments = payments.filter(status='submitted').count()
    pending_reviews = reviews.filter(status='pending').count()
    pending_payouts = payouts.filter(status='pending').count()

    context = {
        'total_users': User.objects.count(),
        'total_owners': OwnerProfile.objects.count(),
        'total_clients': ClientProfile.objects.count(),

        'total_properties': properties.count(),
        'pending_properties': pending_properties,
        'approved_properties': properties.filter(status='approved').count(),
        'rejected_properties': properties.filter(status='rejected').count(),
        'suspended_properties': properties.filter(status='suspended').count(),
        'featured_properties': properties.filter(is_featured=True).count(),

        'total_rooms': Room.objects.count(),

        'total_bookings': bookings.count(),
        'pending_bookings': pending_bookings,
        'accepted_bookings': bookings.filter(status='accepted').count(),
        'completed_bookings': bookings.filter(status='completed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
        'rejected_bookings': bookings.filter(status='rejected').count(),

        'pending_reviews': pending_reviews,
        'approved_reviews': reviews.filter(status='approved').count(),

        'submitted_payments': submitted_payments,
        'confirmed_payments': payments.filter(status='confirmed').count(),
        'rejected_payments': payments.filter(status='rejected').count(),

        'pending_payouts': pending_payouts,
        'scheduled_payouts': payouts.filter(status='scheduled').count(),
        'paid_payouts': payouts.filter(status='paid').count(),
        'held_payouts': payouts.filter(status='held').count(),

        'total_paid': payments.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0,
        'total_commission': payments.filter(status='confirmed').aggregate(total=Sum('platform_commission_amount'))['total'] or 0,
        'total_owner_amount': payments.filter(status='confirmed').aggregate(total=Sum('owner_amount'))['total'] or 0,
        'total_payout_pending': payouts.filter(status__in=['pending', 'scheduled']).aggregate(total=Sum('payout_amount'))['total'] or 0,
        'total_payout_paid': payouts.filter(status='paid').aggregate(total=Sum('payout_amount'))['total'] or 0,

        'urgent_action_count': pending_properties + pending_bookings + submitted_payments + pending_reviews + pending_payouts,
        'recent_properties': properties.order_by('-created_at')[:8],
        'recent_bookings': bookings.order_by('-created_at')[:8],
        'recent_payments': payments.order_by('-created_at')[:8],
        'properties_without_photos': properties.filter(photos__isnull=True).distinct()[:5],
        'properties_without_rooms': properties.filter(rooms__isnull=True).distinct()[:5],
    }

    return render(request, 'admin_panel/dashboard.html', context)


@user_passes_test(is_staff_user)
def admin_property_approval(request):
    status = request.GET.get('status', 'pending').strip()
    query = request.GET.get('q', '').strip()
    valid_statuses = {choice[0] for choice in Property.STATUS_CHOICES}

    properties = Property.objects.select_related('owner').prefetch_related('rooms', 'photos').order_by('-created_at')

    if status in valid_statuses:
        properties = properties.filter(status=status)
    elif status == 'all':
        status = 'all'
    else:
        status = 'pending'
        properties = properties.filter(status='pending')

    if query:
        properties = properties.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(neighbourhood__icontains=query) |
            Q(owner__username__icontains=query) |
            Q(owner__email__icontains=query)
        )

    return render(request, 'admin_panel/property_approval.html', {
        'properties': properties,
        'status': status,
        'query': query,
        'status_choices': Property.STATUS_CHOICES,
        'pending_count': Property.objects.filter(status='pending').count(),
        'approved_count': Property.objects.filter(status='approved').count(),
        'rejected_count': Property.objects.filter(status='rejected').count(),
        'suspended_count': Property.objects.filter(status='suspended').count(),
    })


@user_passes_test(is_staff_user)
def admin_booking_list(request):
    status = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()
    valid_statuses = {choice[0] for choice in Booking.STATUS_CHOICES}

    base_bookings = Booking.objects.select_related(
        'property',
        'room',
        'client',
        'payment',
    ).order_by('-created_at')

    bookings = base_bookings

    if status in valid_statuses:
        bookings = bookings.filter(status=status)
    else:
        status = ''

    if query:
        bookings = bookings.filter(
            Q(customer_name__icontains=query) |
            Q(customer_phone__icontains=query) |
            Q(customer_email__icontains=query) |
            Q(property__name__icontains=query) |
            Q(property__city__icontains=query) |
            Q(room__name__icontains=query)
        )

    booking_items = list(bookings[:200])
    for booking in booking_items:
        try:
            booking.payment_obj = booking.payment
        except Exception:
            booking.payment_obj = None

    return render(request, 'admin_panel/booking_list.html', {
        'bookings': booking_items,
        'status': status,
        'query': query,
        'total_count': Booking.objects.count(),
        'pending_count': Booking.objects.filter(status='pending').count(),
        'accepted_count': Booking.objects.filter(status='accepted').count(),
        'completed_count': Booking.objects.filter(status='completed').count(),
        'cancelled_count': Booking.objects.filter(status='cancelled').count(),
        'rejected_count': Booking.objects.filter(status='rejected').count(),
        'limited_results': bookings.count() > 200,
    })


@user_passes_test(is_staff_user)
@require_POST
def admin_approve_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    property_obj.status = 'approved'
    property_obj.is_verified = True
    property_obj.save()

    create_notification(
        property_obj.owner,
        'Propriedade aprovada',
        f'A propriedade {property_obj.name} foi aprovada e já pode aparecer na +258 Guest.',
        notification_type='property',
        link=f'/properties/{property_obj.id}/'
    )
    send_system_email(
        property_obj.owner.email,
        '+258 Guest - propriedade aprovada',
        f'A propriedade {property_obj.name} foi aprovada e já pode aparecer na plataforma +258 Guest.'
    )

    log_audit('property_approved', request=request, target=property_obj, message='Propriedade aprovada e verificada pela administração.')
    messages.success(request, 'Propriedade aprovada e verificada com sucesso.')
    return redirect('guest258_admin_properties')


@user_passes_test(is_staff_user)
@require_POST
def admin_reject_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    property_obj.status = 'rejected'
    property_obj.save()

    create_notification(
        property_obj.owner,
        'Propriedade rejeitada',
        f'A propriedade {property_obj.name} foi rejeitada. Reveja os dados e submeta novamente, se necessário.',
        notification_type='property',
        link='/proprietario/propriedades/'
    )

    log_audit('property_rejected', request=request, target=property_obj, message='Propriedade rejeitada pela administração.')
    messages.success(request, 'Propriedade rejeitada.')
    return redirect('guest258_admin_properties')


@user_passes_test(is_staff_user)
@require_POST
def admin_toggle_featured_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    property_obj.is_featured = not property_obj.is_featured
    property_obj.save(update_fields=['is_featured', 'updated_at'])

    if property_obj.is_featured:
        log_audit('property_featured', request=request, target=property_obj, message='Propriedade colocada em destaque.')
        messages.success(request, f'{property_obj.name} foi colocado em destaque.')
    else:
        log_audit('property_featured', request=request, target=property_obj, message='Propriedade removida dos destaques.')
        messages.success(request, f'{property_obj.name} foi removido dos destaques.')

    next_url = request.POST.get('next') or 'guest258_admin_properties'
    if isinstance(next_url, str) and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('guest258_admin_properties')


@user_passes_test(is_staff_user)
def admin_review_approval(request):
    reviews = Review.objects.filter(status='pending').order_by('-created_at')

    return render(request, 'admin_panel/review_approval.html', {
        'reviews': reviews
    })


@user_passes_test(is_staff_user)
@require_POST
def admin_approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.status = 'approved'
    review.save()

    log_audit('review_approved', request=request, target=review, message='Avaliação aprovada pela administração.')
    messages.success(request, 'Avaliação aprovada com sucesso.')
    return redirect('guest258_admin_reviews')


@user_passes_test(is_staff_user)
@require_POST
def admin_reject_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.status = 'rejected'
    review.save()

    log_audit('review_rejected', request=request, target=review, message='Avaliação rejeitada pela administração.')
    messages.success(request, 'Avaliação rejeitada.')
    return redirect('guest258_admin_reviews')


@user_passes_test(is_staff_user)
def admin_payment_approval(request):
    status = request.GET.get('status', 'submitted').strip()
    query = request.GET.get('q', '').strip()
    valid_statuses = {choice[0] for choice in Payment.STATUS_CHOICES}

    payments = Payment.objects.select_related(
        'booking',
        'booking__property',
        'booking__property__owner',
        'client',
    ).order_by('-created_at')

    if status in valid_statuses:
        payments = payments.filter(status=status)
    elif status == 'all':
        status = 'all'
    else:
        status = 'submitted'
        payments = payments.filter(status='submitted')

    if query:
        payments = payments.filter(
            Q(transaction_reference__icontains=query) |
            Q(booking__customer_name__icontains=query) |
            Q(booking__customer_phone__icontains=query) |
            Q(booking__property__name__icontains=query) |
            Q(booking__property__owner__username__icontains=query)
        )

    return render(request, 'admin_panel/payment_approval.html', {
        'payments': payments,
        'status': status,
        'query': query,
        'pending_count': Payment.objects.filter(status='pending').count(),
        'submitted_count': Payment.objects.filter(status='submitted').count(),
        'confirmed_count': Payment.objects.filter(status='confirmed').count(),
        'rejected_count': Payment.objects.filter(status='rejected').count(),
    })


@user_passes_test(is_staff_user)
@require_POST
def admin_confirm_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'confirmed'
    payment.save()
    ensure_owner_payout_for_payment(payment)

    if payment.client:
        create_notification(
            payment.client,
            'Pagamento confirmado',
            f'O pagamento da reserva #{payment.booking.id} foi confirmado pela +258 Guest.',
            notification_type='payment',
            link='/reservas/cliente/minhas-reservas/'
        )
    create_notification(
        payment.booking.property.owner,
        'Pagamento confirmado',
        f'A +258 Guest confirmou o pagamento da reserva #{payment.booking.id}.',
        notification_type='payment',
        link='/pagamentos/proprietario/financeiro/'
    )

    log_audit('payment_confirmed', request=request, target=payment, message='Pagamento confirmado pela administração.', metadata={'amount': str(payment.amount), 'booking_id': payment.booking_id})
    messages.success(request, 'Pagamento confirmado com sucesso.')
    return redirect('guest258_admin_payments')


@user_passes_test(is_staff_user)
@require_POST
def admin_reject_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'rejected'
    payment.save()

    if payment.client:
        create_notification(
            payment.client,
            'Pagamento rejeitado',
            f'O comprovativo da reserva #{payment.booking.id} foi rejeitado. Verifique a referência e envie novamente.',
            notification_type='payment',
            link=f'/pagamentos/reserva/{payment.booking.id}/pagar/'
        )

    log_audit('payment_rejected', request=request, target=payment, message='Pagamento rejeitado pela administração.', metadata={'booking_id': payment.booking_id})
    messages.success(request, 'Pagamento rejeitado.')
    return redirect('guest258_admin_payments')


@user_passes_test(is_staff_user)
def admin_audit_log_list(request):
    from dashboard.models import AuditLog

    action = request.GET.get('action', '').strip()
    query = request.GET.get('q', '').strip()

    logs = AuditLog.objects.select_related('actor').order_by('-created_at')
    if action:
        logs = logs.filter(action=action)
    if query:
        logs = logs.filter(
            Q(actor__username__icontains=query) |
            Q(actor__email__icontains=query) |
            Q(target_repr__icontains=query) |
            Q(message__icontains=query) |
            Q(target_id__icontains=query)
        )

    return render(request, 'admin_panel/audit_log_list.html', {
        'logs': logs[:300],
        'action': action,
        'query': query,
        'action_choices': AuditLog.ACTION_CHOICES,
        'total_count': AuditLog.objects.count(),
    })
