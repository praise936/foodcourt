# backend/urls.py — root URL configuration

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth endpoints
    path('api/auth/', include('users.urls')),

    # Restaurant endpoints
    path('api/restaurants/', include('restaurants.urls')),

    # Menu endpoints
    path('api/menu/', include('menu.urls')),

    # Order endpoints
    path('api/orders/', include('orders.urls')),

    # Review endpoints
    path('api/reviews/', include('reviews.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)