from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from functools import wraps

def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has a particular role.
    Usage: @role_required(['ADMIN', 'REVIEWER'])
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied("You do not have the required role to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator