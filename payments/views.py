import csv
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from bookings.models import Booking
from .forms import PaymentForm, GatewayPaymentForm, OwnerPayoutActionForm, RefundReviewForm
from .models import Payment, PaymentTransaction, OwnerPayout
from .gateways import get_gateway, GATEWAYS
from monetization.services import get_owner_commission_percentage
from notifications.services import create_notification, notify_staff
from communications.services import send_system_email
from .services import ensure_owner_payout_for_payment, mark_payout_paid, mark_payout_held
from dashboard.services import log_audit


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def get_or_create_payment_for_booking(booking, user):
    fixed_amount = booking.estimated_amount or 0
    commission_percentage = get_owner_commission_percentage(booking.property.owner)

    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'client': user,
            'amount': fixed_amount,
            'payment_method': 'mpesa',
            'platform_commission_percent': commission_percentage,
            'status': 'pending'
        }
    )

    changed = False
    if payment.client_id != getattr(user, 'id', None):
        payment.client = user
        changed = True
    if payment.amount != fixed_amount:
        payment.amount = fixed_amount
        changed = True
    if payment.platform_commission_percent != commission_percentage:
        payment.platform_commission_percent = commission_percentage
        changed = True
    if changed:
        payment.save()

    return payment, fixed_amount, commission_percentage


def client_can_pay_booking(request, booking):
    if booking.client != request.user:
        messages.error(request, 'Não tem permissão para pagar esta reserva.')
        return False

    if booking.status != 'accepted':
        messages.error(request, 'Esta reserva ainda não está disponível para pagamento. Aguarde a aceitação do proprietário.')
        return False

    return True


def notify_payment_confirmed(payment):
    if payment.client:
        create_notification(
            payment.client,
            'Pagamento confirmado',
            f'O pagamento da reserva #{payment.booking.id} foi confirmado pela +258 Guest.',
            notification_type='payment',
            link='/reservas/cliente/minhas-reservas/'
        )
        send_system_email(
            payment.client.email,
            '+258 Guest - pagamento confirmado',
            f'O pagamento da reserva #{payment.booking.id} foi confirmado com sucesso.'
        )

    create_notification(
        payment.booking.property.owner,
        'Pagamento confirmado',
        f'A +258 Guest confirmou o pagamento da reserva #{payment.booking.id}.',
        notification_type='payment',
        link='/pagamentos/proprietario/financeiro/'
    )
    send_system_email(
        payment.booking.property.owner.email,
        '+258 Guest - pagamento confirmado',
        f'O pagamento da reserva #{payment.booking.id} foi confirmado. Consulte o seu painel financeiro.'
    )


