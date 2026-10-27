from django.db import models
from django.conf import settings
from django.utils import timezone

class AuditEvent(models.Model):
    ACTIONS = [
        ('CREATE', 'Create'), ('UPDATE', 'Update'), ('DELETE', 'Delete'),
        ('LOGIN', 'Login'), ('LOGOUT', 'Logout'), ('EXPORT', 'Export'),
    ]
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    action = models.CharField(max_length=50)
    before_json = models.JSONField(null=True, blank=True)
    after_json = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['object_type', 'object_id'])]

    def __str__(self):
        return f"{self.actor} - {self.action} - {self.object_type}"