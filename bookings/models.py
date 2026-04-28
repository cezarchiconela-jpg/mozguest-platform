from django.db import models
from django.contrib.auth.models import User
from properties.models import Property, Room


class Booking(models.Model):
    BOOKING_TYPES = [
        ('hour', 'Por hora'),
        ('day', 'Por dia'),
        ('night', 'Por noite'),
        ('month', 'Mensal'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('accepted', 'Aceite'),
        ('rejected', 'Rejeitada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Concluída'),
    ]

    client = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name='Cliente registado'
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Propriedade'
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Quarto/Unidade'
    )

    customer_name = models.CharField('Nome do cliente', max_length=150)
    customer_phone = models.CharField('Telefone do cliente', max_length=30)
    customer_email = models.EmailField('E-mail do cliente', blank=True)

    booking_type = models.CharField('Tipo de reserva', max_length=20, choices=BOOKING_TYPES)

    checkin_date = models.DateField('Data de entrada')
    checkin_time = models.TimeField('Hora de entrada', null=True, blank=True)

    checkout_date = models.DateField('Data de saída', null=True, blank=True)
    checkout_time = models.TimeField('Hora de saída', null=True, blank=True)

    number_of_guests = models.PositiveIntegerField('Número de pessoas', default=1)

    units_count = models.PositiveIntegerField(
        'Quantidade calculada',
        default=1,
        help_text='Horas, dias, noites ou meses calculados conforme o tipo de reserva.'
    )

    unit_price = models.DecimalField(
        'Preço unitário',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    estimated_amount = models.DecimalField(
        'Valor estimado',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    client_notes = models.TextField('Observações do cliente', blank=True)
    owner_notes = models.TextField('Observações do proprietário', blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.customer_name} - {self.property.name} - {self.get_status_display()}'

class AvailabilityBlock(models.Model):
    REASON_CHOICES = [
        ('maintenance', 'Manutenção'),
        ('external_booking', 'Reserva externa'),
        ('owner_block', 'Bloqueio do proprietário'),
        ('other', 'Outro motivo'),
    ]

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='availability_blocks',
        verbose_name='Quarto/Unidade'
    )

    start_datetime = models.DateTimeField('Início do bloqueio')
    end_datetime = models.DateTimeField('Fim do bloqueio')

    reason = models.CharField(
        'Motivo',
        max_length=30,
        choices=REASON_CHOICES,
        default='owner_block'
    )

    notes = models.TextField('Observações', blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Criado por'
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Bloqueio de disponibilidade'
        verbose_name_plural = 'Bloqueios de disponibilidade'
        ordering = ['-start_datetime']

    def __str__(self):
        return f'{self.room.name} - {self.start_datetime} até {self.end_datetime}'
