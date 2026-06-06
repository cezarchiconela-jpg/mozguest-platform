from django.contrib import admin
from .models import Payment, PaymentTransaction, OwnerPayout


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = (
        'gateway',
        'status',
        'amount',
        'phone_number',
        'local_reference',
        'external_reference',
        'created_at',
        'updated_at',
        'paid_at',
    )
    can_delete = False


class OwnerPayoutInline(admin.StackedInline):
    model = OwnerPayout
    extra = 0
    readonly_fields = (
        'gross_amount',
        'commission_amount',
        'payout_amount',
        'created_at',
        'updated_at',
        'paid_at',
    )
    can_delete = False


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

    inlines = [PaymentTransactionInline, OwnerPayoutInline]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'local_reference',
        'gateway',
        'status',
        'amount',
        'phone_number',
        'external_reference',
        'created_at',
        'paid_at',
    )
    list_filter = ('gateway', 'status', 'created_at')
    search_fields = (
        'local_reference',
        'external_reference',
        'phone_number',
        'payment__booking__customer_name',
        'payment__booking__property__name',
    )
    readonly_fields = (
        'local_reference',
        'provider_response',
        'error_message',
        'callback_received_at',
        'created_at',
        'updated_at',
        'paid_at',
    )


@admin.register(OwnerPayout)
class OwnerPayoutAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'owner',
        'payment',
        'payout_amount',
        'status',
        'method',
        'payout_reference',
        'created_at',
        'paid_at',
    )
    list_filter = ('status', 'method', 'created_at', 'paid_at')
    search_fields = (
        'owner__username',
        'owner__email',
        'payment__booking__customer_name',
        'payment__booking__property__name',
        'payout_reference',
    )
    readonly_fields = (
        'gross_amount',
        'commission_amount',
        'payout_amount',
        'created_at',
        'updated_at',
        'paid_at',
    )
