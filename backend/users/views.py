# users/views.py — Authentication views



import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)

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
    """Admin only — register a restaurant manager"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_platform_admin:
            return Response(
                {'error': 'Only platform admin can register restaurant managers.'},
                status=status.HTTP_403_FORBIDDEN
            )
        data = request.data.copy()
        data['role'] = 'restaurant_manager'
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            plain_password = request.data.get('password')
            return Response({
                'user': UserSerializer(user, context={'request': request}).data,
                'plain_password': plain_password,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PlatformAdminSetupView(APIView):
    """
    Used once for initial platform admin registration.
    Afterwards, only superusers can create new platform admins.
    """
    permission_classes = [AllowAny]  # Only the very first setup

    def post(self, request):
        # if User.objects.filter(is_platform_admin=True).exists():
        #     return Response({'error': 'Platform admin already exists.'}, status=403)

        data = request.data.copy()
        data['role'] = 'platform_admin'

        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'user': UserSerializer(user).data}, status=201)
        return Response(serializer.errors, status=400)


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


class ChangePasswordView(APIView):
    """Logged in user changes their own password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        # Verify current password is correct
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        # Re-generate tokens since password changed
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Password changed successfully.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class ForgotPasswordView(APIView):
    """
    User submits their email.
    We generate a reset token, save it on the user, and email a reset link.
    In dev mode the email prints to the console/terminal.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response(
                {'error': 'Email address is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # We always return 200 even if email not found — security best practice
        # so attackers can't enumerate which emails are registered
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'message': 'If that email is registered, a reset link has been sent.'
            })

        # Generate a unique token and store it on the user
        token = str(uuid.uuid4()).replace('-', '')
        user.password_reset_token = token
        user.save()

        # Build the reset URL pointing to our frontend
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"

        # Send the email
        send_mail(
            subject='Reset Your FoodCourt Password',
            message=f"""
Hello {user.first_name or user.username},

You requested a password reset for your FoodCourt account.

Click the link below to set a new password:

{reset_url}

If you did not request this, please ignore this email.
Your password will not change.

— The FoodCourt Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({
            'message': 'If that email is registered, a reset link has been sent.'
        })


class ResetPasswordView(APIView):
    """
    User clicks the link from email, submits new password with the token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token', '').strip()
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if not token or not new_password:
            return Response(
                {'error': 'Token and new password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {'error': 'Passwords do not match.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find user by token
        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired reset link.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password and clear the token
        user.set_password(new_password)
        user.password_reset_token = ''
        user.save()

        return Response({'message': 'Password reset successfully. You can now log in.'})


class AllUsersView(APIView):
    """Admin only — list all users"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_platform_admin:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)