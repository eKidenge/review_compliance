from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q

from .models import ReviewCase, PolicyAssessment, Approval, SubmissionAttempt
from .forms import AssessmentForm, ApprovalForm, SubmissionForm
from apps.audit.models import AuditEvent
from apps.accounts.decorators import role_required


@login_required
def case_list(request):
    """
    List all cases. Read-only clients can view, but advanced filters might be hidden.
    """
    if not request.user.can_view_case():
        raise PermissionDenied("You do not have permission to view cases.")

    queryset = ReviewCase.objects.all().order_by('-created_at')
    
    # Filtering Logic
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search_query:
        queryset = queryset.filter(
            Q(canonical_url__icontains=search_query) | 
            Q(business_label__icontains=search_query)
        )
        
    # Pagination
    paginator = Paginator(queryset, 25) # Show 25 cases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'cases': page_obj,
        'page_obj': page_obj,           # Passes pagination data to the template
        'total_count': queryset.count(), # Fixes the "0 Total Cases" bug
        'current_filter': status_filter,
        'search_query': search_query,
        'status_choices': ReviewCase.STATUS_CHOICES
    }
    return render(request, 'cases/list.html', context)


@login_required
def case_detail(request, pk):
    """
    View details of a single case, including its assessment, approval, and submission history.
    """
    if not request.user.can_view_case():
        raise PermissionDenied("You do not have permission to view this case.")

    case = get_object_or_404(ReviewCase, pk=pk)
    
    # Instantiate forms for the template if the user has the right role
    assessment_form = AssessmentForm() if request.user.is_reviewer() else None
    approval_form = ApprovalForm() if request.user.is_admin() else None
    submission_form = SubmissionForm() if request.user.is_submitter() else None

    context = {
        'case': case,
        'assessment_form': assessment_form,
        'approval_form': approval_form,
        'submission_form': submission_form,
    }
    return render(request, 'cases/detail.html', context)


@role_required(['ADMIN', 'REVIEWER'])
@transaction.atomic
def submit_assessment(request, pk):
    """
    Reviewers assess the case. This transitions the case to ELIGIBLE or NOT_ELIGIBLE.
    """
    case = get_object_or_404(ReviewCase, pk=pk)
    
    # Prevent overwriting an existing assessment
    if hasattr(case, 'assessment'):
        messages.error(request, "An assessment already exists for this case.")
        return redirect('cases:case_detail', pk=pk)
        
    if case.status != 'NEEDS_TRIAGE':
        messages.error(request, "This case is not in the triage state.")
        return redirect('cases:case_detail', pk=pk)

    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.case = case
            assessment.assessed_by = request.user
            assessment.save()
            
            # Update case status based on decision
            if assessment.decision == 'ELIGIBLE':
                case.status = 'ELIGIBLE'
            else:
                case.status = 'NOT_ELIGIBLE'
            case.save()

            # Audit Log
            AuditEvent.objects.create(
                actor=request.user, 
                object_type='ReviewCase', 
                object_id=str(case.id),
                action='ASSESSMENT_ADDED', 
                after_json={'status': case.status, 'decision': assessment.decision}
            )
            messages.success(request, f"Assessment saved. Case marked as {case.get_status_display()}.")
            return redirect('cases:case_detail', pk=pk)
        else:
            messages.error(request, "There was an error with your assessment form. Please check the fields.")
    return redirect('cases:case_detail', pk=pk)


@role_required(['ADMIN'])
@transaction.atomic
def approve_case(request, pk):
    """
    Only Admins can approve a case that has been marked ELIGIBLE.
    """
    case = get_object_or_404(ReviewCase, pk=pk)
    
    if case.status != 'ELIGIBLE':
        messages.error(request, "Only cases marked as Eligible can be approved.")
        return redirect('cases:case_detail', pk=pk)
        
    if hasattr(case, 'approval'):
        messages.error(request, "This case has already been approved.")
        return redirect('cases:case_detail', pk=pk)

    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.case = case
            approval.approved_by = request.user
            approval.decision = True
            approval.save()
            
            case.status = 'APPROVED'
            case.save()
            
            AuditEvent.objects.create(
                actor=request.user, 
                object_type='ReviewCase', 
                object_id=str(case.id),
                action='APPROVED'
            )
            messages.success(request, "Case successfully approved for submission.")
        else:
            messages.error(request, "There was an error with the approval form.")
    return redirect('cases:case_detail', pk=pk)


@role_required(['ADMIN', 'SUBMITTER'])
@transaction.atomic
def record_submission(request, pk):
    """
    Submitters record the receipt of a manual submission. 
    Transitions case to REPORT_RECEIVED.
    """
    case = get_object_or_404(ReviewCase, pk=pk)
    
    if case.status != 'APPROVED':
        messages.error(request, "Only approved cases can be submitted.")
        return redirect('cases:case_detail', pk=pk)

    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.case = case
            submission.submitted_by = request.user
            submission.save()
            
            case.status = 'REPORT_RECEIVED'
            case.save()
            
            AuditEvent.objects.create(
                actor=request.user, 
                object_type='ReviewCase', 
                object_id=str(case.id),
                action='SUBMITTED', 
                after_json={'receipt': submission.receipt_reference}
            )
            messages.success(request, "Submission recorded successfully.")
        else:
            messages.error(request, "There was an error recording the submission.")
    return redirect('cases:case_detail', pk=pk)