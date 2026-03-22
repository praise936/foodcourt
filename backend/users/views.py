# users/views.py — Authentication views

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserSerializer, UserUpdateSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    Public registration — customers ONLY.
    Restaurant managers are registered exclusively from the admin dashboard.
    Platform admin uses the secret /admin-setup page.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        requested_role = request.data.get('role', 'customer')

        # Block anyone from self-registering as manager or admin
        if requested_role in ['restaurant_manager', 'platform_admin']:
            return Response(
                {'error': 'You cannot register as a manager or admin from this page.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Force role to customer regardless of what was sent
        data = request.data.copy()
        data['role'] = 'customer'

        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user, context={'request': request}).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterManagerView(APIView):
    """
    Admin only — register a new restaurant manager.
    Admin provides all details including a temporary password.
    Returns the manager credentials so admin can share them.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only platform admin can create managers
        if not request.user.is_platform_admin:
            return Response(
                {'error': 'Only platform admin can register restaurant managers.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Force role to restaurant_manager
        data = request.data.copy()
        data['role'] = 'restaurant_manager'

        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()

            # Return the plain password too so admin can put it on the receipt
            # We only do this once — it won't be retrievable after this
            plain_password = request.data.get('password')

            return Response({
                'user': UserSerializer(user, context={'request': request}).data,
                'plain_password': plain_password,  # included only for the receipt
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Login with username and password"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'This account has been deactivated.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class ProfileView(APIView):
    """Get and update current user profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserSerializer(request.user, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllUsersView(APIView):
    """Admin only — list all users"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_platform_admin:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)