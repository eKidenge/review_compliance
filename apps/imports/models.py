from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import uuid


class ImportBatch(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), 
        ('PROCESSING', 'Processing'), 
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]

    SOURCE_TYPE_CHOICES = [
        ('CSV', 'CSV Upload'),
        ('XLSX', 'XLSX Upload'),
        ('GOOGLE_SHEET', 'Google Sheet Sync'),
    ]
    
    # Unique identifier for the batch
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ownership and File Info
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='imports',
        null=True,
        blank=True,
        help_text="The user or system that initiated this batch."
    )
    filename = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='imports/', 
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])],
        blank=True,
        null=True,
        help_text="The raw CSV or XLSX file uploaded by the user. Null for Google Sheet syncs."
    )
    
    # Source Tracking
    source_type = models.CharField(
        max_length=20, 
        choices=SOURCE_TYPE_CHOICES, 
        default='CSV',
        db_index=True,
        help_text="Origin of this batch (File upload or Google Sheet)."
    )
    
    # Timestamps
    imported_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Retry Tracking
    retry_count = models.IntegerField(
        default=0, 
        help_text="Number of times the background task was retried."
    )
    
    # Metrics (Populated by the Celery task)
    row_count = models.IntegerField(default=0)
    valid_count = models.IntegerField(default=0)
    invalid_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)
    
    # Status & Error Handling
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING', 
        db_index=True
    )
    error_log = models.TextField(blank=True, null=True)
    
    # Transparency Log (Populated by the Celery task)
    invalid_urls_log = models.TextField(
        blank=True, 
        null=True, 
        help_text="A list of rejected rows for audit and user reference."
    )

    class Meta:
        ordering = ['-imported_at']
        verbose_name = "Import Batch"
        verbose_name_plural = "Import Batches"
        indexes = [
            models.Index(fields=['status', 'imported_at']),
        ]

    def __str__(self):
        return f"{self.filename} ({self.status})"

    @property
    def success_rate(self):
        """Returns the percentage of valid URLs from the total rows."""
        if self.row_count == 0:
            return 0
        return round((self.valid_count / self.row_count) * 100, 1)

    @property
    def rejection_rate(self):
        """Returns the percentage of rejected rows from the total rows."""
        if self.row_count == 0:
            return 0
        return round((self.invalid_count / self.row_count) * 100, 1)

    @property
    def is_finished(self):
        """Returns True if the batch has reached a terminal state."""
        return self.status in ['COMPLETED', 'FAILED']

    @property
    def processing_duration(self):
        """Returns the processing duration in seconds."""
        if not self.completed_at or not self.imported_at:
            return None
        delta = self.completed_at - self.imported_at
        return round(delta.total_seconds(), 1)


class GoogleSheetSource(models.Model):
    """
    Stores the credentials and metadata for a Google Sheet that needs to be 
    periodically synced into the ReviewCase database via Celery Beat.
    """
    name = models.CharField(
        max_length=255, 
        help_text="A friendly name for this source (e.g., 'Client A - Main Sheet')."
    )
    spreadsheet_id = models.CharField(
        max_length=255, 
        help_text="The ID from the Google Sheet URL (the string between /d/ and /edit)."
    )
    sheet_name = models.CharField(
        max_length=255, 
        default="Sheet1", 
        help_text="The name of the specific tab in the sheet."
    )
    credentials_json = models.JSONField(
        help_text="Paste the full Service Account JSON key here. Keep this secret."
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(
        default=True, 
        help_text="If unchecked, the scheduled sync will skip this sheet."
    )

    class Meta:
        verbose_name = "Google Sheet Source"
        verbose_name_plural = "Google Sheet Sources"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.spreadsheet_id})"

    @property
    def sync_status(self):
        """Returns a human-readable status for the admin panel."""
        if not self.last_synced_at:
            return "Never Synced"
        if not self.is_active:
            return "Paused"
        return "Active"