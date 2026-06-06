from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SupportTicketForm, AdminSupportTicketForm
from .models import SupportTicket
from notifications.services import create_notification, notify_staff
from communications.services import (
    send_system_email,
    send_support_team_email,
    support_email_message,
    build_absolute_url,
    support_whatsapp_url,
)


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def _tickets_for_user(user):
    return SupportTicket.objects.filter(created_by=user).select_related(
        'booking', 'booking__property', 'booking__room'
    )


def _support_next_step(ticket):
    if ticket.status == 'open':
        return 'Aguardar triagem da administração +258 Guest.'
    if ticket.status == 'in_review':
        return 'A equipa está a analisar. Mantenha documentos e mensagens da reserva disponíveis.'
    if ticket.status == 'resolved':
        return 'Verifique a resposta administrativa e confirme se a situação ficou encerrada.'
    if ticket.status == 'rejected':
        return 'Leia a decisão. Se tiver novos elementos, abra novo pedido com evidências adicionais.'
    return 'Acompanhar actualizações nesta página.'


@login_required
def support_ticket_list(request):
    status = request.GET.get('status', '').strip()
    q = request.GET.get('q', '').strip()

    tickets = _tickets_for_user(request.user)
    valid_statuses = {choice[0] for choice in SupportTicket.STATUS_CHOICES}

    if status in valid_statuses:
        tickets = tickets.filter(status=status)
    else:
        status = ''

    if q:
        tickets = tickets.filter(
            Q(subject__icontains=q)
            | Q(description__icontains=q)
            | Q(booking__property__name__icontains=q)
            | Q(booking__customer_name__icontains=q)
        ).distinct()

    base_tickets = _tickets_for_user(request.user)

    return render(request, 'support/ticket_list.html', {
        'tickets': tickets,
        'status': status,
        'q': q,
        'open_count': base_tickets.filter(status='open').count(),
        'review_count': base_tickets.filter(status='in_review').count(),
        'resolved_count': base_tickets.filter(status='resolved').count(),
        'urgent_count': base_tickets.filter(priority='urgent').count(),
        'support_whatsapp_url': support_whatsapp_url(),
    })


@login_required
def support_ticket_create(request):
    initial = {}
    booking_id = request.GET.get('booking')
    if booking_id:
        initial['booking'] = booking_id

    if request.method == 'POST':
        form = SupportTicketForm(request.POST, user=request.user)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.status = 'open'
            ticket.save()

            link = f'/258-admin/suporte/{ticket.id}/'
            notify_staff(
                title='Nova reclamação aberta',
                message=f'Foi aberta uma nova reclamação #{ticket.id}: {ticket.subject}.',
                notification_type='system',
                link=link,
                send_email=False,
            )
            send_support_team_email(
                f'+258 Guest - nova reclamação #{ticket.id}',
                support_email_message(ticket, intro='Foi aberta uma nova reclamação/suporte na plataforma.', action_link=build_absolute_url(link, request=request))
            )
            send_system_email(
                getattr(request.user, 'email', ''),
                f'+258 Guest - pedido de suporte #{ticket.id} recebido',
                support_email_message(ticket, intro='Recebemos o seu pedido de suporte. A administração irá analisar e responder pela +258 Guest.', action_link=build_absolute_url(f'/suporte/{ticket.id}/', request=request))
            )

            messages.success(request, 'Reclamação enviada com sucesso. A administração irá analisar.')
            return redirect('support_ticket_list')
    else:
        form = SupportTicketForm(user=request.user, initial=initial)

    return render(request, 'support/ticket_form.html', {
        'form': form,
        'title': 'Abrir reclamação/suporte',
        'support_whatsapp_url': support_whatsapp_url(),
    })


@login_required
def support_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        SupportTicket.objects.select_related('booking', 'booking__property', 'booking__room'),
        pk=ticket_id,
        created_by=request.user
    )

    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'next_step': _support_next_step(ticket),
        'support_whatsapp_url': support_whatsapp_url(f'Olá, preciso de apoio sobre a reclamação #{ticket.id}.'),
    })


