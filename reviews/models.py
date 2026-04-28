from django.db import models
from django.contrib.auth.models import User
from properties.models import Property
from builtins import property as builtin_property


class Review(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovada'),
        ('rejected', 'Rejeitada'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Propriedade'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name='Utilizador'
    )

    customer_name = models.CharField(
        'Nome do cliente',
        max_length=150
    )

    rating = models.PositiveSmallIntegerField(
        'Avaliação geral',
        default=5
    )

    cleanliness_rating = models.PositiveSmallIntegerField(
        'Limpeza',
        default=5
    )

    security_rating = models.PositiveSmallIntegerField(
        'Segurança',
        default=5
    )

    location_rating = models.PositiveSmallIntegerField(
        'Localização',
        default=5
    )

    comfort_rating = models.PositiveSmallIntegerField(
        'Conforto',
        default=5
    )

    service_rating = models.PositiveSmallIntegerField(
        'Atendimento',
        default=5
    )

    value_rating = models.PositiveSmallIntegerField(
        'Preço/qualidade',
        default=5
    )

    comment = models.TextField(
        'Comentário',
        blank=True
    )

    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        'Actualizado em',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['property', 'user'],
                name='unique_review_per_user_property'
            )
        ]

    def __str__(self):
        return f'{self.property.name} - {self.rating} estrelas'

    @builtin_property
    def advanced_average(self):
        values = [
            self.rating,
            self.cleanliness_rating,
            self.security_rating,
            self.location_rating,
            self.comfort_rating,
            self.service_rating,
            self.value_rating,
        ]

        valid_values = [value for value in values if value]

        if not valid_values:
            return 0

        return round(sum(valid_values) / len(valid_values), 1)


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Utilizador'
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Propriedade'
    )

    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = ('user', 'property')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.property.name}'
