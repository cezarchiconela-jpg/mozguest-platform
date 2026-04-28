from django.contrib import admin
from .models import OwnerProfile, ClientProfile


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'business_name',
        'nuit',
        'payment_phone',
        'verification_status',
        'created_at',
    )

    list_filter = (
        'verification_status',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'business_name',
        'nuit',
    )


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone',
        'city',
        'neighbourhood',
        'preferred_contact',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'phone',
        'city',
        'neighbourhood',
    )

    list_filter = (
        'city',
        'created_at',
    )
