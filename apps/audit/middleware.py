from django.utils.deprecation import MiddlewareMixin
from .models import AuditEvent
import json

class AuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                # Log mutating requests
                try:
                    AuditEvent.objects.create(
                        actor=request.user,
                        object_type='HTTP_REQUEST',
                        object_id=0,
                        action=f"{request.method} {request.path}",
                        after_json={"status_code": response.status_code}
                    )
                except Exception:
                    pass
        return response