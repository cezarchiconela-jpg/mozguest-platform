from django.contrib import admin
from .models import OwnerProfile, ClientProfile


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'business_name',
        'nuit',
        'document_number',
        'payment_phone',
        'kyc_completion_percent',
        'verification_status',
        'created_at',
        'verified_at',
    )

    list_filter = (
        'verification_status',
        'created_at',
        'verified_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'business_name',
        'nuit',
        'document_number',
    )

    readonly_fields = ('kyc_completion_percent', 'verified_at')


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
