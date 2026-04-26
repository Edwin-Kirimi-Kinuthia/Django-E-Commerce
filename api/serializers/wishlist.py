from rest_framework import serializers
from wishlist.models import WishlistItem
from .products import ProductListSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at']


class AddToWishlistSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
