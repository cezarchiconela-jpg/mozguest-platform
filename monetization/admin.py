from django.contrib import admin
from .models import CommercialPlan, OwnerSubscription


@admin.register(CommercialPlan)
class CommercialPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'plan_type',
        'monthly_price',
        'commission_percentage',
        'max_properties',
        'can_feature_properties',
        'priority_support',
        'is_active',
    )

    list_filter = (
        'plan_type',
        'is_active',
        'can_feature_properties',
        'priority_support',
    )


@admin.register(OwnerSubscription)
class OwnerSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'plan',
        'status',
        'start_date',
        'end_date',
        'created_at',
    )

    list_filter = (
        'status',
        'plan',
        'created_at',
    )

    search_fields = (
        'owner__username',
        'owner__email',
        'plan__name',
    )
