from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Import the main dashboard view
from apps.dashboard.views import dashboard_view

urlpatterns = [
    # ==========================================
    # 1. ADMIN PANEL
    # ==========================================
    path('admin/', admin.site.urls),

    # ==========================================
    # 2. AUTHENTICATION (Login, Logout, Password Reset)
    # ==========================================
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password Change (For logged-in users)
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url='/password-change/done/'
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),

    # Password Reset (For logged-out users - requires email setup)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/password-reset/complete/'
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # ==========================================
    # 3. DASHBOARD (Default Landing Page)
    # ==========================================
    path('', dashboard_view, name='dashboard'),

    # ==========================================
    # 4. APP ROUTING (Namespaces)
    # ==========================================
    # Accounts (User Management & Profiles)
    path('accounts/', include('apps.accounts.urls')),
    
    # Imports (CSV/XLSX Upload & Processing)
    path('imports/', include('apps.imports.urls')),
    
    # Cases (Triage, Approval, Submission)
    path('cases/', include('apps.cases.urls')),
    
    # Audit (Immutable Logs)
    path('audit/', include('apps.audit.urls')),
]

# ==========================================
# 5. DEVELOPMENT SERVERS (Media & Static Files)
# ==========================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ==========================================
# 6. CUSTOM ERROR HANDLERS (Optional but recommended)
# ==========================================
handler403 = 'apps.dashboard.views.error_403'
handler404 = 'apps.dashboard.views.error_404'
handler500 = 'apps.dashboard.views.error_500'