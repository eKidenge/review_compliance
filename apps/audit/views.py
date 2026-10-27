from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import AuditEvent

@login_required
def audit_log_list(request):
    # Only Admins can view the full audit log (Section 3)
    if request.user.role != 'ADMIN':
        raise PermissionDenied
        
    events = AuditEvent.objects.all().order_by('-timestamp')
    
    # Basic pagination
    from django.core.paginator import Paginator
    paginator = Paginator(events, 50) # Show 50 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'audit/log_list.html', {'page_obj': page_obj})