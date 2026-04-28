from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        'booking',
        'property',
        'client',
        'owner',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'booking__customer_name',
        'property__name',
        'client__username',
        'owner__username',
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'conversation',
        'sender',
        'is_read',
        'created_at',
    )

    list_filter = (
        'is_read',
        'created_at',
    )

    search_fields = (
        'sender__username',
        'text',
    )
