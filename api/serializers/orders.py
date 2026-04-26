from rest_framework import serializers
from order.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    sub_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'sub_total']

    def get_sub_total(self, obj):
        return obj.sub_total()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'total', 'discount_amount', 'coupon_code',
            'emailAddress', 'created', 'updated',
            'billingName', 'billingAddress1', 'billingCity',
            'billingState', 'billingPostcode', 'billingCountry',
            'shippingName', 'shippingAddress1', 'shippingCity',
            'shippingState', 'shippingPostcode', 'shippingCountry',
            'items',
        ]
        read_only_fields = ['status', 'total', 'discount_amount', 'created', 'updated']


class CheckoutSerializer(serializers.Serializer):
    stripe_token = serializers.CharField()
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    # Billing
    billing_name = serializers.CharField(max_length=250)
    billing_address1 = serializers.CharField(max_length=250)
    billing_city = serializers.CharField(max_length=250)
    billing_state = serializers.CharField(max_length=5)
    billing_postcode = serializers.CharField(max_length=10)
    billing_country = serializers.CharField(max_length=200)

    # Shipping
    shipping_name = serializers.CharField(max_length=250)
    shipping_address1 = serializers.CharField(max_length=250)
    shipping_city = serializers.CharField(max_length=250)
    shipping_state = serializers.CharField(max_length=5)
    shipping_postcode = serializers.CharField(max_length=10)
    shipping_country = serializers.CharField(max_length=200)
