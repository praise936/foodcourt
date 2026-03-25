# users/serializers.py — Serialize user data for API responses

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Handles new user registration"""

    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'password', 'password_confirm', 'phone', 'role']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """General purpose user serializer"""

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'role', 'phone', 'avatar_url', 'created_at']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """For updating profile info - now accepts avatar URL string instead of file"""
    avatar_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar', 'avatar_url']
    
    def get_avatar_url(self, obj):
        """Return the avatar URL"""
        return obj.avatar
class ChangePasswordSerializer(serializers.Serializer):
    """Validates password change — requires current password"""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data