from decimal import Decimal
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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
        ('initiated', 'Pagamento iniciado'),
        ('submitted', 'Comprovativo enviado'),
        ('confirmed', 'Confirmado'),
        ('rejected', 'Rejeitado'),
        ('failed', 'Falhado'),
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
        'Comissão +258 Guest',
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
            self.platform_commission_amount = (self.amount * self.platform_commission_percent) / Decimal('100')
            self.owner_amount = self.amount - self.platform_commission_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Pagamento #{self.id} - {self.booking.property.name}'


class PaymentTransaction(models.Model):
    GATEWAY_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('emola', 'e-Mola'),
        ('bank_transfer', 'Transferência bancária'),
        ('manual', 'Comprovativo manual'),
        ('other', 'Outro gateway'),
    ]

    STATUS_CHOICES = [
        ('created', 'Criada'),
        ('initiated', 'Iniciada'),
        ('waiting_authorization', 'Aguardando autorização'),
        ('paid', 'Paga'),
        ('failed', 'Falhada'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
        ('refunded', 'Reembolsada'),
    ]

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Pagamento'
    )

    gateway = models.CharField(
        'Gateway',
        max_length=30,
        choices=GATEWAY_CHOICES
    )

    status = models.CharField(
        'Estado',
        max_length=30,
        choices=STATUS_CHOICES,
        default='created'
    )

    amount = models.DecimalField(
        'Valor',
        max_digits=10,
        decimal_places=2
    )

    phone_number = models.CharField(
        'Número que vai autorizar o pagamento',
        max_length=30,
        blank=True
    )

    local_reference = models.CharField(
        'Referência +258 Guest',
        max_length=60,
        unique=True,
        blank=True
    )

    external_reference = models.CharField(
        'Referência do provedor',
        max_length=150,
        blank=True
    )

    checkout_url = models.URLField(
        'URL de checkout',
        blank=True
    )

    provider_response = models.TextField(
        'Resposta do provedor',
        blank=True
    )

    error_message = models.TextField(
        'Mensagem de erro',
        blank=True
    )

    callback_received_at = models.DateTimeField(
        'Callback recebido em',
        null=True,
        blank=True
    )

    paid_at = models.DateTimeField(
        'Pago em',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Transacção de pagamento'
        verbose_name_plural = 'Transacções de pagamento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gateway', 'status']),
            models.Index(fields=['local_reference']),
            models.Index(fields=['external_reference']),
        ]

    def save(self, *args, **kwargs):
        if not self.local_reference:
            self.local_reference = self.generate_local_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_local_reference():
        return f'MZG-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:10].upper()}'

    def mark_paid(self, external_reference='', provider_response=''):
        self.status = 'paid'
        if external_reference:
            self.external_reference = external_reference
        if provider_response:
            self.provider_response = provider_response
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'external_reference', 'provider_response', 'paid_at', 'updated_at'])

        payment = self.payment
        payment.status = 'confirmed'
        payment.payment_method = self.gateway if self.gateway in {'mpesa', 'emola', 'bank_transfer'} else payment.payment_method
        payment.transaction_reference = self.external_reference or self.local_reference
        payment.save(update_fields=['status', 'payment_method', 'transaction_reference', 'platform_commission_amount', 'owner_amount', 'updated_at'])

    def mark_failed(self, error_message=''):
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])

        payment = self.payment
        if payment.status not in {'confirmed', 'submitted'}:
            payment.status = 'failed'
            payment.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f'{self.get_gateway_display()} - {self.local_reference} - {self.get_status_display()}'

class OwnerPayout(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('scheduled', 'Agendada'),
        ('paid', 'Liquidada'),
        ('held', 'Retida'),
        ('cancelled', 'Cancelada'),
    ]

    METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('emola', 'e-Mola'),
        ('bank_transfer', 'Transferência bancária'),
        ('cash', 'Numerário'),
        ('other', 'Outro'),
    ]

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='owner_payout',
        verbose_name='Pagamento do cliente'
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owner_payouts',
        verbose_name='Proprietário'
    )

    gross_amount = models.DecimalField(
        'Valor pago pelo cliente',
        max_digits=10,
        decimal_places=2,
        default=0
    )

    commission_amount = models.DecimalField(
        'Comissão +258 Guest',
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payout_amount = models.DecimalField(
        'Valor líquido a pagar ao proprietário',
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        'Estado da liquidação',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    method = models.CharField(
        'Método de liquidação',
        max_length=30,
        choices=METHOD_CHOICES,
        blank=True
    )

    payout_reference = models.CharField(
        'Referência de liquidação',
        max_length=150,
        blank=True
    )

    payout_phone = models.CharField(
        'Número de pagamento do proprietário',
        max_length=30,
        blank=True
    )

    payout_bank_details = models.TextField(
        'Dados bancários / observações de pagamento',
        blank=True
    )

    admin_notes = models.TextField('Notas administrativas', blank=True)

    scheduled_at = models.DateTimeField('Agendada para', null=True, blank=True)
    paid_at = models.DateTimeField('Liquidada em', null=True, blank=True)

    created_at = models.DateTimeField('Criada em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada em', auto_now=True)

    class Meta:
        verbose_name = 'Liquidação ao proprietário'
        verbose_name_plural = 'Liquidações aos proprietários'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['created_at']),
        ]

    def sync_from_payment(self, save=False):
        self.owner = self.payment.booking.property.owner
        self.gross_amount = self.payment.amount or Decimal('0')
        self.commission_amount = self.payment.platform_commission_amount or Decimal('0')
        self.payout_amount = self.payment.owner_amount or Decimal('0')

        owner_profile = getattr(self.owner, 'owner_profile', None)
        if owner_profile and not self.payout_phone:
            self.payout_phone = owner_profile.payment_phone or ''

        if save:
            self.save()

    def mark_paid(self, method='', reference='', notes=''):
        if method:
            self.method = method
        if reference:
            self.payout_reference = reference
        if notes:
            self.admin_notes = notes
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save(update_fields=['method', 'payout_reference', 'admin_notes', 'status', 'paid_at', 'updated_at'])

    def mark_held(self, notes=''):
        self.status = 'held'
        if notes:
            self.admin_notes = notes
        self.save(update_fields=['status', 'admin_notes', 'updated_at'])

    def __str__(self):
        owner_name = self.owner.get_full_name() or self.owner.username if self.owner else 'Proprietário'
        return f'Liquidação #{self.id} - {owner_name} - {self.get_status_display()}'

