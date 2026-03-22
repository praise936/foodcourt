# users/models.py — Custom user model with roles

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended user model with role support.
    Roles: platform_admin, restaurant_manager, customer
    """

    ROLE_CHOICES = (
        ('platform_admin', 'Platform Admin'),
        ('restaurant_manager', 'Restaurant Manager'),
        ('customer', 'Customer'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Use email as the login field instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def avatar_url(self):
        """Return full URL for avatar image"""
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def is_platform_admin(self):
        return self.role == 'platform_admin'

    @property
    def is_restaurant_manager(self):
        return self.role == 'restaurant_manager'