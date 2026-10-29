
import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class ImportBatch(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    SOURCE_TYPE_CHOICES = [
        ("CSV", "CSV Upload"),
        ("XLSX", "XLSX Upload"),
        ("GOOGLE_SHEET", "Google Sheet Sync"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="imports",
        null=True,
        blank=True,
        help_text="User who initiated this import; null for system jobs.",
    )

    filename = models.CharField(max_length=255)

    file = models.FileField(
        upload_to="imports/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["csv", "xlsx"]
            )
        ],
        blank=True,
        null=True,
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default="CSV",
        db_index=True,
    )

    imported_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    retry_count = models.PositiveIntegerField(default=0)

    row_count = models.PositiveIntegerField(default=0)
    valid_count = models.PositiveIntegerField(default=0)
    invalid_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )

    error_log = models.TextField(blank=True, default="")
    invalid_urls_log = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-imported_at"]
        verbose_name = "Import Batch"
        verbose_name_plural = "Import Batches"
        indexes = [
            models.Index(fields=["status", "imported_at"]),
            models.Index(fields=["source_type", "status"]),
        ]

    def __str__(self):
        return f"{self.filename} ({self.status})"

    @property
    def success_rate(self):
        """Percentage of input rows successfully imported."""
        if not self.row_count:
            return 0

        return round(
            self.valid_count / self.row_count * 100,
            1,
        )

    @property
    def rejection_rate(self):
        """Percentage of input rows rejected as invalid."""
        if not self.row_count:
            return 0

        return round(
            self.invalid_count / self.row_count * 100,
            1,
        )

    @property
    def is_finished(self):
        return self.status in {"COMPLETED", "FAILED"}

    @property
    def processing_duration(self):
        if not self.imported_at:
            return None

        end_time = self.completed_at

        if end_time is None:
            if self.status != "PROCESSING":
                return None
            end_time = timezone.now()

        return round(
            (end_time - self.imported_at).total_seconds(),
            1,
        )


class GoogleSheetSource(models.Model):
    name = models.CharField(max_length=255)

    spreadsheet_id = models.CharField(max_length=255)

    sheet_name = models.CharField(
        max_length=255,
        default="Sheet1",
    )

    credentials_json = models.JSONField(
        help_text=(
            "Service account credentials. "
            "Restrict admin access and protect this sensitive data."
        ),
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    # Operational tracking for the most recent synchronization.
    last_sync_status = models.CharField(
        max_length=20,
        choices=[
            ("NEVER", "Never Synced"),
            ("PROCESSING", "Processing"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
        ],
        default="NEVER",
        db_index=True,
    )

    last_sync_error = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Google Sheet Source"
        verbose_name_plural = "Google Sheet Sources"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.spreadsheet_id})"

    @property
    def sync_status(self):
        if not self.is_active:
            return "Paused"

        if self.last_sync_status == "NEVER":
            return "Never Synced"

        return self.last_sync_status.title()
