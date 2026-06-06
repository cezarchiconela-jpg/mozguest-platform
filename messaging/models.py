from django.db import models
from django.contrib.auth.models import User
from bookings.models import Booking
from properties.models import Property


class Conversation(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='conversation',
        verbose_name='Reserva'
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name='Propriedade'
    )

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_conversations',
        verbose_name='Cliente'
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owner_conversations',
        verbose_name='Proprietário'
    )

    created_at = models.DateTimeField('Criada em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada em', auto_now=True)

    class Meta:
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
        ordering = ['-updated_at']

    def __str__(self):
        return f'Conversa reserva #{self.booking.id}'


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversa'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Remetente'
    )

    text = models.TextField('Mensagem')

    is_read = models.BooleanField('Lida', default=False)

    created_at = models.DateTimeField('Enviada em', auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['created_at']

    def __str__(self):
        return f'Mensagem de {self.sender.username}'
