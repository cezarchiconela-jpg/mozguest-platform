from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking
from notifications.services import create_notification
from .forms import MessageForm
from .models import Conversation, Message
from .services import get_or_create_conversation


@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(
        client=request.user
    ) | Conversation.objects.filter(
        owner=request.user
    )

    conversations = conversations.distinct().order_by('-updated_at')

    return render(request, 'messaging/conversation_list.html', {
        'conversations': conversations
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
    conversation = get_object_or_404(Conversation, pk=conversation_id)

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

            conversation.save()

            if request.user == conversation.client:
                recipient = conversation.owner
            else:
                recipient = conversation.client

            create_notification(
                recipient=recipient,
                title='Nova mensagem recebida',
                message=f'Recebeu uma nova mensagem sobre a reserva #{conversation.booking.id}.',
                notification_type='system',
                link=f'/mensagens/{conversation.id}/'
            )

            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    messages_qs = conversation.messages.select_related('sender').all()

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'messages_qs': messages_qs,
        'form': form,
    })
