from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'booking',
        'client',
        'payment_method',
        'amount',
        'platform_commission_amount',
        'owner_amount',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'payment_method',
        'created_at',
    )

    search_fields = (
        'booking__customer_name',
        'booking__property__name',
        'transaction_reference',
    )

    readonly_fields = (
        'platform_commission_amount',
        'owner_amount',
        'created_at',
        'updated_at',
    )
