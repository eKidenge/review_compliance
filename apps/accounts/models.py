from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('REVIEWER', 'Case Reviewer'),
        ('SUBMITTER', 'Submitter'),
        ('CLIENT', 'Read-only Client'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='REVIEWER')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Security & Tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # Helper methods for template logic
    def is_admin(self):
        return self.role == 'ADMIN'

    def is_reviewer(self):
        return self.role in ['ADMIN', 'REVIEWER']

    def is_submitter(self):
        return self.role in ['ADMIN', 'SUBMITTER']

    def can_view_case(self):
        return self.role in ['ADMIN', 'REVIEWER', 'SUBMITTER', 'CLIENT']

    # Security Helper Methods
    def record_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5: # Lock after 5 failed attempts
            self.is_locked = True
        self.save()

    def record_successful_login(self, ip_address):
        self.failed_login_attempts = 0
        self.last_login_ip = ip_address
        self.save()