from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from audit.models import AuditLog


@login_required
def audit_log_list(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admins only.')
        return redirect('users:dashboard')

    action = request.GET.get('action', '').strip()
    query = request.GET.get('q', '').strip()

    logs = AuditLog.objects.all().order_by('-created_at')
    if action:
        logs = logs.filter(action=action)
    if query:
        logs = logs.filter(
            Q(description__icontains=query)
            | Q(actor_email__icontains=query)
            | Q(model_name__icontains=query)
            | Q(object_repr__icontains=query)
        )

    return render(
        request,
        'audit/audit_log_list.html',
        {
            'logs': logs[:300],
            'actions': AuditLog.ACTION_CHOICES,
            'selected_action': action,
            'query': query,
        },
    )
