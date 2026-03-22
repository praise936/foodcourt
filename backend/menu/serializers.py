# menu/serializers.py

from rest_framework import serializers
from .models import MenuItem, MenuCategory


class MenuCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'order']


class MenuItemSerializer(serializers.ModelSerializer):
    """Full menu item with image_url for frontend display"""

    image_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'image_url',
            'availability', 'is_featured', 'prep_time_minutes',
            'category', 'category_name', 'restaurant', 'created_at'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """For creating/updating menu items — accepts image file"""

    class Meta:
        model = MenuItem
        fields = [
            'name', 'description', 'price', 'image',
            'availability', 'is_featured', 'prep_time_minutes', 'category'
        ]