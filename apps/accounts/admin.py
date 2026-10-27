from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile', {'fields': ('role', 'phone_number', 'last_login_ip', 'is_locked')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile', {'fields': ('role', 'phone_number')}),
    )