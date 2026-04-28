from django.db import models
from django.contrib.auth.models import User
from bookings.models import Booking


class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('booking_problem', 'Problema com reserva'),
        ('payment_problem', 'Problema com pagamento'),
        ('property_problem', 'Problema com alojamento'),
        ('client_problem', 'Problema com cliente'),
        ('owner_problem', 'Problema com proprietário'),
        ('technical_problem', 'Problema técnico'),
        ('other', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('open', 'Aberta'),
        ('in_review', 'Em análise'),
        ('resolved', 'Resolvida'),
        ('rejected', 'Rejeitada'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name='Criado por'
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_tickets',
        verbose_name='Reserva relacionada'
    )

    category = models.CharField(
        'Categoria',
        max_length=40,
        choices=CATEGORY_CHOICES,
        default='other'
    )

    subject = models.CharField('Assunto', max_length=200)

    description = models.TextField('Descrição')

    priority = models.CharField(
        'Prioridade',
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )

    admin_response = models.TextField('Resposta da administração', blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Reclamação/Suporte'
        verbose_name_plural = 'Reclamações/Suporte'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.id} - {self.subject}'
