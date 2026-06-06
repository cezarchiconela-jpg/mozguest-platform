from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking', 'Reserva'),
        ('payment', 'Pagamento'),
        ('property', 'Propriedade'),
        ('review', 'Avaliação'),
        ('system', 'Sistema'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinatário'
    )

    notification_type = models.CharField(
        'Tipo',
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='system'
    )

    title = models.CharField('Título', max_length=200)
    message = models.TextField('Mensagem')

    link = models.CharField(
        'Link',
        max_length=300,
        blank=True,
        help_text='URL interna para onde o utilizador será enviado ao clicar.'
    )

    is_read = models.BooleanField('Lida', default=False)

    created_at = models.DateTimeField('Criada em', auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient.username} - {self.title}'
