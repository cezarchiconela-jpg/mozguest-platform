from django.db import models
from django.contrib.auth.models import User
from bookings.models import Booking


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('emola', 'e-Mola'),
        ('bank_transfer', 'Transferência bancária'),
        ('cash', 'Pagamento no local'),
        ('other', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('submitted', 'Comprovativo enviado'),
        ('confirmed', 'Confirmado'),
        ('rejected', 'Rejeitado'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Reserva'
    )

    client = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Cliente'
    )

    payment_method = models.CharField(
        'Método de pagamento',
        max_length=30,
        choices=PAYMENT_METHODS
    )

    amount = models.DecimalField(
        'Valor pago',
        max_digits=10,
        decimal_places=2
    )

    platform_commission_percent = models.DecimalField(
        'Comissão da plataforma (%)',
        max_digits=5,
        decimal_places=2,
        default=10
    )

    platform_commission_amount = models.DecimalField(
        'Comissão MozGuest',
        max_digits=10,
        decimal_places=2,
        default=0
    )

    owner_amount = models.DecimalField(
        'Valor do proprietário',
        max_digits=10,
        decimal_places=2,
        default=0
    )

    transaction_reference = models.CharField(
        'Referência da transacção',
        max_length=150,
        blank=True
    )

    proof = models.ImageField(
        'Comprovativo',
        upload_to='payments/',
        null=True,
        blank=True
    )

    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    admin_notes = models.TextField('Notas administrativas', blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.amount:
            self.platform_commission_amount = (self.amount * self.platform_commission_percent) / 100
            self.owner_amount = self.amount - self.platform_commission_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Pagamento #{self.id} - {self.booking.property.name}'
