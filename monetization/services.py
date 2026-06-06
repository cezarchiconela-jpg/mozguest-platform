from decimal import Decimal

from .models import CommercialPlan, OwnerSubscription

DEFAULT_MAX_PROPERTIES = 1
DEFAULT_MAX_PHOTOS_PER_PROPERTY = 10
DEFAULT_COMMISSION_PERCENTAGE = Decimal('10.00')


def get_active_subscription(owner):
    if not owner or not owner.is_authenticated:
        return None

    return (
        OwnerSubscription.objects
        .select_related('plan')
        .filter(owner=owner, status='active', plan__isnull=False, plan__is_active=True)
        .order_by('-created_at')
        .first()
    )


def get_effective_plan(owner):
    subscription = get_active_subscription(owner)
    if subscription and subscription.plan:
        return subscription.plan

    return (
        CommercialPlan.objects
        .filter(is_active=True, plan_type='free')
        .order_by('monthly_price', 'id')
        .first()
    )


def get_owner_limits(owner):
    plan = get_effective_plan(owner)

    if plan:
        return {
            'plan': plan,
            'max_properties': plan.max_properties,
            'max_photos_per_property': plan.max_photos_per_property,
            'commission_percentage': plan.commission_percentage,
            'can_feature_properties': plan.can_feature_properties,
        }

    return {
        'plan': None,
        'max_properties': DEFAULT_MAX_PROPERTIES,
        'max_photos_per_property': DEFAULT_MAX_PHOTOS_PER_PROPERTY,
        'commission_percentage': DEFAULT_COMMISSION_PERCENTAGE,
        'can_feature_properties': False,
    }


def get_owner_commission_percentage(owner):
    return get_owner_limits(owner)['commission_percentage']