@login_required
def submit_payment(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    if booking.client != request.user:
        messages.error(request, 'Não tem permissão para pagar esta reserva.')
        return redirect('home')

    if booking.status != 'accepted':
        messages.error(request, 'Esta reserva ainda não está disponível para pagamento. Aguarde a aceitação do proprietário.')
        return redirect('client_booking_list')

    fixed_amount = booking.estimated_amount or 0
    commission_percentage = get_owner_commission_percentage(booking.property.owner)

    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'client': request.user,
            'amount': fixed_amount,
            'payment_method': 'mpesa',
            'platform_commission_percent': commission_percentage,
            'status': 'pending'
        }
    )

    if payment.amount != fixed_amount or payment.platform_commission_percent != commission_percentage:
        payment.amount = fixed_amount
        payment.platform_commission_percent = commission_percentage
        payment.save()

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES, instance=payment, fixed_amount=fixed_amount)

        if form.is_valid():
            payment = form.save(commit=False)
            payment.client = request.user
            payment.booking = booking
            payment.amount = fixed_amount
            payment.platform_commission_percent = commission_percentage
            payment.status = 'submitted'
            payment.save()

            create_notification(
                booking.property.owner,
                'Comprovativo recebido',
                f'O cliente enviou comprovativo para a reserva #{booking.id} em {booking.property.name}.',
                notification_type='payment',
                link='/pagamentos/proprietario/pagamentos/'
            )
            notify_staff(
                'Pagamento pendente de confirmação',
                f'Comprovativo enviado para a reserva #{booking.id}. Validar pagamento no +258 Admin.',
                notification_type='payment',
                link='/258-admin/pagamentos/'
            )
            send_system_email(
                booking.property.owner.email,
                '+258 Guest - comprovativo recebido',
                f'O cliente enviou comprovativo para a reserva #{booking.id}. A administração irá validar o pagamento.'
            )

            messages.success(request, 'Comprovativo de pagamento enviado com sucesso. Aguarde confirmação.')
            return redirect('client_booking_list')
    else:
        form = PaymentForm(instance=payment, fixed_amount=fixed_amount)

    owner_payment_phone = getattr(getattr(booking.property.owner, 'owner_profile', None), 'payment_phone', '')

    return render(request, 'payments/payment_form.html', {
        'form': form,
        'booking': booking,
        'payment': payment,
        'owner_payment_phone': owner_payment_phone,
        'guest258_mpesa_number': getattr(settings, 'GUEST258_MPESA_NUMBER', ''),
        'guest258_emola_number': getattr(settings, 'GUEST258_EMOLA_NUMBER', ''),
        'guest258_bank_details': getattr(settings, 'GUEST258_BANK_DETAILS', ''),
        'guest258_payment_note': getattr(settings, 'GUEST258_PAYMENT_NOTE', ''),
    })


