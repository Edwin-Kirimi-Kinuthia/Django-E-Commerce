from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    fields = ['product', 'variant', 'quantity', 'active', 'user']
    readonly_fields = ['product', 'variant']
    extra = 0
    can_delete = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['cart_id', 'date_added', 'item_count']
    list_display_links = ['cart_id']
    search_fields = ['cart_id']
    readonly_fields = ['cart_id', 'date_added']
    inlines = [CartItemInline]
    date_hierarchy = 'date_added'

    def item_count(self, obj):
        return obj.cartitem_set.count()
    item_count.short_description = 'Items'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'cart', 'user', 'variant', 'quantity', 'active', 'sub_total']
    list_display_links = ['product']
    list_filter = ['active']
    search_fields = ['product__name', 'cart__cart_id', 'user__username']
    raw_id_fields = ['product', 'cart', 'user', 'variant']
