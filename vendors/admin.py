from django.contrib import admin
from django.utils.html import format_html

from .models import Vendor, VendorReview, VendorShipment


def approve_vendors(modeladmin, request, queryset):
    queryset.update(status=Vendor.STATUS_APPROVED)
approve_vendors.short_description = 'Approve selected vendors'


def suspend_vendors(modeladmin, request, queryset):
    queryset.update(status=Vendor.STATUS_SUSPENDED)
suspend_vendors.short_description = 'Suspend selected vendors'


class VendorReviewInline(admin.TabularInline):
    model = VendorReview
    extra = 0
    readonly_fields = ['user', 'rating', 'title', 'body', 'created']
    can_delete = False


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['logo_thumb', 'name', 'user', 'status_badge', 'product_count_display',
                    'avg_rating_display', 'commission_rate', 'created']
    list_display_links = ['name']
    list_filter = ['status', 'created']
    search_fields = ['name', 'user__username', 'user__email']
    readonly_fields = ['slug', 'created', 'updated']
    actions = [approve_vendors, suspend_vendors]
    list_per_page = 25
    inlines = [VendorReviewInline]

    fieldsets = [
        ('Store', {'fields': ['user', 'name', 'slug', 'description', 'logo', 'banner']}),
        ('Contact', {'fields': ['phone', 'address', 'website']}),
        ('Settings', {'fields': ['status', 'commission_rate', 'created', 'updated']}),
    ]

    def logo_thumb(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">', obj.logo.url)
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:var(--amz-nav,#312e81);color:#fff;'
            'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;">{}</div>',
            obj.name[:1].upper()
        )
    logo_thumb.short_description = ''

    def status_badge(self, obj):
        colours = {
            Vendor.STATUS_PENDING:   ('#92400e', '#fef3c7'),
            Vendor.STATUS_APPROVED:  ('#065f46', '#d1fae5'),
            Vendor.STATUS_SUSPENDED: ('#991b1b', '#fee2e2'),
        }
        fg, bg = colours.get(obj.status, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def product_count_display(self, obj):
        return obj.products.count()
    product_count_display.short_description = 'Products'

    def avg_rating_display(self, obj):
        r = obj.average_rating
        return f'{r} ★' if r else '—'
    avg_rating_display.short_description = 'Avg Rating'


@admin.register(VendorReview)
class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'user', 'rating', 'title', 'created']
    list_filter = ['rating', 'vendor']
    search_fields = ['vendor__name', 'user__username', 'title']
    readonly_fields = ['created']


@admin.register(VendorShipment)
class VendorShipmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'vendor', 'carrier_display_col', 'tracking_number', 'shipped_at', 'estimated_delivery']
    list_display_links = ['id', 'order']
    list_filter = ['carrier', 'vendor', 'shipped_at']
    search_fields = ['order__id', 'vendor__name', 'tracking_number']
    readonly_fields = ['shipped_at']
    date_hierarchy = 'shipped_at'

    fieldsets = [
        ('Shipment', {
            'fields': ['order', 'vendor', 'shipped_at'],
        }),
        ('Carrier & Tracking', {
            'fields': ['carrier', 'carrier_other', 'tracking_number', 'tracking_url'],
        }),
        ('Delivery', {
            'fields': ['estimated_delivery', 'notes'],
        }),
    ]

    def carrier_display_col(self, obj):
        return obj.carrier_display
    carrier_display_col.short_description = 'Carrier'
