import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from bookings.models import Booking
from .forms import PaymentForm
from .models import Payment


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@login_required
def submit_payment(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    if booking.client != request.user:
        messages.error(request, 'Não tem permissão para pagar esta reserva.')
        return redirect('home')

    if booking.status not in ['accepted', 'pending']:
        messages.error(request, 'Esta reserva não está disponível para pagamento.')
        return redirect('client_booking_list')

    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'client': request.user,
            'amount': booking.estimated_amount or 0,
            'payment_method': 'mpesa',
            'status': 'pending'
        }
    )

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES, instance=payment)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.client = request.user
            payment.booking = booking
            payment.status = 'submitted'
            payment.save()

            messages.success(request, 'Comprovativo de pagamento enviado com sucesso. Aguarde confirmação.')
            return redirect('client_booking_list')
    else:
        form = PaymentForm(instance=payment)

    return render(request, 'payments/payment_form.html', {
        'form': form,
        'booking': booking,
        'payment': payment,
    })


@login_required
def owner_payment_list(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    payments = Payment.objects.filter(
        booking__property__owner=request.user
    ).select_related('booking', 'booking__property', 'booking__room')

    return render(request, 'owner/payment_list.html', {
        'payments': payments
    })


@login_required
def owner_finance_dashboard(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    payments = Payment.objects.filter(
        booking__property__owner=request.user
    ).select_related('booking', 'booking__property', 'booking__room')

    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if status:
        payments = payments.filter(status=status)

    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)

    if end_date:
        payments = payments.filter(created_at__date__lte=end_date)

    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_commission = payments.aggregate(total=Sum('platform_commission_amount'))['total'] or 0
    total_owner_amount = payments.aggregate(total=Sum('owner_amount'))['total'] or 0

    confirmed_payments = payments.filter(status='confirmed')
    pending_payments = payments.filter(status__in=['pending', 'submitted'])
    rejected_payments = payments.filter(status='rejected')

    property_summary = payments.values(
        'booking__property__name'
    ).annotate(
        total_paid=Sum('amount'),
        total_commission=Sum('platform_commission_amount'),
        total_owner=Sum('owner_amount'),
        total_payments=Count('id')
    ).order_by('-total_paid')

    return render(request, 'owner/finance_dashboard.html', {
        'payments': payments,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'total_commission': total_commission,
        'total_owner_amount': total_owner_amount,
        'confirmed_payments': confirmed_payments.count(),
        'pending_payments': pending_payments.count(),
        'rejected_payments': rejected_payments.count(),
        'property_summary': property_summary,
    })


@user_passes_test(is_staff_user)
def admin_finance_dashboard(request):
    payments = Payment.objects.select_related(
        'booking',
        'booking__property',
        'booking__room',
        'booking__property__owner',
        'client'
    )

    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if status:
        payments = payments.filter(status=status)

    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)

    if end_date:
        payments = payments.filter(created_at__date__lte=end_date)

    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_commission = payments.aggregate(total=Sum('platform_commission_amount'))['total'] or 0
    total_owner_amount = payments.aggregate(total=Sum('owner_amount'))['total'] or 0

    confirmed_payments = payments.filter(status='confirmed')
    submitted_payments = payments.filter(status='submitted')
    pending_payments = payments.filter(status='pending')
    rejected_payments = payments.filter(status='rejected')

    owner_summary = payments.values(
        'booking__property__owner__username',
        'booking__property__owner__email'
    ).annotate(
        total_paid=Sum('amount'),
        total_commission=Sum('platform_commission_amount'),
        total_owner=Sum('owner_amount'),
        total_payments=Count('id')
    ).order_by('-total_paid')

    property_summary = payments.values(
        'booking__property__name',
        'booking__property__city'
    ).annotate(
        total_paid=Sum('amount'),
        total_commission=Sum('platform_commission_amount'),
        total_owner=Sum('owner_amount'),
        total_payments=Count('id')
    ).order_by('-total_paid')

    return render(request, 'admin_panel/finance_dashboard.html', {
        'payments': payments,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'total_commission': total_commission,
        'total_owner_amount': total_owner_amount,
        'confirmed_payments': confirmed_payments.count(),
        'submitted_payments': submitted_payments.count(),
        'pending_payments': pending_payments.count(),
        'rejected_payments': rejected_payments.count(),
        'owner_summary': owner_summary,
        'property_summary': property_summary,
    })


@user_passes_test(is_staff_user)
def admin_finance_export_csv(request):
    payments = Payment.objects.select_related(
        'booking',
        'booking__property',
        'booking__room',
        'booking__property__owner',
        'client'
    )

    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if status:
        payments = payments.filter(status=status)

    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)

    if end_date:
        payments = payments.filter(created_at__date__lte=end_date)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mozguest_relatorio_financeiro.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID Pagamento',
        'ID Reserva',
        'Cliente',
        'Proprietario',
        'Propriedade',
        'Quarto',
        'Metodo',
        'Valor Pago',
        'Comissao MozGuest',
        'Valor Proprietario',
        'Estado',
        'Referencia',
        'Criado em',
    ])

    for payment in payments:
        writer.writerow([
            payment.id,
            payment.booking.id,
            payment.booking.customer_name,
            payment.booking.property.owner.username,
            payment.booking.property.name,
            payment.booking.room.name,
            payment.get_payment_method_display(),
            payment.amount,
            payment.platform_commission_amount,
            payment.owner_amount,
            payment.get_status_display(),
            payment.transaction_reference,
            payment.created_at,
        ])

    return response


@login_required
def owner_finance_export_csv(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem exportar este relatório.')
        return redirect('home')

    payments = Payment.objects.filter(
        booking__property__owner=request.user
    ).select_related('booking', 'booking__property', 'booking__room')

    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if status:
        payments = payments.filter(status=status)

    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)

    if end_date:
        payments = payments.filter(created_at__date__lte=end_date)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mozguest_relatorio_proprietario.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID Pagamento',
        'ID Reserva',
        'Cliente',
        'Propriedade',
        'Quarto',
        'Metodo',
        'Valor Pago',
        'Comissao MozGuest',
        'Valor Proprietario',
        'Estado',
        'Referencia',
        'Criado em',
    ])

    for payment in payments:
        writer.writerow([
            payment.id,
            payment.booking.id,
            payment.booking.customer_name,
            payment.booking.property.name,
            payment.booking.room.name,
            payment.get_payment_method_display(),
            payment.amount,
            payment.platform_commission_amount,
            payment.owner_amount,
            payment.get_status_display(),
            payment.transaction_reference,
            payment.created_at,
        ])

    return response
