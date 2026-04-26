import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from order.models import Order, OrderItem
from cart.models import CartItem
from coupons.models import Coupon
from api.serializers.orders import OrderSerializer, CheckoutSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Order, id=self.kwargs['pk'], user=self.request.user)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk, user=request.user)
        if order.status not in (Order.PENDING, Order.CONFIRMED):
            return Response(
                {'error': f'Cannot cancel an order with status "{order.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = Order.CANCELLED
        order.save(update_fields=['status', 'updated'])
        return Response(OrderSerializer(order).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get active cart items
        cart_items = CartItem.objects.filter(
            user=request.user, active=True
        ).select_related('product')

        if not cart_items.exists():
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate totals
        subtotal = sum(item.sub_total() for item in cart_items)
        discount_amount = 0
        coupon_code = data.get('coupon_code', '').strip()

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                valid, message = coupon.is_valid(order_total=subtotal)
                if not valid:
                    return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
                discount_amount = coupon.calculate_discount(subtotal)
            except Coupon.DoesNotExist:
                return Response({'error': 'Invalid coupon code.'}, status=status.HTTP_400_BAD_REQUEST)

        total = subtotal - discount_amount

        # Charge via Stripe
        try:
            charge = stripe.Charge.create(
                amount=int(total * 100),
                currency='gbp',
                description=f'Order for {request.user.email}',
                source=data['stripe_token'],
            )
        except stripe.error.CardError as e:
            return Response({'error': str(e.user_message)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except stripe.error.StripeError as e:
            return Response({'error': 'Payment failed. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create Order
        order = Order.objects.create(
            user=request.user,
            token=charge['id'],
            total=total,
            discount_amount=discount_amount,
            coupon_code=coupon_code,
            emailAddress=request.user.email,
            status=Order.CONFIRMED,
            billingName=data['billing_name'],
            billingAddress1=data['billing_address1'],
            billingCity=data['billing_city'],
            billingState=data['billing_state'],
            billingPostcode=data['billing_postcode'],
            billingCountry=data['billing_country'],
            shippingName=data['shipping_name'],
            shippingAddress1=data['shipping_address1'],
            shippingCity=data['shipping_city'],
            shippingState=data['shipping_state'],
            shippingPostcode=data['shipping_postcode'],
            shippingCountry=data['shipping_country'],
        )

        # Create order items and update stock
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product.name,
                quantity=item.quantity,
                price=item.product.effective_price,
            )
            item.product.stock -= item.quantity
            item.product.save(update_fields=['stock'])

        # Increment coupon usage
        if coupon_code and discount_amount:
            Coupon.objects.filter(code=coupon_code).update(
                uses_count=coupon.uses_count + 1
            )

        # Clear cart
        cart_items.delete()

        # Send confirmation email
        try:
            message = render_to_string('email/order_confirmation.html', {'order': order})
            send_mail(
                subject=f'Order Confirmed — #{order.id}',
                message='',
                html_message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[order.emailAddress],
                fail_silently=True,
            )
        except Exception:
            pass  # don't fail the order if email fails

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
