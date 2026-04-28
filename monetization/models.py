from django.db import models
from django.contrib.auth.models import User


class CommercialPlan(models.Model):
    PLAN_TYPES = [
        ('free', 'Gratuito'),
        ('featured', 'Destaque'),
        ('premium', 'Premium'),
    ]

    name = models.CharField('Nome do plano', max_length=100)
    plan_type = models.CharField('Tipo', max_length=30, choices=PLAN_TYPES, default='free')
    monthly_price = models.DecimalField('Preço mensal', max_digits=12, decimal_places=2, default=0)
    commission_percentage = models.DecimalField('Comissão (%)', max_digits=5, decimal_places=2, default=10)
    max_properties = models.PositiveIntegerField('Máximo de propriedades', default=1)
    max_photos_per_property = models.PositiveIntegerField('Máximo de fotos por propriedade', default=10)
    can_feature_properties = models.BooleanField('Pode destacar propriedades', default=False)
    priority_support = models.BooleanField('Suporte prioritário', default=False)
    description = models.TextField('Descrição', blank=True)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Plano comercial'
        verbose_name_plural = 'Planos comerciais'
        ordering = ['monthly_price']

    def __str__(self):
        return self.name


class OwnerSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('pending', 'Pendente'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Proprietário'
    )

    plan = models.ForeignKey(
        CommercialPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscriptions',
        verbose_name='Plano'
    )

    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField('Data de início', null=True, blank=True)
    end_date = models.DateField('Data de fim', null=True, blank=True)
    notes = models.TextField('Notas administrativas', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Subscrição do proprietário'
        verbose_name_plural = 'Subscrições dos proprietários'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.owner.username} - {self.plan}'
