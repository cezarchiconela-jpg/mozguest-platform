from django.contrib import admin
from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'subject',
        'created_by',
        'category',
        'priority',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'priority',
        'category',
        'created_at',
    )

    search_fields = (
        'subject',
        'description',
        'created_by__username',
        'booking__customer_name',
    )
