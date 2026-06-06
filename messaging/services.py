from .models import Conversation


def get_or_create_conversation(booking):
    conversation, created = Conversation.objects.get_or_create(
        booking=booking,
        defaults={
            'property': booking.property,
            'client': booking.client,
            'owner': booking.property.owner,
        }
    )

    return conversation