@login_required
def owner_payment_list(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    status = request.GET.get('status', '').strip()
    valid_statuses = {choice[0] for choice in Payment.STATUS_CHOICES}

    payments = Payment.objects.filter(
        booking__property__owner=request.user
    ).select_related('booking', 'booking__property', 'booking__room').order_by('-created_at')

    if status in valid_statuses:
        payments = payments.filter(status=status)
    else:
        status = ''

    return render(request, 'owner/payment_list.html', {
        'payments': payments,
        'status': status,
        'submitted_count': Payment.objects.filter(booking__property__owner=request.user, status='submitted').count(),
        'confirmed_count': Payment.objects.filter(booking__property__owner=request.user, status='confirmed').count(),
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
    pending_payments = payments.filter(status__in=['pending', 'submitted', 'initiated'])
    rejected_payments = payments.filter(status='rejected')

    payouts = OwnerPayout.objects.filter(owner=request.user)
    payout_pending_total = payouts.filter(status__in=['pending', 'scheduled']).aggregate(total=Sum('payout_amount'))['total'] or 0
    payout_paid_total = payouts.filter(status='paid').aggregate(total=Sum('payout_amount'))['total'] or 0
    payout_held_total = payouts.filter(status='held').aggregate(total=Sum('payout_amount'))['total'] or 0

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
        'payout_pending_total': payout_pending_total,
        'payout_paid_total': payout_paid_total,
        'payout_held_total': payout_held_total,
        'payout_pending_count': payouts.filter(status='pending').count(),
        'payout_paid_count': payouts.filter(status='paid').count(),
        'payout_held_count': payouts.filter(status='held').count(),
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

    payouts = OwnerPayout.objects.all()
    payout_pending_total = payouts.filter(status__in=['pending', 'scheduled']).aggregate(total=Sum('payout_amount'))['total'] or 0
    payout_paid_total = payouts.filter(status='paid').aggregate(total=Sum('payout_amount'))['total'] or 0
    payout_held_total = payouts.filter(status='held').aggregate(total=Sum('payout_amount'))['total'] or 0

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
        'payout_pending_total': payout_pending_total,
        'payout_paid_total': payout_paid_total,
        'payout_held_total': payout_held_total,
        'payout_pending_count': payouts.filter(status='pending').count(),
        'payout_paid_count': payouts.filter(status='paid').count(),
        'payout_held_count': payouts.filter(status='held').count(),
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
    response['Content-Disposition'] = 'attachment; filename="guest258_relatorio_financeiro.csv"'

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
        'Comissao +258 Guest',
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
    response['Content-Disposition'] = 'attachment; filename="guest258_relatorio_proprietario.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID Pagamento',
        'ID Reserva',
        'Cliente',
        'Propriedade',
        'Quarto',
        'Metodo',
        'Valor Pago',
        'Comissao +258 Guest',
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


@login_required
def start_gateway_payment(request, booking_id, gateway_name):
    booking = get_object_or_404(Booking, pk=booking_id)

    if not client_can_pay_booking(request, booking):
        return redirect('client_booking_list')

    if gateway_name not in GATEWAYS:
        messages.error(request, 'Método de pagamento online não suportado.')
        return redirect('submit_payment', booking_id=booking.id)

    payment, fixed_amount, commission_percentage = get_or_create_payment_for_booking(booking, request.user)

    if payment.status == 'confirmed':
        messages.info(request, 'Este pagamento já está confirmado.')
        return redirect('client_booking_list')

    if request.method == 'POST':
        form = GatewayPaymentForm(request.POST)
        if form.is_valid():
            transaction = PaymentTransaction.objects.create(
                payment=payment,
                gateway=gateway_name,
                amount=fixed_amount,
                phone_number=form.cleaned_data['phone_number'],
                status='created'
            )

            gateway = get_gateway(gateway_name)
            result = gateway.initiate(transaction)

            transaction.status = result.status
            transaction.external_reference = result.external_reference
            transaction.checkout_url = result.checkout_url
            transaction.provider_response = result.provider_response
            transaction.error_message = result.error_message
            transaction.save()

            if result.status == 'paid':
                transaction.mark_paid(
                    external_reference=result.external_reference,
                    provider_response=result.provider_response
                )
                notify_payment_confirmed(payment)
                messages.success(request, 'Pagamento confirmado com sucesso.')
            elif result.success:
                payment.status = 'initiated'
                payment.payment_method = gateway_name
                payment.transaction_reference = transaction.local_reference
                payment.save()

                create_notification(
                    booking.property.owner,
                    'Pagamento online iniciado',
                    f'O cliente iniciou pagamento {transaction.get_gateway_display()} para a reserva #{booking.id}.',
                    notification_type='payment',
                    link='/pagamentos/proprietario/pagamentos/'
                )
                notify_staff(
                    'Pagamento online iniciado',
                    f'Transacção {transaction.local_reference} iniciada para a reserva #{booking.id}.',
                    notification_type='payment',
                    link='/258-admin/pagamentos/'
                )
                messages.success(request, 'Pedido de pagamento iniciado. Autorize no telemóvel e acompanhe o estado nesta página.')
            else:
                transaction.mark_failed(result.error_message)
                messages.error(request, f'Não foi possível iniciar o pagamento: {result.error_message}')

            return redirect('payment_transaction_status', transaction_id=transaction.id)
    else:
        initial_phone = booking.customer_phone or ''
        form = GatewayPaymentForm(initial={'phone_number': initial_phone})

    return render(request, 'payments/gateway_start.html', {
        'form': form,
        'booking': booking,
        'payment': payment,
        'gateway_name': gateway_name,
        'gateway_label': dict(PaymentTransaction.GATEWAY_CHOICES).get(gateway_name, gateway_name),
        'payment_gateway_mode': getattr(settings, 'GUEST258_PAYMENT_GATEWAY_MODE', 'sandbox'),
    })


@login_required
def payment_transaction_status(request, transaction_id):
    transaction = get_object_or_404(
        PaymentTransaction.objects.select_related('payment', 'payment__booking', 'payment__booking__property'),
        pk=transaction_id
    )
    booking = transaction.payment.booking

    if booking.client != request.user and booking.property.owner != request.user and not request.user.is_staff:
        messages.error(request, 'Não tem permissão para ver esta transacção.')
        return redirect('home')

    can_simulate = getattr(settings, 'GUEST258_PAYMENT_GATEWAY_MODE', 'sandbox') != 'live' or settings.DEBUG

    return render(request, 'payments/transaction_status.html', {
        'transaction': transaction,
        'payment': transaction.payment,
        'booking': booking,
        'can_simulate': can_simulate,
    })


@login_required
@require_POST
def check_gateway_payment_status(request, transaction_id):
    transaction = get_object_or_404(PaymentTransaction, pk=transaction_id)
    booking = transaction.payment.booking

    if booking.client != request.user and booking.property.owner != request.user and not request.user.is_staff:
        messages.error(request, 'Não tem permissão para consultar esta transacção.')
        return redirect('home')

    gateway = get_gateway(transaction.gateway)
    result = gateway.query(transaction)

    transaction.provider_response = result.provider_response or transaction.provider_response
    transaction.error_message = result.error_message
    if result.external_reference:
        transaction.external_reference = result.external_reference

    if result.status == 'paid' and transaction.status != 'paid':
        transaction.save()
        transaction.mark_paid(result.external_reference, result.provider_response)
        notify_payment_confirmed(transaction.payment)
        messages.success(request, 'Pagamento confirmado.')
    else:
        transaction.status = result.status or transaction.status
        transaction.save()
        if result.success:
            messages.info(request, 'Estado da transacção actualizado.')
        else:
            messages.error(request, result.error_message or 'Não foi possível consultar o pagamento.')

    return redirect('payment_transaction_status', transaction_id=transaction.id)


@login_required
@require_POST
def simulate_gateway_payment_success(request, transaction_id):
    transaction = get_object_or_404(PaymentTransaction, pk=transaction_id)
    booking = transaction.payment.booking

    if booking.client != request.user and not request.user.is_staff:
        messages.error(request, 'Não tem permissão para simular esta transacção.')
        return redirect('home')

    if getattr(settings, 'GUEST258_PAYMENT_GATEWAY_MODE', 'sandbox') == 'live' and not settings.DEBUG:
        messages.error(request, 'Simulação desactivada em produção live.')
        return redirect('payment_transaction_status', transaction_id=transaction.id)

    transaction.mark_paid(
        external_reference=transaction.external_reference or f'SIMULADO-{transaction.local_reference}',
        provider_response='Pagamento confirmado por simulação sandbox/local.'
    )
    notify_payment_confirmed(transaction.payment)
    messages.success(request, 'Pagamento simulado e confirmado com sucesso.')
    return redirect('payment_transaction_status', transaction_id=transaction.id)


@csrf_exempt
def payment_gateway_webhook(request, gateway_name):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método não permitido'}, status=405)

    expected_token = getattr(settings, 'GUEST258_GATEWAY_CALLBACK_TOKEN', '')
    if expected_token:
        received_token = request.headers.get('X-+258 Guest-Token') or request.GET.get('token', '')
        if received_token != expected_token:
            return HttpResponseForbidden('Token inválido')

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    local_reference = str(payload.get('reference') or payload.get('local_reference') or payload.get('merchant_reference') or '')
    external_reference = str(payload.get('transaction_id') or payload.get('external_reference') or payload.get('provider_reference') or '')
    raw_status = str(payload.get('status') or payload.get('payment_status') or '').lower()

    if not local_reference and not external_reference:
        return JsonResponse({'ok': False, 'error': 'Referência em falta'}, status=400)

    transactions = PaymentTransaction.objects.filter(gateway=gateway_name)
    if local_reference:
        transactions = transactions.filter(local_reference=local_reference)
    else:
        transactions = transactions.filter(external_reference=external_reference)

    transaction = transactions.select_related('payment', 'payment__booking', 'payment__booking__property').first()
    if not transaction:
        return JsonResponse({'ok': False, 'error': 'Transacção não encontrada'}, status=404)

    gateway = get_gateway(gateway_name)
    status = gateway._normalize_status(raw_status)

    transaction.callback_received_at = timezone.now()
    transaction.provider_response = json.dumps(payload, ensure_ascii=False)
    if external_reference:
        transaction.external_reference = external_reference

    if status == 'paid':
        transaction.save()
        transaction.mark_paid(external_reference=external_reference, provider_response=transaction.provider_response)
        notify_payment_confirmed(transaction.payment)
    elif status in {'failed', 'cancelled', 'expired'}:
        transaction.status = status
        transaction.error_message = str(payload.get('error') or payload.get('message') or '')
        transaction.save()
        if transaction.payment.status not in {'confirmed', 'submitted'}:
            transaction.payment.status = 'failed'
            transaction.payment.save(update_fields=['status', 'updated_at'])
    else:
        transaction.status = status
        transaction.save()

    return JsonResponse({'ok': True, 'transaction': transaction.local_reference, 'status': transaction.status})


@user_passes_test(is_staff_user)
def admin_transaction_list(request):
    status = request.GET.get('status', '').strip()
    gateway = request.GET.get('gateway', '').strip()

    transactions = PaymentTransaction.objects.select_related(
        'payment',
        'payment__booking',
        'payment__booking__property',
        'payment__booking__property__owner',
        'payment__client',
    ).order_by('-created_at')

    if status:
        transactions = transactions.filter(status=status)
    if gateway:
        transactions = transactions.filter(gateway=gateway)

    return render(request, 'admin_panel/payment_transaction_list.html', {
        'transactions': transactions,
        'status': status,
        'gateway': gateway,
        'gateway_choices': PaymentTransaction.GATEWAY_CHOICES,
        'status_choices': PaymentTransaction.STATUS_CHOICES,
        'total_count': PaymentTransaction.objects.count(),
        'waiting_count': PaymentTransaction.objects.filter(status='waiting_authorization').count(),
        'paid_count': PaymentTransaction.objects.filter(status='paid').count(),
        'failed_count': PaymentTransaction.objects.filter(status='failed').count(),
    })


@login_required
def owner_payout_list(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    status = request.GET.get('status', '').strip()
    valid_statuses = {choice[0] for choice in OwnerPayout.STATUS_CHOICES}

    payouts = OwnerPayout.objects.filter(owner=request.user).select_related(
        'payment',
        'payment__booking',
        'payment__booking__property',
        'payment__booking__room',
    ).order_by('-created_at')

    if status in valid_statuses:
        payouts = payouts.filter(status=status)
    else:
        status = ''

    confirmed_payment_total = Payment.objects.filter(
        booking__property__owner=request.user,
        status='confirmed'
    ).aggregate(total=Sum('owner_amount'))['total'] or 0

    pending_total = payouts.filter(status__in=['pending', 'scheduled']).aggregate(total=Sum('payout_amount'))['total'] or 0
    paid_total = payouts.filter(status='paid').aggregate(total=Sum('payout_amount'))['total'] or 0
    held_total = payouts.filter(status='held').aggregate(total=Sum('payout_amount'))['total'] or 0

    return render(request, 'owner/payout_list.html', {
        'payouts': payouts,
        'status': status,
        'status_choices': OwnerPayout.STATUS_CHOICES,
        'confirmed_payment_total': confirmed_payment_total,
        'pending_total': pending_total,
        'paid_total': paid_total,
        'held_total': held_total,
        'pending_count': OwnerPayout.objects.filter(owner=request.user, status='pending').count(),
        'scheduled_count': OwnerPayout.objects.filter(owner=request.user, status='scheduled').count(),
        'paid_count': OwnerPayout.objects.filter(owner=request.user, status='paid').count(),
        'held_count': OwnerPayout.objects.filter(owner=request.user, status='held').count(),
    })


@user_passes_test(is_staff_user)
def admin_payout_list(request):
    status = request.GET.get('status', 'pending').strip()
    query = request.GET.get('q', '').strip()
    valid_statuses = {choice[0] for choice in OwnerPayout.STATUS_CHOICES}

    payouts = OwnerPayout.objects.select_related(
        'owner',
        'payment',
        'payment__client',
        'payment__booking',
        'payment__booking__property',
        'payment__booking__room',
    ).order_by('-created_at')

    if status in valid_statuses:
        payouts = payouts.filter(status=status)
    elif status == 'all':
        status = 'all'
    else:
        status = 'pending'
        payouts = payouts.filter(status='pending')

    if query:
        payouts = payouts.filter(
            Q(owner__username__icontains=query) |
            Q(owner__email__icontains=query) |
            Q(payment__booking__customer_name__icontains=query) |
            Q(payment__booking__property__name__icontains=query) |
            Q(payout_reference__icontains=query) |
            Q(payment__transaction_reference__icontains=query)
        )

    all_payouts = OwnerPayout.objects.all()
    pending_total = all_payouts.filter(status__in=['pending', 'scheduled']).aggregate(total=Sum('payout_amount'))['total'] or 0
    paid_total = all_payouts.filter(status='paid').aggregate(total=Sum('payout_amount'))['total'] or 0
    held_total = all_payouts.filter(status='held').aggregate(total=Sum('payout_amount'))['total'] or 0
    total_commission = Payment.objects.filter(status='confirmed').aggregate(total=Sum('platform_commission_amount'))['total'] or 0

    return render(request, 'admin_panel/payout_list.html', {
        'payouts': payouts,
        'status': status,
        'query': query,
        'status_choices': OwnerPayout.STATUS_CHOICES,
        'pending_total': pending_total,
        'paid_total': paid_total,
        'held_total': held_total,
        'total_commission': total_commission,
        'pending_count': all_payouts.filter(status='pending').count(),
        'scheduled_count': all_payouts.filter(status='scheduled').count(),
        'paid_count': all_payouts.filter(status='paid').count(),
        'held_count': all_payouts.filter(status='held').count(),
        'cancelled_count': all_payouts.filter(status='cancelled').count(),
        'action_form': OwnerPayoutActionForm(),
    })


@user_passes_test(is_staff_user)
@require_POST
def admin_mark_payout_paid(request, payout_id):
    payout = get_object_or_404(OwnerPayout.objects.select_related('payment', 'payment__booking', 'owner'), pk=payout_id)
    form = OwnerPayoutActionForm(request.POST)

    if form.is_valid():
        mark_payout_paid(
            payout,
            method=form.cleaned_data.get('method') or payout.method or 'mpesa',
            reference=form.cleaned_data.get('payout_reference') or '',
            notes=form.cleaned_data.get('admin_notes') or '',
            actor=request.user,
        )
        messages.success(request, 'Liquidação marcada como paga com sucesso.')
    else:
        messages.error(request, 'Verifique os dados da liquidação.')

    return redirect('admin_owner_payout_list')


@user_passes_test(is_staff_user)
@require_POST
def admin_hold_payout(request, payout_id):
    payout = get_object_or_404(OwnerPayout.objects.select_related('payment', 'payment__booking', 'owner'), pk=payout_id)
    notes = request.POST.get('admin_notes', '').strip()
    mark_payout_held(payout, notes=notes, actor=request.user)
    messages.success(request, 'Liquidação colocada em retenção para análise.')
    return redirect('admin_owner_payout_list')


@user_passes_test(is_staff_user)
@require_POST
def admin_sync_missing_payouts(request):
    verified_count = 0
    for payment in Payment.objects.filter(status='confirmed').select_related('booking', 'booking__property'):
        payout = ensure_owner_payout_for_payment(payment)
        if payout:
            verified_count += 1
    messages.success(request, f'Liquidações sincronizadas com base nos pagamentos confirmados. Total verificado: {verified_count}.')
    return redirect('admin_owner_payout_list')


@user_passes_test(is_staff_user)
def admin_payout_export_csv(request):
    payouts = OwnerPayout.objects.select_related(
        'owner', 'payment', 'payment__booking', 'payment__booking__property'
    ).order_by('-created_at')

    status = request.GET.get('status')
    if status:
        payouts = payouts.filter(status=status)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="guest258_liquidacoes_proprietarios.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID Liquidação',
        'ID Pagamento',
        'ID Reserva',
        'Proprietário',
        'Propriedade',
        'Valor Pago Cliente',
        'Comissão +258 Guest',
        'Valor Proprietário',
        'Estado',
        'Método',
        'Referência',
        'Criado em',
        'Liquidado em',
    ])

    for payout in payouts:
        writer.writerow([
            payout.id,
            payout.payment.id,
            payout.payment.booking.id,
            payout.owner.username if payout.owner else '',
            payout.payment.booking.property.name,
            payout.gross_amount,
            payout.commission_amount,
            payout.payout_amount,
            payout.get_status_display(),
            payout.get_method_display() if payout.method else '',
            payout.payout_reference,
            payout.created_at,
            payout.paid_at,
        ])

    return response


@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related('booking', 'booking__property', 'booking__room', 'client'),
        pk=payment_id,
        status='confirmed'
    )
    booking = payment.booking
    if booking.client != request.user and booking.property.owner != request.user and not request.user.is_staff:
        messages.error(request, 'Não tem permissão para ver este recibo.')
        return redirect('home')

    return render(request, 'payments/payment_receipt.html', {
        'payment': payment,
        'booking': booking,
        'print_mode': request.GET.get('print') == '1',
    })


@login_required
def payout_receipt(request, payout_id):
    payout = get_object_or_404(
        OwnerPayout.objects.select_related('payment', 'payment__booking', 'payment__booking__property', 'owner'),
        pk=payout_id,
        status='paid'
    )
    if payout.owner != request.user and not request.user.is_staff:
        messages.error(request, 'Não tem permissão para ver este comprovativo de liquidação.')
        return redirect('home')

    return render(request, 'payments/payout_receipt.html', {
        'payout': payout,
        'payment': payout.payment,
        'booking': payout.payment.booking,
        'print_mode': request.GET.get('print') == '1',
    })


@user_passes_test(is_staff_user)
def admin_daily_finance_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    payments = Payment.objects.filter(status='confirmed')
    payouts = OwnerPayout.objects.all()

    if start_date:
        payments = payments.filter(updated_at__date__gte=start_date)
        payouts = payouts.filter(updated_at__date__gte=start_date)
    if end_date:
        payments = payments.filter(updated_at__date__lte=end_date)
        payouts = payouts.filter(updated_at__date__lte=end_date)

    total_received = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_commission = payments.aggregate(total=Sum('platform_commission_amount'))['total'] or 0
    total_owner_amount = payments.aggregate(total=Sum('owner_amount'))['total'] or 0
    total_payout_paid = payouts.filter(status='paid').aggregate(total=Sum('payout_amount'))['total'] or 0
    total_payout_pending = OwnerPayout.objects.filter(status__in=['pending', 'scheduled']).aggregate(total=Sum('payout_amount'))['total'] or 0
    total_payout_held = OwnerPayout.objects.filter(status='held').aggregate(total=Sum('payout_amount'))['total'] or 0

    daily_rows = []
    by_date = {}
    for payment in payments.select_related('booking'):
        key = timezone.localtime(payment.updated_at).date()
        row = by_date.setdefault(key, {'date': key, 'received': 0, 'commission': 0, 'owner_amount': 0, 'payments': 0, 'payout_paid': 0})
        row['received'] += payment.amount or 0
        row['commission'] += payment.platform_commission_amount or 0
        row['owner_amount'] += payment.owner_amount or 0
        row['payments'] += 1
    for payout in payouts.filter(status='paid'):
        key = timezone.localtime(payout.paid_at or payout.updated_at).date()
        row = by_date.setdefault(key, {'date': key, 'received': 0, 'commission': 0, 'owner_amount': 0, 'payments': 0, 'payout_paid': 0})
        row['payout_paid'] += payout.payout_amount or 0
    daily_rows = [by_date[k] for k in sorted(by_date.keys(), reverse=True)]

    return render(request, 'admin_panel/daily_finance_report.html', {
        'start_date': start_date,
        'end_date': end_date,
        'total_received': total_received,
        'total_commission': total_commission,
        'total_owner_amount': total_owner_amount,
        'total_payout_paid': total_payout_paid,
        'total_payout_pending': total_payout_pending,
        'total_payout_held': total_payout_held,
        'daily_rows': daily_rows,
    })


@user_passes_test(is_staff_user)
def admin_refund_review_list(request):
    status = request.GET.get('status', 'pending_review').strip()
    query = request.GET.get('q', '').strip()
    valid = {choice[0] for choice in Booking.REFUND_STATUS_CHOICES}

    bookings = Booking.objects.filter(status='cancelled').select_related('property', 'room', 'client', 'payment').order_by('-updated_at')
    if status in valid:
        bookings = bookings.filter(refund_status=status)
    elif status == 'all':
        status = 'all'
    else:
        status = 'pending_review'
        bookings = bookings.filter(refund_status='pending_review')

    if query:
        bookings = bookings.filter(
            Q(customer_name__icontains=query) |
            Q(customer_phone__icontains=query) |
            Q(property__name__icontains=query) |
            Q(refund_reference__icontains=query)
        )

    return render(request, 'admin_panel/refund_review_list.html', {
        'bookings': bookings,
        'status': status,
        'query': query,
        'status_choices': Booking.REFUND_STATUS_CHOICES,
        'pending_count': Booking.objects.filter(status='cancelled', refund_status='pending_review').count(),
        'refunded_count': Booking.objects.filter(status='cancelled', refund_status='refunded').count(),
        'form': RefundReviewForm(),
    })


@user_passes_test(is_staff_user)
@require_POST
def admin_review_refund(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related('property', 'client'), pk=booking_id, status='cancelled')
    form = RefundReviewForm(request.POST)
    if form.is_valid():
        booking.refund_status = form.cleaned_data['refund_status']
        booking.refund_amount = form.cleaned_data.get('refund_amount')
        booking.refund_reference = form.cleaned_data.get('refund_reference') or ''
        booking.refund_notes = form.cleaned_data.get('refund_notes') or ''
        booking.refund_reviewed_by = request.user
        booking.refund_reviewed_at = timezone.now()
        booking.save(update_fields=['refund_status', 'refund_amount', 'refund_reference', 'refund_notes', 'refund_reviewed_by', 'refund_reviewed_at', 'updated_at'])

        if booking.client:
            create_notification(
                booking.client,
                'Cancelamento/reembolso actualizado',
                f'A +258 Guest actualizou a análise do cancelamento da reserva #{booking.id}: {booking.get_refund_status_display()}.',
                notification_type='payment',
                link='/reservas/cliente/minhas-reservas/?status=cancelled'
            )
        log_audit(
            'refund_reviewed',
            request=request,
            target=booking,
            message=f'Reembolso/cancelamento revisto: {booking.get_refund_status_display()}.',
            metadata={'refund_amount': str(booking.refund_amount or ''), 'refund_reference': booking.refund_reference}
        )
        messages.success(request, 'Análise de cancelamento/reembolso actualizada com sucesso.')
    else:
        messages.error(request, 'Verifique os dados do reembolso.')
    return redirect('admin_refund_review_list')
