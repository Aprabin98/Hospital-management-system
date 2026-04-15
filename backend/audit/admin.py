from django.contrib import admin

from audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at',
        'action',
        'actor_email',
        'actor_role',
        'model_name',
        'object_id',
        'ip_address',
    ]
    list_filter = ['action', 'actor_role', 'model_name', 'created_at']
    search_fields = ['actor_email', 'description', 'object_repr', 'ip_address', 'path']
    ordering = ['-created_at']
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
