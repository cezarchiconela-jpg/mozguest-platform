from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from properties.models import Property, Room
from .forms import BookingForm, AvailabilityBlockForm
from .models import Booking, AvailabilityBlock
from .services import calculate_booking_amount, booking_has_conflict, get_booking_period
from notifications.services import create_notification, notify_staff
from communications.services import send_system_email
from dashboard.services import log_audit


def user_is_owner(user):
    return user.is_authenticated and hasattr(user, 'owner_profile')


def notify_booking_user(user, title, message, link='', notification_type='booking'):
    if user:
        create_notification(user, title, message, notification_type=notification_type, link=link)
        send_system_email(getattr(user, 'email', ''), title, message)


def user_can_access_booking(user, booking):
    if not user.is_authenticated:
        return False

    if booking.client == user:
        return True

    if booking.property.owner == user:
        return True

    if user.is_staff:
        return True

    return False


def booking_create(request, room_id):
    room = get_object_or_404(Room, pk=room_id, is_available=True)
    property_obj = room.property

    if request.method == 'POST':
        form = BookingForm(request.POST, room=room)

        if form.is_valid():
            booking = form.save(commit=False)
            booking.room = room
            booking.property = property_obj

            if request.user.is_authenticated:
                booking.client = request.user

            unit_price, units_count, estimated_amount, start, end = calculate_booking_amount(
                room=room,
                booking_type=booking.booking_type,
                checkin_date=booking.checkin_date,
                checkin_time=booking.checkin_time,
                checkout_date=booking.checkout_date,
                checkout_time=booking.checkout_time
            )

            if unit_price is None:
                messages.error(request, 'Este tipo de reserva ainda não tem preço definido para esta unidade.')
                return render(request, 'bookings/booking_form.html', {
                    'form': form,
                    'room': room,
                    'property': property_obj,
                })

            if not start or not end:
                messages.error(request, 'Não foi possível calcular o período da reserva. Verifique as datas e horas.')
                return render(request, 'bookings/booking_form.html', {
                    'form': form,
                    'room': room,
                    'property': property_obj,
                })

            if booking_has_conflict(room, start, end):
                messages.error(request, 'Este quarto/unidade já tem reserva ou bloqueio neste período.')
                return render(request, 'bookings/booking_form.html', {
                    'form': form,
                    'room': room,
                    'property': property_obj,
                })

            booking.unit_price = unit_price or 0
            booking.units_count = units_count or 1
            booking.estimated_amount = estimated_amount or 0
            booking.status = 'pending'
            booking.save()

            notify_booking_user(
                property_obj.owner,
                'Novo pedido de reserva recebido',
                f'Recebeu uma nova reserva para {property_obj.name} / {room.name}. Cliente: {booking.customer_name}.',
                link='/reservas/proprietario/reservas/?status=pending',
            )
            notify_staff(
                'Nova reserva criada',
                f'Reserva #{booking.id} criada para {property_obj.name} por {booking.customer_name}.',
                notification_type='booking',
                link='/258-admin/'
            )

            messages.success(request, 'Pedido de reserva enviado com sucesso. Aguarde confirmação do proprietário.')
            return redirect('booking_success', booking_id=booking.id)
    else:
        initial = {}

        if request.user.is_authenticated:
            initial['customer_name'] = request.user.get_full_name() or request.user.username
            initial['customer_email'] = request.user.email
            client_profile = getattr(request.user, 'client_profile', None)
            if client_profile and client_profile.phone:
                initial['customer_phone'] = client_profile.phone

        form = BookingForm(initial=initial, room=room)

    return render(request, 'bookings/booking_form.html', {
        'form': form,
        'room': room,
        'property': property_obj,
    })


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    return render(request, 'bookings/booking_success.html', {
        'booking': booking
    })


@login_required
def client_booking_list(request):
    status = request.GET.get('status', '').strip()
    valid_statuses = {choice[0] for choice in Booking.STATUS_CHOICES}

    bookings = Booking.objects.filter(
        client=request.user
    ).select_related(
        'property',
        'room',
        'payment',
    ).order_by('-created_at')

    if status in valid_statuses:
        bookings = bookings.filter(status=status)
    else:
        status = ''

    booking_items = list(bookings)
    for booking in booking_items:
        try:
            booking.payment_obj = booking.payment
        except Exception:
            booking.payment_obj = None

    return render(request, 'client/booking_list.html', {
        'bookings': booking_items,
        'status': status,
        'pending_count': Booking.objects.filter(client=request.user, status='pending').count(),
        'accepted_count': Booking.objects.filter(client=request.user, status='accepted').count(),
    })


