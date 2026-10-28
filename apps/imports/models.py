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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='imports'
    )
    filename = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='imports/', 
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])]
    )
    imported_at = models.DateTimeField(auto_now_add=True)
    
    # Metrics
    row_count = models.IntegerField(default=0)
    valid_count = models.IntegerField(default=0)
    invalid_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_log = models.TextField(blank=True, null=True)
    
    # NEW FIELD: Log of rejected URLs for compliance transparency
    invalid_urls_log = models.TextField(
        blank=True, 
        null=True, 
        help_text="A list of rejected rows for audit and user reference."
    )

    class Meta:
        ordering = ['-imported_at']
        verbose_name = "Import Batch"
        verbose_name_plural = "Import Batches"

    def __str__(self):
        return f"{self.filename} ({self.status})"

    @property
    def success_rate(self):
        """Returns the percentage of valid URLs from the total rows."""
        if self.row_count == 0:
            return 0
        return round((self.valid_count / self.row_count) * 100, 1)