# backend/users/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    RegisterManagerView,
    LoginView,
    ProfileView,
    AllUsersView,
)

urlpatterns = [
    # Public — customers only
    path('register/', RegisterView.as_view(), name='register'),

    # Admin only — register a restaurant manager
    path('register-manager/', RegisterManagerView.as_view(), name='register_manager'),

    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', AllUsersView.as_view(), name='all_users'),
]