@login_required
def owner_booking_list(request):
    if not user_is_owner(request.user):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    status = request.GET.get('status', '').strip()
    valid_statuses = {choice[0] for choice in Booking.STATUS_CHOICES}

    base_bookings = Booking.objects.filter(property__owner=request.user)
    bookings = base_bookings.select_related(
        'property',
        'room',
        'client',
        'payment',
    ).order_by('-created_at')

    if status in valid_statuses:
        bookings = bookings.filter(status=status)
    else:
        status = ''

    booking_items = list(bookings)
    for booking in booking_items:
        try:
            booking.payment_obj = booking.payment
        except Exception:
            booking.payment_obj = None

    return render(request, 'owner/booking_list.html', {
        'bookings': booking_items,
        'status': status,
        'total_count': base_bookings.count(),
        'pending_count': base_bookings.filter(status='pending').count(),
        'accepted_count': base_bookings.filter(status='accepted').count(),
        'completed_count': base_bookings.filter(status='completed').count(),
    })


@login_required
@require_POST
def owner_booking_accept(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        property__owner=request.user
    )

    if booking.status != 'pending':
        messages.error(request, 'Apenas reservas pendentes podem ser aceites.')
        return redirect('owner_booking_list')

    start, end = get_booking_period(
        booking.booking_type,
        booking.checkin_date,
        booking.checkin_time,
        booking.checkout_date,
        booking.checkout_time
    )

    if booking_has_conflict(booking.room, start, end, exclude_booking_id=booking.id):
        messages.error(request, 'Não é possível aceitar esta reserva porque existe conflito de disponibilidade.')
        return redirect('owner_booking_list')

    booking.status = 'accepted'
    booking.save()
    log_audit('booking_accepted', request=request, target=booking, message='Reserva aceite pelo proprietário.')

    if booking.client:
        notify_booking_user(
            booking.client,
            'Reserva aceite pelo proprietário',
            f'A sua reserva #{booking.id} em {booking.property.name} foi aceite. Pode agora enviar o comprovativo de pagamento.',
            link='/reservas/cliente/minhas-reservas/?status=accepted',
        )

    messages.success(request, 'Reserva aceite com sucesso.')
    return redirect('owner_booking_list')


@login_required
@require_POST
def owner_booking_reject(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        property__owner=request.user
    )

    if booking.status != 'pending':
        messages.error(request, 'Apenas reservas pendentes podem ser rejeitadas.')
        return redirect('owner_booking_list')

    booking.status = 'rejected'
    booking.save()
    log_audit('booking_rejected', request=request, target=booking, message='Reserva rejeitada pelo proprietário.')

    if booking.client:
        notify_booking_user(
            booking.client,
            'Reserva rejeitada',
            f'A sua reserva #{booking.id} em {booking.property.name} foi rejeitada pelo proprietário.',
            link='/reservas/cliente/minhas-reservas/?status=rejected',
        )

    messages.success(request, 'Reserva rejeitada.')
    return redirect('owner_booking_list')


@login_required
@require_POST
def owner_booking_complete(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        property__owner=request.user
    )

    if booking.status != 'accepted':
        messages.error(request, 'Apenas reservas aceites podem ser marcadas como concluídas.')
        return redirect('owner_booking_list')

    booking.status = 'completed'
    booking.save()
    log_audit('booking_completed', request=request, target=booking, message='Reserva marcada como concluída pelo proprietário.')

    if booking.client:
        notify_booking_user(
            booking.client,
            'Reserva concluída',
            f'A reserva #{booking.id} em {booking.property.name} foi marcada como concluída.',
            link='/reservas/cliente/minhas-reservas/?status=completed',
        )

    messages.success(request, 'Reserva marcada como concluída.')
    return redirect('owner_booking_list')


