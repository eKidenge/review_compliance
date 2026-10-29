
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.imports.models import ImportBatch


class ReviewCase(models.Model):
    STATUS_CHOICES = [
        ("NEEDS_TRIAGE", "Needs Triage"),
        ("NOT_ELIGIBLE", "Not Eligible"),
        ("INSUFFICIENT_EVIDENCE", "Insufficient Evidence"),
        ("ELIGIBLE", "Eligible"),
        ("APPROVED", "Approved"),
        ("REPORT_RECEIVED", "Report Received"),
        ("REMOVED", "Review Removed"),
        ("RETAINED", "Review Retained"),
    ]

    canonical_url = models.URLField(unique=True, db_index=True)
    original_url = models.URLField()
    business_label = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    source_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cases",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="NEEDS_TRIAGE",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Review Case"
        verbose_name_plural = "Review Cases"
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        permissions = [
            ("can_triage", "Can triage cases"),
            ("can_approve", "Can approve cases"),
            ("can_submit", "Can submit reports"),
        ]

    def __str__(self):
        return (
            f"Case #{self.id} | "
            f"{self.business_label or 'Unknown Business'} | "
            f"{self.get_status_display()}"
        )

    def clean(self):
        """
        Validate permitted status transitions.

        This validation runs when full_clean() is called.
        Django does not automatically call clean() on every save().
        """
        super().clean()

        if not self.pk:
            return

        old_instance = (
            ReviewCase.objects
            .filter(pk=self.pk)
            .only("status")
            .first()
        )

        if old_instance is None:
            return

        if (
            old_instance.status == "APPROVED"
            and self.status == "NEEDS_TRIAGE"
        ):
            raise ValidationError(
                "Cannot revert an approved case to Needs Triage."
            )

        if (
            old_instance.status == "REMOVED"
            and self.status != "REMOVED"
        ):
            raise ValidationError(
                "A case marked as Removed cannot be reopened."
            )

    @property
    def is_ready_for_submission(self):
        """Return whether the case has been approved for submission."""
        return self.status == "APPROVED"

    @property
    def has_active_report(self):
        """Return whether a report has been received or has an outcome."""
        return self.status in [
            "REPORT_RECEIVED",
            "REMOVED",
            "RETAINED",
        ]


class PolicyAssessment(models.Model):
    CATEGORY_CHOICES = [
        ("SPAM", "Spam or Misleading Content"),
        ("FAKE_ENGAGEMENT", "Fake Engagement or Bot Activity"),
        ("CONFLICT_OF_INTEREST", "Conflict of Interest"),
        ("OFF_TOPIC", "Off-Topic or Irrelevant Content"),
        ("PROFANITY", "Profanity or Hate Speech"),
        ("PERSONAL_INFO", "Contains Personal Information"),
        ("ILLEGAL_CONTENT", "Illegal or Restricted Content"),
        ("OTHER", "Other Policy Violation"),
    ]

    DECISION_CHOICES = [
        ("ELIGIBLE", "Eligible - Violation Confirmed"),
        ("NOT_ELIGIBLE", "Not Eligible - No Violation Found"),
        (
            "INSUFFICIENT_EVIDENCE",
            "Insufficient Evidence - Needs More Proof",
        ),
    ]

    case = models.OneToOneField(
        ReviewCase,
        on_delete=models.CASCADE,
        related_name="assessment",
    )
    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
    )
    rationale = models.TextField()
    decision = models.CharField(
        max_length=50,
        choices=DECISION_CHOICES,
    )
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    assessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Policy Assessment"
        verbose_name_plural = "Policy Assessments"

    def __str__(self):
        return (
            f"Assessment for Case #{self.case_id} - "
            f"{self.get_decision_display()}"
        )


class Approval(models.Model):
    case = models.OneToOneField(
        ReviewCase,
        on_delete=models.CASCADE,
        related_name="approval",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approvals_given",
    )
    decision = models.BooleanField()  # True = approved, False = rejected
    rationale = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Approval"
        verbose_name_plural = "Approvals"

    def __str__(self):
        decision_text = "Approved" if self.decision else "Rejected"
        return f"Approval for Case #{self.case_id} - {decision_text}"


class SubmissionAttempt(models.Model):
    RESULT_CHOICES = [
        ("SUCCESS", "Success - Report Received"),
        ("FAILED", "Failed - Platform Rejected"),
        ("ERROR", "Error - Technical Issue"),
    ]

    case = models.ForeignKey(
        ReviewCase,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=100)
    receipt_reference = models.CharField(max_length=255)
    result = models.CharField(
        max_length=50,
        choices=RESULT_CHOICES,
    )
    error_summary = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Submission Attempt"
        verbose_name_plural = "Submission Attempts"

    def __str__(self):
        return (
            f"Submission for Case #{self.case_id} - "
            f"{self.get_result_display()}"
        )


class Outcome(models.Model):
    OUTCOME_CHOICES = [
        ("REMOVED", "Review Removed"),
        ("RETAINED", "Review Retained"),
        ("UNKNOWN", "Outcome Unknown"),
    ]

    case = models.ForeignKey(
        ReviewCase,
        on_delete=models.CASCADE,
        related_name="outcomes",
    )
    outcome_type = models.CharField(
        max_length=50,
        choices=OUTCOME_CHOICES,
    )
    source = models.CharField(max_length=100)
    observed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-observed_at"]
        verbose_name = "Outcome"
        verbose_name_plural = "Outcomes"

    def __str__(self):
        return (
            f"Outcome for Case #{self.case_id} - "
            f"{self.get_outcome_type_display()}"
        )
