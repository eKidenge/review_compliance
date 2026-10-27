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
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='imports')
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='imports/', validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx'])])
    imported_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)
    valid_count = models.IntegerField(default=0)
    invalid_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_log = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.filename} ({self.status})"