from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment
from .services import ensure_owner_payout_for_payment


@receiver(post_save, sender=Payment)
def create_owner_payout_when_payment_confirmed(sender, instance, **kwargs):
    if instance.status == 'confirmed':
        ensure_owner_payout_for_payment(instance)