@login_required
@require_POST
def client_booking_cancel(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        client=request.user
    )

    if booking.status not in ['pending', 'accepted']:
        messages.error(request, 'Esta reserva já não pode ser cancelada.')
        return redirect('client_booking_list')

    cancellation_reason = request.POST.get('cancellation_reason', '').strip()
    booking.mark_cancelled(cancelled_by='client', reason=cancellation_reason)
    log_audit('booking_cancelled', request=request, target=booking, message='Reserva cancelada pelo cliente.', metadata={'reason': cancellation_reason, 'refund_status': booking.refund_status})

    notify_booking_user(
        booking.property.owner,
        'Reserva cancelada pelo cliente',
        f'A reserva #{booking.id} para {booking.property.name} foi cancelada pelo cliente {booking.customer_name}.',
        link='/reservas/proprietario/reservas/?status=cancelled',
    )

    messages.success(request, 'Reserva cancelada com sucesso.')
    return redirect('client_booking_list')


@login_required
def owner_availability_calendar(request, property_id):
    if not user_is_owner(request.user):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)

    rooms = property_obj.rooms.all()
    blocks = AvailabilityBlock.objects.filter(
        room__property=property_obj
    ).select_related('room')

    bookings = Booking.objects.filter(
        property=property_obj,
        status__in=['pending', 'accepted']
    ).select_related('room', 'client')

    form = AvailabilityBlockForm()
    form.fields['room'].queryset = rooms

    return render(request, 'owner/availability_calendar.html', {
        'property': property_obj,
        'rooms': rooms,
        'blocks': blocks,
        'bookings': bookings,
        'form': form,
    })


@login_required
def owner_availability_events(request, property_id):
    if not user_is_owner(request.user):
        return JsonResponse([], safe=False)

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)

    events = []

    blocks = AvailabilityBlock.objects.filter(
        room__property=property_obj
    ).select_related('room')

    for block in blocks:
        events.append({
            'title': f'Bloqueio - {block.room.name}',
            'start': block.start_datetime.isoformat(),
            'end': block.end_datetime.isoformat(),
            'color': '#dc2626',
            'extendedProps': {
                'type': 'block',
                'reason': block.get_reason_display(),
            }
        })

    bookings = Booking.objects.filter(
        property=property_obj,
        status__in=['pending', 'accepted']
    ).select_related('room')

    for booking in bookings:
        start, end = get_booking_period(
            booking.booking_type,
            booking.checkin_date,
            booking.checkin_time,
            booking.checkout_date,
            booking.checkout_time
        )

        if start and end:
            events.append({
                'title': f'{booking.get_status_display()} - {booking.room.name}',
                'start': start.isoformat(),
                'end': end.isoformat(),
                'color': '#2563eb' if booking.status == 'accepted' else '#d97706',
                'extendedProps': {
                    'type': 'booking',
                    'customer': booking.customer_name,
                }
            })

    return JsonResponse(events, safe=False)


@login_required
def owner_availability_block_create(request, property_id):
    if not user_is_owner(request.user):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)

    if request.method == 'POST':
        form = AvailabilityBlockForm(request.POST)
        form.fields['room'].queryset = property_obj.rooms.all()

        if form.is_valid():
            block = form.save(commit=False)

            if block.room.property.owner != request.user:
                messages.error(request, 'Não tem permissão para bloquear este quarto.')
                return redirect('owner_availability_calendar', property_id=property_obj.id)

            block.created_by = request.user
            block.save()

            messages.success(request, 'Bloqueio de disponibilidade criado com sucesso.')
            return redirect('owner_availability_calendar', property_id=property_obj.id)

        messages.error(request, 'Não foi possível criar o bloqueio. Verifique os dados.')
        return redirect('owner_availability_calendar', property_id=property_obj.id)

    return redirect('owner_availability_calendar', property_id=property_obj.id)


@login_required
@require_POST
def owner_availability_block_delete(request, block_id):
    if not user_is_owner(request.user):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    block = get_object_or_404(
        AvailabilityBlock,
        pk=block_id,
        room__property__owner=request.user
    )

    property_id = block.room.property.id
    block.delete()

    messages.success(request, 'Bloqueio removido com sucesso.')
    return redirect('owner_availability_calendar', property_id=property_id)
