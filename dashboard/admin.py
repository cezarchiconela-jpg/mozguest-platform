from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'target_model', 'target_id', 'target_repr')
    list_filter = ('action', 'target_model', 'created_at')
    search_fields = ('actor__username', 'actor__email', 'target_repr', 'message', 'target_id')
    readonly_fields = ('actor', 'action', 'target_model', 'target_id', 'target_repr', 'message', 'metadata', 'ip_address', 'user_agent', 'created_at')
    ordering = ('-created_at',)
