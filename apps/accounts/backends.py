from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
            
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing difference
            UserModel().set_password(password)
            return None

        # Check if the account is locked
        if user.is_locked:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            # Success: Reset failed attempts and record IP
            ip = request.META.get('REMOTE_ADDR') if request else None
            user.record_successful_login(ip)
            return user
        else:
            # Failure: Increment failed attempts
            user.record_failed_login()
            return None