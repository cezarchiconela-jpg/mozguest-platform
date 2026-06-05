from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



class OwnerProfile(models.Model):
    VERIFICATION_STATUS = [
        ('unverified', 'Não verificado'),
        ('pending', 'Pendente'),
        ('in_review', 'Em análise'),
        ('verified', 'Verificado'),
        ('rejected', 'Rejeitado'),
        ('suspended', 'Suspenso'),
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
    payout_bank_details = models.TextField('Dados bancários para liquidação', blank=True)
    payout_emola_phone = models.CharField('Número e-Mola para liquidação', max_length=30, blank=True)
    payout_mpesa_phone = models.CharField('Número M-Pesa para liquidação', max_length=30, blank=True)

    identity_document = models.FileField('Documento de identificação', upload_to='kyc/owners/', null=True, blank=True)
    nuit_document = models.FileField('Comprovativo de NUIT', upload_to='kyc/owners/', null=True, blank=True)
    ownership_proof = models.FileField('Comprovativo de titularidade/autorização do alojamento', upload_to='kyc/owners/', null=True, blank=True)
    verification_notes = models.TextField('Notas de verificação', blank=True)
    verified_at = models.DateTimeField('Verificado em', null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_owner_profiles', verbose_name='Verificado por')

    verification_status = models.CharField(
        'Estado de verificação',
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='unverified'
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Perfil do Proprietário'
        verbose_name_plural = 'Perfis dos Proprietários'

    @property
    def is_verified(self):
        return self.verification_status == 'verified'

    @property
    def kyc_completion_percent(self):
        checks = [
            bool(self.business_name),
            bool(self.document_type),
            bool(self.document_number),
            bool(self.nuit),
            bool(self.payment_phone or self.payout_mpesa_phone or self.payout_emola_phone or self.payout_bank_details),
            bool(self.identity_document),
            bool(self.ownership_proof),
        ]
        return int((sum(checks) / len(checks)) * 100) if checks else 0

    def mark_verified(self, user=None, notes=''):
        self.verification_status = 'verified'
        self.verified_at = timezone.now()
        if user is not None:
            self.verified_by = user
        if notes:
            self.verification_notes = notes
        self.save(update_fields=['verification_status', 'verified_at', 'verified_by', 'verification_notes', 'updated_at'])

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
