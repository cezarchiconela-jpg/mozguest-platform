from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SupportTicketForm, AdminSupportTicketForm
from .models import SupportTicket
from notifications.services import create_notification, notify_staff


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


@login_required
def support_ticket_list(request):
    tickets = SupportTicket.objects.filter(created_by=request.user)

    return render(request, 'support/ticket_list.html', {
        'tickets': tickets
    })


@login_required
def support_ticket_create(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, user=request.user)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.status = 'open'
            ticket.save()

            notify_staff(
                title='Nova reclamação aberta',
                message=f'Foi aberta uma nova reclamação: {ticket.subject}.',
                notification_type='system',
                link='/moz-admin/suporte/'
            )

            messages.success(request, 'Reclamação enviada com sucesso. A administração irá analisar.')
            return redirect('support_ticket_list')
    else:
        form = SupportTicketForm(user=request.user)

    return render(request, 'support/ticket_form.html', {
        'form': form,
        'title': 'Abrir reclamação/suporte'
    })


@login_required
def support_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        SupportTicket,
        pk=ticket_id,
        created_by=request.user
    )

    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket
    })


@login_required
def owner_support_ticket_list(request):
    if not hasattr(request.user, 'owner_profile'):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return redirect('home')

    tickets = SupportTicket.objects.filter(
        booking__property__owner=request.user
    )

    return render(request, 'owner/support_ticket_list.html', {
        'tickets': tickets
    })


@user_passes_test(is_staff_user)
def admin_support_ticket_list(request):
    tickets = SupportTicket.objects.all()

    status = request.GET.get('status')
    priority = request.GET.get('priority')

    if status:
        tickets = tickets.filter(status=status)

    if priority:
        tickets = tickets.filter(priority=priority)

    return render(request, 'admin_panel/support_ticket_list.html', {
        'tickets': tickets,
        'status': status,
        'priority': priority,
    })


@user_passes_test(is_staff_user)
def admin_support_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, pk=ticket_id)

    old_status = ticket.status

    if request.method == 'POST':
        form = AdminSupportTicketForm(request.POST, instance=ticket)

        if form.is_valid():
            ticket = form.save()

            if old_status != ticket.status:
                create_notification(
                    recipient=ticket.created_by,
                    title='Estado da reclamação actualizado',
                    message=f'A sua reclamação #{ticket.id} foi actualizada para: {ticket.get_status_display()}.',
                    notification_type='system',
                    link=f'/suporte/{ticket.id}/'
                )

            messages.success(request, 'Reclamação actualizada com sucesso.')
            return redirect('admin_support_ticket_detail', ticket_id=ticket.id)
    else:
        form = AdminSupportTicketForm(instance=ticket)

    return render(request, 'admin_panel/support_ticket_detail.html', {
        'ticket': ticket,
        'form': form,
    })
