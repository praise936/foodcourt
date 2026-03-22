# notifications/urls.py
from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationClearView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/read/', NotificationMarkReadView.as_view(), name='mark_read'),
    path('clear/', NotificationClearView.as_view(), name='clear_notifications'),
]