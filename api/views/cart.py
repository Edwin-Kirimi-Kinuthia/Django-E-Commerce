from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from cart.models import Cart, CartItem
from shop.models import Product
from api.serializers.cart import CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer


def _get_or_create_user_cart(user):
    cart_id = f'user_{user.id}'
    cart, _ = Cart.objects.get_or_create(cart_id=cart_id)
    return cart


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(
            user=request.user, active=True
        ).select_related('product__category')
        total = sum(item.sub_total() for item in items)
        return Response({
            'items': CartItemSerializer(items, many=True).data,
            'total': str(total),
            'item_count': items.count(),
        })


class CartAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(
            Product, id=serializer.validated_data['product_id'], available=True
        )
        quantity = serializer.validated_data['quantity']

        if quantity > product.stock:
            return Response(
                {'error': f'Only {product.stock} items in stock.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = _get_or_create_user_cart(request.user)
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            active=True,
            defaults={'cart': cart, 'quantity': 0},
        )

        new_quantity = item.quantity + quantity
        if new_quantity > product.stock:
            return Response(
                {'error': f'Cannot add {quantity} more. Only {product.stock - item.quantity} remaining.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = new_quantity
        item.save()
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CartUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        item = get_object_or_404(CartItem, id=item_id, user=request.user, active=True)
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data['quantity']
        if quantity > item.product.stock:
            return Response(
                {'error': f'Only {item.product.stock} items in stock.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = quantity
        item.save()
        return Response(CartItemSerializer(item).data)


class CartRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        item = get_object_or_404(CartItem, id=item_id, user=request.user, active=True)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        CartItem.objects.filter(user=request.user, active=True).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
