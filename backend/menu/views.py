# menu/views.py — Menu item CRUD

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import MenuItem, MenuCategory
from .serializers import MenuItemSerializer, MenuItemCreateSerializer, MenuCategorySerializer
from restaurants.models import Restaurant

from django.db.models import Q
from notifications.models import Notification  # Import Notification model


class MenuListView(APIView):
    """GET — Public: get all menu items for a restaurant"""
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, restaurant_id):
        search = request.query_params.get('search', '')
        items = MenuItem.objects.filter(restaurant_id=restaurant_id)
        if search:
            items = items.filter(name__icontains=search)
        serializer = MenuItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, restaurant_id):
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)

        # Only the manager of this restaurant can add items
        if restaurant.manager != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MenuItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.save(restaurant=restaurant)
            item_data = MenuItemSerializer(item, context={'request': request}).data

            # Create notification for users who have this restaurant saved? 
            # Or just for platform admins? You can customize this.
            # For now, create notification for the restaurant manager
            Notification.objects.create(
                user=restaurant.manager,
                type='NEW_MENU_ITEM',
                title='New Menu Item Added',
                message=f'Added "{item.name}" to your menu',
                data={'menu_item_id': item.id, 'item_data': item_data}
            )

            return Response(item_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Other views (MenuItemDetailView, MenuAvailabilityView, MenuCategoryListView) remain the same


class MenuItemDetailView(APIView):
    """PUT / DELETE a single menu item"""
    permission_classes = [IsAuthenticated]

    def put(self, request, restaurant_id, item_id):
        item = get_object_or_404(MenuItem, pk=item_id, restaurant_id=restaurant_id)

        if item.restaurant.manager != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MenuItemCreateSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(MenuItemSerializer(item, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, restaurant_id, item_id):
        item = get_object_or_404(MenuItem, pk=item_id, restaurant_id=restaurant_id)

        if item.restaurant.manager != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        item.delete()
        return Response({'message': 'Item deleted'}, status=status.HTTP_204_NO_CONTENT)


class MenuAvailabilityView(APIView):
    """Toggle availability of a menu item"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, restaurant_id, item_id):
        item = get_object_or_404(MenuItem, pk=item_id, restaurant_id=restaurant_id)

        if item.restaurant.manager != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        availability = request.data.get('availability')
        if availability not in ['available', 'later', 'unavailable']:
            return Response({'error': 'Invalid availability value'}, status=status.HTTP_400_BAD_REQUEST)

        item.availability = availability
        item.save()
        return Response(MenuItemSerializer(item, context={'request': request}).data)


class MenuCategoryListView(APIView):
    """List and create categories for a restaurant"""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, restaurant_id):
        categories = MenuCategory.objects.filter(restaurant_id=restaurant_id)
        serializer = MenuCategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request, restaurant_id):
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        if restaurant.manager != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MenuCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(restaurant=restaurant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)