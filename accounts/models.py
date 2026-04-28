from django.db import models
from django.contrib.auth.models import User


class OwnerProfile(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pendente'),
        ('verified', 'Verificado'),
        ('rejected', 'Rejeitado'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='owner_profile',
        verbose_name='Utilizador'
    )

    business_name = models.CharField('Nome comercial', max_length=200, blank=True)
    document_type = models.CharField('Tipo de documento', max_length=100, blank=True)
    document_number = models.CharField('Número do documento', max_length=100, blank=True)
    nuit = models.CharField('NUIT', max_length=50, blank=True)
    payment_phone = models.CharField('Telefone para pagamentos', max_length=30, blank=True)

    verification_status = models.CharField(
        'Estado de verificação',
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Perfil do Proprietário'
        verbose_name_plural = 'Perfis dos Proprietários'

    def __str__(self):
        return self.business_name or self.user.get_full_name() or self.user.username


class ClientProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name='Utilizador'
    )

    phone = models.CharField('Telefone', max_length=30, blank=True)
    city = models.CharField('Cidade', max_length=100, blank=True)
    neighbourhood = models.CharField('Bairro', max_length=100, blank=True)
    preferred_contact = models.CharField('Contacto preferencial', max_length=50, blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Perfil do Cliente'
        verbose_name_plural = 'Perfis dos Clientes'

    def __str__(self):
        return self.user.get_full_name() or self.user.username
