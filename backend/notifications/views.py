# notifications/views.py
# Endpoint where the frontend saves the FCM token for a user

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class SaveFCMTokenView(APIView):
    """
    Frontend calls this after getting an FCM token from Firebase.
    We save it on the user so we can push notifications to them.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('token', '').strip()
        if not token:
            return Response(
                {'error': 'Token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.user.fcm_token = token
        request.user.save()
        return Response({'message': 'FCM token saved.'})