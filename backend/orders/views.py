# orders/views.py — Order placement and management (No WebSockets)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

# REMOVED: from channels.layers import get_channel_layer
# REMOVED: from asgiref.sync import async_to_sync

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from notifications.models import Notification


class PlaceOrderView(APIView):
    """Customer places a new order — create notification for restaurant"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save(customer=request.user)
            order_data = OrderSerializer(order, context={'request': request}).data

            # Create notification for restaurant manager
            Notification.objects.create(
                user=order.restaurant.manager,
                type='NEW_ORDER',
                title='New Order Received!',
                message=f'New order #{order.id} from {order.customer.get_full_name() or order.customer.email}',
                data={'order_id': order.id, 'order_data': order_data}
            )

            return Response(order_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyOrdersView(APIView):
    """Customer sees only their own orders"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)


class OrderDetailView(APIView):
    """Get or update a single order — customer or restaurant manager"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        # Only the customer or the restaurant manager can see this order
        if order.customer != request.user and order.restaurant.manager != request.user and not request.user.is_platform_admin:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data)


class UpdateOrderStatusView(APIView):
    """Restaurant manager updates order status — creates notification for customer"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        # Only restaurant manager or admin can update status
        if order.restaurant.manager != request.user and not request.user.is_platform_admin:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']

        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        order_data = OrderSerializer(order, context={'request': request}).data

        # Create notification for customer
        notification_type = 'ORDER_STATUS_UPDATE'
        title = f'Order #{order.id} Status Update'
        message = f'Your order is now: {order.get_status_display()}'
        
        # Special notification types for certain statuses
        if new_status == 'ready':
            notification_type = 'ORDER_READY'
            title = 'Order Ready for Pickup!'
            message = f'Order #{order.id} is ready. Come pick it up!'
        elif new_status == 'completed':
            notification_type = 'ORDER_PICKED_UP'
            title = 'Order Completed'
            message = f'Order #{order.id} has been picked up. Thank you!'
        
        Notification.objects.create(
            user=order.customer,
            type=notification_type,
            title=title,
            message=message,
            data={'order_id': order.id, 'order_data': order_data}
        )

        return Response(order_data)


class RestaurantOrdersView(APIView):
    """Restaurant manager sees all orders for their restaurant"""
    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id):
        from restaurants.models import Restaurant
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)

        if restaurant.manager != request.user and not request.user.is_platform_admin:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)


class AllOrdersView(APIView):
    """Platform admin sees all orders across all restaurants"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_platform_admin:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        orders = Order.objects.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)