@login_required
def owner_support_ticket_list(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    status = request.GET.get('status', '').strip()
    q = request.GET.get('q', '').strip()
    valid_statuses = {choice[0] for choice in SupportTicket.STATUS_CHOICES}

    tickets = SupportTicket.objects.filter(
        booking__property__owner=request.user
    ).select_related('created_by', 'booking', 'booking__property', 'booking__room')

    if status in valid_statuses:
        tickets = tickets.filter(status=status)
    else:
        status = ''

    if q:
        tickets = tickets.filter(
            Q(subject__icontains=q)
            | Q(description__icontains=q)
            | Q(created_by__username__icontains=q)
            | Q(booking__customer_name__icontains=q)
            | Q(booking__property__name__icontains=q)
        ).distinct()

    return render(request, 'owner/support_ticket_list.html', {
        'tickets': tickets,
        'status': status,
        'q': q,
    })


@user_passes_test(is_staff_user)
def admin_support_ticket_list(request):
    tickets = SupportTicket.objects.select_related(
        'created_by', 'booking', 'booking__property', 'booking__room'
    ).all()

    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    q = request.GET.get('q', '').strip()

    valid_statuses = {choice[0] for choice in SupportTicket.STATUS_CHOICES}
    valid_priorities = {choice[0] for choice in SupportTicket.PRIORITY_CHOICES}

    if status in valid_statuses:
        tickets = tickets.filter(status=status)
    else:
        status = ''

    if priority in valid_priorities:
        tickets = tickets.filter(priority=priority)
    else:
        priority = ''

    if q:
        tickets = tickets.filter(
            Q(subject__icontains=q)
            | Q(description__icontains=q)
            | Q(created_by__username__icontains=q)
            | Q(created_by__email__icontains=q)
            | Q(booking__customer_name__icontains=q)
            | Q(booking__property__name__icontains=q)
        ).distinct()

    all_tickets = SupportTicket.objects.all()

    return render(request, 'admin_panel/support_ticket_list.html', {
        'tickets': tickets,
        'status': status,
        'priority': priority,
        'q': q,
        'open_count': all_tickets.filter(status='open').count(),
        'review_count': all_tickets.filter(status='in_review').count(),
        'urgent_count': all_tickets.filter(priority='urgent').count(),
        'resolved_count': all_tickets.filter(status='resolved').count(),
        'rejected_count': all_tickets.filter(status='rejected').count(),
    })


@user_passes_test(is_staff_user)
def admin_support_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        SupportTicket.objects.select_related('created_by', 'booking', 'booking__property', 'booking__room'),
        pk=ticket_id
    )

    old_status = ticket.status
    old_response = ticket.admin_response

    if request.method == 'POST':
        form = AdminSupportTicketForm(request.POST, instance=ticket)

        if form.is_valid():
            ticket = form.save()
            user_link = f'/suporte/{ticket.id}/'

            if old_status != ticket.status:
                create_notification(
                    recipient=ticket.created_by,
                    title='Estado da reclamação actualizado',
                    message=f'A sua reclamação #{ticket.id} foi actualizada para: {ticket.get_status_display()}.',
                    notification_type='system',
                    link=user_link
                )
                send_system_email(
                    getattr(ticket.created_by, 'email', ''),
                    f'+258 Guest - estado da reclamação #{ticket.id} actualizado',
                    support_email_message(ticket, intro='O estado do seu pedido de suporte foi actualizado.', action_link=build_absolute_url(user_link, request=request))
                )

            if ticket.admin_response and ticket.admin_response != old_response:
                create_notification(
                    recipient=ticket.created_by,
                    title='Nova resposta da administração',
                    message=f'A administração respondeu à sua reclamação #{ticket.id}: {ticket.subject}.',
                    notification_type='system',
                    link=user_link
                )
                send_system_email(
                    getattr(ticket.created_by, 'email', ''),
                    f'+258 Guest - resposta da administração à reclamação #{ticket.id}',
                    support_email_message(ticket, intro='A administração respondeu ao seu pedido de suporte.', action_link=build_absolute_url(user_link, request=request))
                )

            messages.success(request, 'Reclamação actualizada com sucesso.')
            return redirect('admin_support_ticket_detail', ticket_id=ticket.id)
    else:
        form = AdminSupportTicketForm(instance=ticket)

    return render(request, 'admin_panel/support_ticket_detail.html', {
        'ticket': ticket,
        'form': form,
        'next_step': _support_next_step(ticket),
    })
