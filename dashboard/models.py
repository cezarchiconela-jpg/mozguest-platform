from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Registo operacional de acções sensíveis realizadas na plataforma."""

    ACTION_CHOICES = [
        ('property_approved', 'Propriedade aprovada'),
        ('property_rejected', 'Propriedade rejeitada'),
        ('property_featured', 'Destaque de propriedade alterado'),
        ('review_approved', 'Avaliação aprovada'),
        ('review_rejected', 'Avaliação rejeitada'),
        ('booking_accepted', 'Reserva aceite'),
        ('booking_rejected', 'Reserva rejeitada'),
        ('booking_cancelled', 'Reserva cancelada'),
        ('booking_completed', 'Reserva concluída'),
        ('payment_confirmed', 'Pagamento confirmado'),
        ('payment_rejected', 'Pagamento rejeitado'),
        ('payout_paid', 'Liquidação paga'),
        ('payout_held', 'Liquidação retida'),
        ('payout_synced', 'Liquidações sincronizadas'),
        ('owner_verified', 'Proprietário verificado'),
        ('owner_rejected', 'Verificação do proprietário rejeitada'),
        ('owner_suspended', 'Proprietário suspenso'),
        ('refund_reviewed', 'Cancelamento/reembolso revisto'),
        ('other', 'Outra acção'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guest258_audit_logs',
        verbose_name='Utilizador que executou'
    )
    action = models.CharField('Acção', max_length=50, choices=ACTION_CHOICES, default='other')
    target_model = models.CharField('Modelo alvo', max_length=120, blank=True)
    target_id = models.CharField('ID alvo', max_length=80, blank=True)
    target_repr = models.CharField('Descrição do alvo', max_length=255, blank=True)
    message = models.TextField('Mensagem')
    metadata = models.JSONField('Metadados', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('Navegador/Dispositivo', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Registo de auditoria'
        verbose_name_plural = 'Registos de auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['target_model', 'target_id']),
            models.Index(fields=['actor', 'created_at']),
        ]

    def __str__(self):
        actor = self.actor.get_username() if self.actor else 'Sistema'
        return f'{actor} - {self.get_action_display()} - {self.created_at:%Y-%m-%d %H:%M}'
