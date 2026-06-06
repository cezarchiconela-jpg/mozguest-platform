from django.utils import timezone

from .models import OwnerPayout
from notifications.services import create_notification, notify_staff
from communications.services import send_system_email
from dashboard.services import log_audit


def ensure_owner_payout_for_payment(payment):
    """Cria ou actualiza a liquidação do proprietário quando a +258 Guest confirma o pagamento do cliente."""
    if not payment or payment.status != 'confirmed':
        return None

    payout, created = OwnerPayout.objects.get_or_create(
        payment=payment,
        defaults={
            'owner': payment.booking.property.owner,
            'gross_amount': payment.amount or 0,
            'commission_amount': payment.platform_commission_amount or 0,
            'payout_amount': payment.owner_amount or 0,
            'status': 'pending',
        }
    )
    payout.sync_from_payment(save=True)

    if created:
        owner = payout.owner
        create_notification(
            owner,
            'Valor disponível para liquidação',
            f'A reserva #{payment.booking.id} foi paga. O valor líquido a receber é {payout.payout_amount} MT, aguardando liquidação pela +258 Guest.',
            notification_type='payment',
            link='/pagamentos/proprietario/liquidacoes/'
        )
        notify_staff(
            'Nova liquidação pendente',
            f'O pagamento da reserva #{payment.booking.id} foi confirmado. Liquidar {payout.payout_amount} MT ao proprietário {owner.username if owner else ""}.',
            notification_type='payment',
            link='/pagamentos/admin/liquidacoes/'
        )

    return payout


def mark_payout_paid(payout, method='', reference='', notes='', actor=None):
    payout.mark_paid(method=method, reference=reference, notes=notes)
    log_audit('payout_paid', actor=actor, target=payout, message='Liquidação marcada como paga.', metadata={'method': method, 'reference': reference, 'amount': str(payout.payout_amount)})

    owner = payout.owner
    payment = payout.payment
    create_notification(
        owner,
        'Liquidação efectuada pela +258 Guest',
        f'A +258 Guest liquidou {payout.payout_amount} MT referente à reserva #{payment.booking.id}.',
        notification_type='payment',
        link='/pagamentos/proprietario/liquidacoes/'
    )
    if owner and owner.email:
        send_system_email(
            owner.email,
            '+258 Guest - liquidação efectuada',
            f'A +258 Guest liquidou {payout.payout_amount} MT referente à reserva #{payment.booking.id}. Referência: {payout.payout_reference or "não informada"}.'
        )

    return payout


def mark_payout_held(payout, notes='', actor=None):
    payout.mark_held(notes=notes)
    log_audit('payout_held', actor=actor, target=payout, message='Liquidação colocada em retenção.', metadata={'notes': notes, 'amount': str(payout.payout_amount)})
    if payout.owner:
        create_notification(
            payout.owner,
            'Liquidação retida temporariamente',
            f'A liquidação referente à reserva #{payout.payment.booking.id} foi colocada em retenção pela +258 Guest. Motivo: {notes or "em análise"}.',
            notification_type='payment',
            link='/pagamentos/proprietario/liquidacoes/'
        )
    return payout
