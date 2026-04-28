from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from properties.models import Property, Room
from .forms import BookingForm, AvailabilityBlockForm
from .models import Booking, AvailabilityBlock
from .services import calculate_booking_amount, booking_has_conflict, get_booking_period


def user_is_owner(user):
    return user.is_authenticated and hasattr(user, 'owner_profile')


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
        form = BookingForm(request.POST)

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

            messages.success(request, 'Pedido de reserva enviado com sucesso. Aguarde confirmação do proprietário.')
            return redirect('booking_success', booking_id=booking.id)
    else:
        initial = {}

        if request.user.is_authenticated:
            initial['customer_name'] = request.user.get_full_name() or request.user.username
            initial['customer_email'] = request.user.email

        form = BookingForm(initial=initial)

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
    bookings = Booking.objects.filter(
        client=request.user
    ).select_related(
        'property',
        'room'
    ).order_by('-created_at')

    return render(request, 'client/booking_list.html', {
        'bookings': bookings
    })


@login_required
def owner_booking_list(request):
    if not user_is_owner(request.user):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    bookings = Booking.objects.filter(
        property__owner=request.user
    ).select_related(
        'property',
        'room',
        'client'
    ).order_by('-created_at')

    return render(request, 'owner/booking_list.html', {
        'bookings': bookings
    })


@login_required
def owner_booking_accept(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        property__owner=request.user
    )

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

    messages.success(request, 'Reserva aceite com sucesso.')
    return redirect('owner_booking_list')


@login_required
def owner_booking_reject(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        property__owner=request.user
    )

    booking.status = 'rejected'
    booking.save()

    messages.success(request, 'Reserva rejeitada.')
    return redirect('owner_booking_list')


@login_required
def owner_booking_complete(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        property__owner=request.user
    )

    booking.status = 'completed'
    booking.save()

    messages.success(request, 'Reserva marcada como concluída.')
    return redirect('owner_booking_list')


@login_required
def client_booking_cancel(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        client=request.user
    )

    if booking.status not in ['pending', 'accepted']:
        messages.error(request, 'Esta reserva já não pode ser cancelada.')
        return redirect('client_booking_list')

    booking.status = 'cancelled'
    booking.save()

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
