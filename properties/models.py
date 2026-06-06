from django.db import models
from django.contrib.auth.models import User


class Property(models.Model):
    PROPERTY_TYPES = [
        ('guest_house', 'Guest House'),
        ('room', 'Quarto'),
        ('apartment', 'Apartamento'),
        ('residence', 'Residência'),
        ('lodge', 'Pousada'),
        ('other', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('suspended', 'Suspenso'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties', verbose_name='Proprietário')
    name = models.CharField('Nome do estabelecimento', max_length=200)
    property_type = models.CharField('Tipo de alojamento', max_length=50, choices=PROPERTY_TYPES)
    description = models.TextField('Descrição')
    province = models.CharField('Província', max_length=100, blank=True)
    city = models.CharField('Cidade', max_length=100)
    district = models.CharField('Distrito', max_length=100, blank=True)
    neighbourhood = models.CharField('Bairro', max_length=100, blank=True)
    address_reference = models.CharField('Referência de localização', max_length=255, blank=True)
    latitude = models.DecimalField('Latitude', max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField('Longitude', max_digits=10, decimal_places=7, null=True, blank=True)
    phone = models.CharField('Telefone', max_length=30, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=30, blank=True)
    email = models.EmailField('E-mail', blank=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified = models.BooleanField('Verificado', default=False)
    is_featured = models.BooleanField('Em destaque', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Propriedade'
        verbose_name_plural = 'Propriedades'
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.name


class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Quarto Individual'),
        ('double', 'Quarto de Casal'),
        ('suite', 'Suíte'),
        ('apartment', 'Apartamento'),
        ('studio', 'Estúdio'),
        ('house', 'Casa'),
        ('other', 'Outro'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rooms', verbose_name='Propriedade')
    name = models.CharField('Nome do quarto/unidade', max_length=150)
    room_type = models.CharField('Tipo de unidade', max_length=50, choices=ROOM_TYPES)
    description = models.TextField('Descrição', blank=True)
    capacity = models.PositiveIntegerField('Capacidade de pessoas', default=1)
    price_hour = models.DecimalField('Preço por hora', max_digits=10, decimal_places=2, null=True, blank=True)
    price_day = models.DecimalField('Preço por dia', max_digits=10, decimal_places=2, null=True, blank=True)
    price_night = models.DecimalField('Preço por noite', max_digits=10, decimal_places=2, null=True, blank=True)
    price_month = models.DecimalField('Preço mensal', max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_hours = models.PositiveIntegerField('Mínimo de horas', default=1)
    has_private_bathroom = models.BooleanField('Casa de banho privativa', default=False)
    has_ac = models.BooleanField('Ar condicionado', default=False)
    has_wifi = models.BooleanField('Wi-Fi', default=False)
    has_parking = models.BooleanField('Estacionamento', default=False)
    is_available = models.BooleanField('Disponível', default=True)
    status = models.CharField('Estado', max_length=20, default='active')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Quarto/Unidade'
        verbose_name_plural = 'Quartos/Unidades'
        ordering = ['property', 'name']

    def __str__(self):
        return f'{self.property.name} - {self.name}'


class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos', verbose_name='Propriedade')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='photos', verbose_name='Quarto/Unidade', null=True, blank=True)
    image = models.ImageField('Imagem', upload_to='properties/')
    caption = models.CharField('Legenda', max_length=200, blank=True)
    is_main = models.BooleanField('Imagem principal', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Fotografia'
        verbose_name_plural = 'Fotografias'
        ordering = ['-is_main', '-created_at']

    def __str__(self):
        return f'Foto - {self.property.name}'
