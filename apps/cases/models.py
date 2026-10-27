from django.db import models
from django.conf import settings
from apps.imports.models import ImportBatch
from django.core.exceptions import ValidationError

class ReviewCase(models.Model):
    STATUS_CHOICES = [
        ('NEEDS_TRIAGE', 'Needs Triage'),
        ('NOT_ELIGIBLE', 'Not Eligible'),
        ('INSUFFICIENT_EVIDENCE', 'Insufficient Evidence'),
        ('ELIGIBLE', 'Eligible'),
        ('APPROVED', 'Approved'),
        ('REPORT_RECEIVED', 'Report Received'),
        ('REMOVED', 'Review Removed'),
        ('RETAINED', 'Review Retained'),
    ]
    canonical_url = models.URLField(unique=True, db_index=True)
    original_url = models.URLField()
    business_label = models.CharField(max_length=255, blank=True, null=True)
    source_batch = models.ForeignKey(ImportBatch, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='NEEDS_TRIAGE', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("can_triage", "Can triage cases"),
            ("can_approve", "Can approve cases"),
            ("can_submit", "Can submit reports"),
        ]

    def __str__(self):
        return f"{self.business_label or 'Review'} - {self.get_status_display()}"

    def clean(self):
        # Prevent status regression
        if self.pk:
            old_instance = ReviewCase.objects.get(pk=self.pk)
            if old_instance.status == 'APPROVED' and self.status == 'NEEDS_TRIAGE':
                raise ValidationError("Cannot revert an approved case to Needs Triage.")

class PolicyAssessment(models.Model):
    case = models.OneToOneField(ReviewCase, on_delete=models.CASCADE, related_name='assessment')
    category = models.CharField(max_length=100)
    rationale = models.TextField()
    decision = models.CharField(max_length=50) 
    assessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    assessed_at = models.DateTimeField(auto_now=True)

class Approval(models.Model):
    case = models.OneToOneField(ReviewCase, on_delete=models.CASCADE, related_name='approval')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision = models.BooleanField()
    rationale = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class SubmissionAttempt(models.Model):
    case = models.ForeignKey(ReviewCase, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    submitted_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=100)
    receipt_reference = models.CharField(max_length=255)
    result = models.CharField(max_length=50)
    error_summary = models.TextField(blank=True, null=True)

class Outcome(models.Model):
    case = models.ForeignKey(ReviewCase, on_delete=models.CASCADE, related_name='outcomes')
    outcome_type = models.CharField(max_length=50)
    source = models.CharField(max_length=100)
    observed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)