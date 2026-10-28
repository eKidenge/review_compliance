from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q

from .models import AuditEvent


@login_required
def audit_log_list(request):
    """
    Displays the immutable system audit log.
    Only accessible by Administrators.
    """
    # Security check: Only Admins can view the full audit log (SRS Section 3)
    if request.user.role != 'ADMIN':
        raise PermissionDenied("Only administrators can view the audit log.")

    # Base queryset
    events = AuditEvent.objects.all().order_by('-timestamp')

    # Search / Filter Logic
    search_query = request.GET.get('q', '').strip()
    action_filter = request.GET.get('action', '').strip()

    if search_query:
        events = events.filter(
            Q(actor__username__icontains=search_query) |
            Q(object_type__icontains=search_query) |
            Q(object_id__icontains=search_query)
        )
    
    if action_filter:
        events = events.filter(action=action_filter)

    # Pagination (50 per page)
    paginator = Paginator(events, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unique actions for the filter dropdown
    unique_actions = AuditEvent.objects.values_list('action', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'action_filter': action_filter,
        'unique_actions': unique_actions,
        'total_events': events.count(),
    }
    
    return render(request, 'audit/log_list.html', context)