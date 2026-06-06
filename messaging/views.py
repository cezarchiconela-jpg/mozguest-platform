from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking
from communications.services import (
    build_whatsapp_url,
    booking_whatsapp_message,
    booking_email_message,
    build_absolute_url,
    get_user_display_name,
    send_system_email,
)
from notifications.services import create_notification
from .forms import MessageForm
from .models import Conversation, Message
from .services import get_or_create_conversation


def _conversation_queryset_for_user(user):
    return Conversation.objects.filter(
        Q(client=user) | Q(owner=user)
    ).select_related(
        'booking',
        'booking__room',
        'property',
        'client',
        'owner',
    ).prefetch_related('messages').annotate(
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
        )
    ).distinct()


def _quick_replies_for_user(conversation, user):
    status = conversation.booking.status
    is_owner = user == conversation.owner

    if is_owner:
        replies = [
            'Olá, obrigado pelo pedido. Estamos a confirmar a disponibilidade e respondemos em breve.',
            'A reserva foi recebida. Pode confirmar a hora prevista de chegada, por favor?',
            'A reserva está aceite. Pode enviar o comprovativo de pagamento pela área de pagamentos da +258 Guest.',
            'Obrigado. A informação foi registada nesta conversa para acompanhamento.'
        ]
        if status == 'pending':
            replies.insert(0, 'Olá, recebemos o seu pedido. Estamos a validar a disponibilidade da unidade.')
        elif status == 'accepted':
            replies.insert(0, 'A sua reserva está aceite. Aguardamos o comprovativo pela +258 Guest para validação.')
        return replies[:5]

    replies = [
        'Olá, gostaria de confirmar a disponibilidade desta reserva.',
        'A que horas posso efectuar o check-in?',
        'Pode confirmar a localização exacta e referências de chegada?',
        'Obrigado. Vou acompanhar a reserva pela +258 Guest.'
    ]
    if status == 'accepted':
        replies.insert(0, 'Obrigado pela confirmação. Vou proceder com o pagamento e enviar o comprovativo pela +258 Guest.')
    elif status == 'pending':
        replies.insert(0, 'Olá, submeti uma reserva e gostaria de saber quando será confirmada.')
    return replies[:5]


def _conversation_next_action(conversation, user):
    booking = conversation.booking
    if user == conversation.owner:
        if booking.status == 'pending':
            return 'Analisar disponibilidade e aceitar ou rejeitar a reserva.'
        if booking.status == 'accepted':
            return 'Acompanhar pagamento e coordenar chegada do cliente.'
        if booking.status == 'completed':
            return 'Verificar avaliação e histórico financeiro.'
        return 'Manter histórico da conversa para referência.'

    if booking.status == 'pending':
        return 'Aguardar confirmação do proprietário. Não efectue pagamento antes da reserva ser aceite.'
    if booking.status == 'accepted':
        return 'Enviar comprovativo de pagamento pela +258 Guest e combinar chegada.'
    if booking.status == 'completed':
        return 'Pode deixar avaliação do alojamento e guardar nos favoritos.'
    if booking.status == 'rejected':
        return 'Pesquisar outro alojamento ou contactar suporte se houver dúvida.'
    return 'Acompanhar actualizações da reserva.'


@login_required
def conversation_list(request):
    q = request.GET.get('q', '').strip()
    filter_mode = request.GET.get('filtro', '').strip()

    conversations = _conversation_queryset_for_user(request.user)

    if q:
        conversations = conversations.filter(
            Q(property__name__icontains=q)
            | Q(booking__customer_name__icontains=q)
            | Q(booking__customer_phone__icontains=q)
            | Q(booking__room__name__icontains=q)
            | Q(messages__text__icontains=q)
        ).distinct()

    if filter_mode == 'nao_lidas':
        conversations = conversations.filter(unread_count__gt=0)
    elif filter_mode == 'reservas_pendentes':
        conversations = conversations.filter(booking__status='pending')
    elif filter_mode == 'reservas_aceites':
        conversations = conversations.filter(booking__status='accepted')
    elif filter_mode == 'com_pagamento':
        conversations = conversations.filter(booking__payment__isnull=False)

    conversations = conversations.order_by('-updated_at')

    all_conversations = _conversation_queryset_for_user(request.user)
    unread_message_count = Message.objects.filter(
        conversation__in=all_conversations,
        is_read=False
    ).exclude(sender=request.user).count()

    return render(request, 'messaging/conversation_list.html', {
        'conversations': conversations,
        'q': q,
        'filter_mode': filter_mode,
        'total_count': all_conversations.count(),
        'unread_count': all_conversations.filter(unread_count__gt=0).count(),
        'unread_message_count': unread_message_count,
        'pending_count': all_conversations.filter(booking__status='pending').count(),
        'accepted_count': all_conversations.filter(booking__status='accepted').count(),
        'payment_count': all_conversations.filter(booking__payment__isnull=False).count(),
        'recent_conversations': all_conversations.order_by('-updated_at')[:3],
    })


@login_required
def start_conversation_from_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    if booking.client != request.user and booking.property.owner != request.user:
        messages.error(request, 'Não tem permissão para aceder a esta conversa.')
        return redirect('home')

    if not booking.client:
        messages.error(request, 'Esta reserva não está associada a um cliente registado.')
        return redirect('home')

    conversation = get_or_create_conversation(booking)

    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.select_related(
            'booking',
            'booking__room',
            'property',
            'client',
            'owner',
        ),
        pk=conversation_id
    )

    if conversation.client != request.user and conversation.owner != request.user:
        messages.error(request, 'Não tem permissão para aceder a esta conversa.')
        return redirect('home')

    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)

        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            # Actualiza o campo updated_at da conversa.
            conversation.save()

            if request.user == conversation.client:
                recipient = conversation.owner
                sender_label = conversation.booking.customer_name or get_user_display_name(request.user)
            else:
                recipient = conversation.client
                sender_label = conversation.property.name or get_user_display_name(request.user)

            link = f'/mensagens/{conversation.id}/'
            create_notification(
                recipient=recipient,
                title='Nova mensagem recebida',
                message=f'{sender_label} enviou uma nova mensagem sobre a reserva #{conversation.booking.id}.',
                notification_type='system',
                link=link
            )
            send_system_email(
                getattr(recipient, 'email', ''),
                f'+258 Guest - nova mensagem na reserva #{conversation.booking.id}',
                booking_email_message(
                    conversation.booking,
                    intro=f'{sender_label} enviou uma nova mensagem na +258 Guest:\n\n"{message.text[:500]}"',
                    action_link=build_absolute_url(link, request=request)
                )
            )

            messages.success(request, 'Mensagem enviada e notificação registada.')
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    messages_qs = conversation.messages.select_related('sender').all()

    if request.user == conversation.client:
        other_party_label = conversation.property.name
        other_party_phone = conversation.property.whatsapp or conversation.property.phone
        current_role = 'cliente'
    else:
        other_party_label = conversation.booking.customer_name
        other_party_phone = conversation.booking.customer_phone
        current_role = 'proprietario'

    whatsapp_url = build_whatsapp_url(
        other_party_phone,
        booking_whatsapp_message(conversation.booking)
    )

    quick_replies = _quick_replies_for_user(conversation, request.user)
    next_action = _conversation_next_action(conversation, request.user)

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'messages_qs': messages_qs,
        'form': form,
        'other_party_label': other_party_label,
        'other_party_phone': other_party_phone,
        'whatsapp_url': whatsapp_url,
        'quick_replies': quick_replies,
        'next_action': next_action,
        'current_role': current_role,
        'message_count': messages_qs.count(),
    })
