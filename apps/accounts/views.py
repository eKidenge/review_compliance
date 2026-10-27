from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileUpdateForm
from apps.audit.models import AuditEvent


# ==========================================
# MIXINS
# ==========================================

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin to restrict access to Admins only.
    If a non-admin tries to access, raise PermissionDenied (403).
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'ADMIN'
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to access User Management.")


# ==========================================
# CLASS BASED VIEWS (ADMIN USER MANAGEMENT)
# ==========================================

class UserListView(AdminRequiredMixin, ListView):
    """
    Admin view to list all users with search and role filtering.
    """
    model = CustomUser
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        role_filter = self.request.GET.get('role')
        
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        if role_filter:
            queryset = queryset.filter(role=role_filter)
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = CustomUser.ROLE_CHOICES
        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    """
    Admin view to create a new user and assign a role.
    """
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"User '{self.object.username}' created successfully.")
        
        # Audit Log
        AuditEvent.objects.create(
            actor=self.request.user,
            object_type='CustomUser',
            object_id=str(self.object.id),
            action='CREATE',
            after_json={'username': self.object.username, 'role': self.object.role}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the user. Please check the form.")
        return super().form_invalid(form)


class UserUpdateView(AdminRequiredMixin, UpdateView):
    """
    Admin view to edit an existing user's details and role.
    """
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"User '{self.object.username}' updated successfully.")
        
        # Audit Log
        AuditEvent.objects.create(
            actor=self.request.user,
            object_type='CustomUser',
            object_id=str(self.object.id),
            action='UPDATE',
            after_json={'username': self.object.username, 'role': self.object.role, 'is_active': self.object.is_active}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the user. Please check the form.")
        return super().form_invalid(form)


# ==========================================
# FUNCTION BASED VIEWS (PROFILE)
# ==========================================

@login_required
def profile_view(request):
    """
    View for users to see their own profile.
    """
    return render(request, 'accounts/profile.html', {'user_obj': request.user})


@login_required
def profile_update(request):
    """
    View for users to edit their own profile.
    Note: Users cannot change their own role.
    """
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            
            # Audit Log
            AuditEvent.objects.create(
                actor=request.user,
                object_type='CustomUser',
                object_id=str(request.user.id),
                action='UPDATE_PROFILE',
                after_json={'email': request.user.email}
            )
            return redirect('accounts:profile')
        else:
            messages.error(request, "There was an error updating your profile.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile_form.html', {'form': form})