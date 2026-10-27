from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.cases.models import ReviewCase, SubmissionAttempt
from apps.imports.models import ImportBatch
from apps.accounts.models import CustomUser
from apps.audit.models import AuditEvent

@login_required
def dashboard_view(request):
    """
    Role-based routing for the dashboard.
    """
    role = request.user.role
    
    if role == 'ADMIN':
        return render(request, 'dashboard/admin_dashboard.html', get_admin_context())
    elif role == 'REVIEWER':
        return render(request, 'dashboard/reviewer_dashboard.html', get_reviewer_context(request))
    elif role == 'SUBMITTER':
        return render(request, 'dashboard/submitter_dashboard.html', get_submitter_context(request))
    elif role == 'CLIENT':
        return render(request, 'dashboard/client_dashboard.html', get_client_context())
    
    # Fallback if role is not recognized
    return render(request, 'dashboard/client_dashboard.html', get_client_context())


# ==========================================
# CONTEXT GENERATORS (Data Fetching Logic)
# ==========================================

def get_admin_context():
    """High-level system metrics, user counts, and recent audit logs."""
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    return {
        'total_users': CustomUser.objects.count(),
        'total_cases': ReviewCase.objects.count(),
        'total_imports': ImportBatch.objects.count(),
        'status_counts': ReviewCase.objects.values('status').annotate(count=Count('id')),
        'recent_audit_logs': AuditEvent.objects.order_by('-timestamp')[:10],
        'recent_imports': ImportBatch.objects.order_by('-imported_at')[:5],
        'system_health': {
            'active_users': CustomUser.objects.filter(is_active=True).count(),
            'new_users_week': CustomUser.objects.filter(created_at__gte=seven_days_ago).count(),
        }
    }

def get_reviewer_context(request):
    """Focuses on the triage queue and assessment metrics."""
    return {
        'needs_triage_count': ReviewCase.objects.filter(status='NEEDS_TRIAGE').count(),
        'my_assessments_count': ReviewCase.objects.filter(assessment__assessed_by=request.user).count(),
        'assigned_queue': ReviewCase.objects.filter(status='NEEDS_TRIAGE').order_by('created_at')[:10],
        'recently_assessed': ReviewCase.objects.filter(
            assessment__assessed_by=request.user
        ).order_by('-assessment__assessed_at')[:5]
    }

def get_submitter_context(request):
    """Focuses on approved cases waiting for manual submission."""
    return {
        'ready_for_submission_count': ReviewCase.objects.filter(status='APPROVED').count(),
        'my_submissions_count': SubmissionAttempt.objects.filter(submitted_by=request.user).count(),
        'submission_queue': ReviewCase.objects.filter(status='APPROVED').order_by('updated_at')[:15],
        'recent_submissions': SubmissionAttempt.objects.filter(
            submitted_by=request.user
        ).order_by('-submitted_at')[:5]
    }

def get_client_context():
    """High-level, sanitized overview of outcomes without internal workflow clutter."""
    total = ReviewCase.objects.count()
    removed = ReviewCase.objects.filter(status='REMOVED').count()
    retained = ReviewCase.objects.filter(status='RETAINED').count()
    reported = ReviewCase.objects.filter(status='REPORT_RECEIVED').count()
    
    return {
        'total_submitted': reported,
        'total_removed': removed,
        'total_retained': retained,
        'success_rate': round((removed / total * 100), 2) if total > 0 else 0,
        'status_counts': ReviewCase.objects.values('status').annotate(count=Count('id')),
    }


def error_403(request, exception):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)