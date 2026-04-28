from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from bookings.models import Booking
from properties.models import Property
from reviews.models import Review
from payments.models import Payment

from .services import create_notification, notify_staff


def get_old_status(instance):
    if not instance.pk:
        return None

    try:
        old_instance = instance.__class__.objects.get(pk=instance.pk)
        return getattr(old_instance, 'status', None)
    except instance.__class__.DoesNotExist:
        return None


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    instance._old_status = get_old_status(instance)


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    booking = instance

    if created:
        create_notification(
            recipient=booking.property.owner,
            title='Nova reserva recebida',
            message=f'Recebeu uma nova reserva para {booking.property.name}, quarto/unidade {booking.room.name}.',
            notification_type='booking',
            link='/reservas/proprietario/reservas/'
        )

        if booking.client:
            create_notification(
                recipient=booking.client,
                title='Reserva enviada',
                message=f'O seu pedido de reserva para {booking.property.name} foi enviado e está pendente de confirmação.',
                notification_type='booking',
                link='/reservas/cliente/minhas-reservas/'
            )

        return

    old_status = getattr(instance, '_old_status', None)

    if old_status and old_status != booking.status:
        if booking.client:
            status_label = booking.get_status_display()

            create_notification(
                recipient=booking.client,
                title=f'Reserva {status_label}',
                message=f'A sua reserva para {booking.property.name}, quarto/unidade {booking.room.name}, foi actualizada para: {status_label}.',
                notification_type='booking',
                link='/reservas/cliente/minhas-reservas/'
            )

        create_notification(
            recipient=booking.property.owner,
            title='Estado da reserva actualizado',
            message=f'A reserva de {booking.customer_name} para {booking.property.name} está agora como {booking.get_status_display()}.',
            notification_type='booking',
            link='/reservas/proprietario/reservas/'
        )


@receiver(pre_save, sender=Property)
def property_pre_save(sender, instance, **kwargs):
    instance._old_status = get_old_status(instance)


@receiver(post_save, sender=Property)
def property_post_save(sender, instance, created, **kwargs):
    property_obj = instance

    if created:
        notify_staff(
            title='Nova propriedade pendente',
            message=f'A propriedade {property_obj.name} foi cadastrada e aguarda aprovação.',
            notification_type='property',
            link='/moz-admin/propriedades/'
        )

        create_notification(
            recipient=property_obj.owner,
            title='Propriedade enviada para aprovação',
            message=f'A sua propriedade {property_obj.name} foi cadastrada e aguarda aprovação da MozGuest.',
            notification_type='property',
            link='/proprietario/propriedades/'
        )

        return

    old_status = getattr(instance, '_old_status', None)

    if old_status and old_status != property_obj.status:
        create_notification(
            recipient=property_obj.owner,
            title='Estado da propriedade actualizado',
            message=f'A propriedade {property_obj.name} foi actualizada para: {property_obj.get_status_display()}.',
            notification_type='property',
            link='/proprietario/propriedades/'
        )


@receiver(pre_save, sender=Review)
def review_pre_save(sender, instance, **kwargs):
    instance._old_status = get_old_status(instance)


@receiver(post_save, sender=Review)
def review_post_save(sender, instance, created, **kwargs):
    review = instance

    if created:
        notify_staff(
            title='Nova avaliação pendente',
            message=f'Nova avaliação para {review.property.name} aguarda aprovação.',
            notification_type='review',
            link='/moz-admin/avaliacoes/'
        )

        create_notification(
            recipient=review.property.owner,
            title='Nova avaliação recebida',
            message=f'O alojamento {review.property.name} recebeu uma nova avaliação, aguardando aprovação.',
            notification_type='review',
            link='/proprietario/propriedades/'
        )

        return

    old_status = getattr(instance, '_old_status', None)

    if old_status and old_status != review.status:
        if review.user:
            create_notification(
                recipient=review.user,
                title='Estado da avaliação actualizado',
                message=f'A sua avaliação para {review.property.name} foi actualizada para: {review.get_status_display()}.',
                notification_type='review',
                link=f'/properties/{review.property.id}/'
            )


@receiver(pre_save, sender=Payment)
def payment_pre_save(sender, instance, **kwargs):
    instance._old_status = get_old_status(instance)


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    payment = instance

    if created:
        return

    old_status = getattr(instance, '_old_status', None)

    if old_status and old_status != payment.status:
        if payment.status == 'submitted':
            notify_staff(
                title='Pagamento pendente de confirmação',
                message=f'O cliente enviou comprovativo para a reserva #{payment.booking.id}.',
                notification_type='payment',
                link='/moz-admin/pagamentos/'
            )

            create_notification(
                recipient=payment.booking.property.owner,
                title='Pagamento enviado pelo cliente',
                message=f'O cliente enviou comprovativo de pagamento para {payment.booking.property.name}.',
                notification_type='payment',
                link='/pagamentos/proprietario/pagamentos/'
            )

        if payment.client:
            create_notification(
                recipient=payment.client,
                title='Estado do pagamento actualizado',
                message=f'O pagamento da reserva #{payment.booking.id} está agora como: {payment.get_status_display()}.',
                notification_type='payment',
                link='/reservas/cliente/minhas-reservas/'
            )

        create_notification(
            recipient=payment.booking.property.owner,
            title='Estado do pagamento actualizado',
            message=f'O pagamento da reserva #{payment.booking.id} está agora como: {payment.get_status_display()}.',
            notification_type='payment',
            link='/pagamentos/proprietario/pagamentos/'
        )
