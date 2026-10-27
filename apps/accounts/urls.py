from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Profile (For all logged-in users)
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_update, name='profile_update'),

    # User Management (Admin Only - Class Based Views)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
]