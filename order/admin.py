from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.utils.timezone import now
from datetime import timedelta

from .models import Order, OrderItem, ShippingRate


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'quantity', 'price']
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False
    max_num = 0
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'billingName', 'emailAddress', 'total', 'status_badge_display', 'created']
    list_display_links = ['id', 'billingName']
    list_filter = ['status', 'created']
    search_fields = ['id', 'billingName', 'emailAddress', 'token']
    list_per_page = 25
    date_hierarchy = 'created'
    readonly_fields = [
        'id', 'token', 'total', 'emailAddress', 'created', 'updated',
        'billingName', 'billingAddress1', 'billingCity', 'billingState',
        'billingPostcode', 'billingCountry',
        'shippingName', 'shippingAddress1', 'shippingCity', 'shippingState',
        'shippingPostcode', 'shippingCountry',
    ]
    fieldsets = [
        ('Order Information', {'fields': ['id', 'token', 'total', 'status', 'created', 'updated']}),
        ('Billing', {'fields': ['billingName', 'billingAddress1', 'billingCity', 'billingState', 'billingPostcode', 'billingCountry', 'emailAddress']}),
        ('Shipping', {'fields': ['shippingName', 'shippingAddress1', 'shippingCity', 'shippingState', 'shippingPostcode', 'shippingCountry']}),
    ]
    inlines = [OrderItemInline]

    def status_badge_display(self, obj):
        colours = {
            'pending':   ('#92400e', '#fef3c7'),
            'confirmed': ('#1e40af', '#dbeafe'),
            'shipped':   ('#5b21b6', '#ede9fe'),
            'delivered': ('#065f46', '#d1fae5'),
            'cancelled': ('#991b1b', '#fee2e2'),
            'refunded':  ('#374151', '#f3f4f6'),
        }
        fg, bg = colours.get(obj.status, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge_display.short_description = 'Status'
    status_badge_display.admin_order_field = 'status'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_list_display_links(self, request, list_display):
        return ['id', 'billingName']

    def changelist_view(self, request, extra_context=None):
        # Sales stats for the last 30 days
        thirty_days_ago = now() - timedelta(days=30)
        recent_orders = Order.objects.filter(created__gte=thirty_days_ago)

        stats = {
            'total_revenue': recent_orders.aggregate(s=Sum('total'))['s'] or 0,
            'order_count': recent_orders.count(),
            'avg_order_value': (
                recent_orders.aggregate(s=Sum('total'))['s'] or 0
            ) / max(recent_orders.count(), 1),
            'pending_count': Order.objects.filter(status=Order.PENDING).count(),
            'shipped_count': Order.objects.filter(status=Order.SHIPPED).count(),
        }

        extra_context = extra_context or {}
        extra_context['dashboard_stats'] = stats
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'method', 'country_display', 'rate', 'free_shipping_threshold', 'estimated_days', 'is_active']
    list_display_links = ['name']
    list_filter = ['method', 'is_active']
    list_editable = ['is_active', 'rate']
    search_fields = ['name', 'country']

    fieldsets = [
        ('Shipping Method', {
            'fields': ['name', 'method', 'is_active'],
        }),
        ('Geographic Scope', {
            'fields': ['country'],
            'description': 'Leave country blank to apply this rate to all countries.',
        }),
        ('Pricing', {
            'fields': ['rate', 'min_order_amount', 'free_shipping_threshold'],
        }),
        ('Details', {
            'fields': ['estimated_days'],
        }),
    ]

    def country_display(self, obj):
        return obj.country or 'All Countries'
    country_display.short_description = 'Country'
