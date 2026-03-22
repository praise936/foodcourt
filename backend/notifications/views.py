# notifications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """Get all notifications for current user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationMarkAllReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'message': 'All notifications marked as read'})


class NotificationMarkReadView(APIView):
    """Mark single notification as read"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})


class NotificationClearView(APIView):
    """Delete all notifications for current user"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        Notification.objects.filter(user=request.user).delete()
        return Response({'message': 'All notifications cleared'}, status=status.HTTP_204_NO_CONTENT)