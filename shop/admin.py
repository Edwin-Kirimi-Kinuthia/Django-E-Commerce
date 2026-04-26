from django.contrib import admin
from django.utils.html import format_html
from .models import Category, FeaturedSlide, Product, ProductAttribute, ProductImage, ProductVariant, Review


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_feature', 'order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['name', 'value', 'price_modifier', 'stock', 'sku']
    verbose_name = 'Size / Colour Variant'
    verbose_name_plural = 'Size & Colour Variants (affect price/stock per option)'


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 3
    fields = ['name', 'value']
    verbose_name = 'Attribute'
    verbose_name_plural = 'Product Attributes (Material, Color, Care, Fit…)'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'category', 'price', 'discount_price', 'stock_display', 'available', 'is_featured', 'brand', 'created']
    list_editable = ['price', 'discount_price', 'available', 'is_featured']
    list_filter = ['available', 'is_featured', 'category', 'vendor', 'brand']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'sku', 'brand']
    list_per_page = 20
    inlines = [ProductImageInline, ProductAttributeInline, ProductVariantInline]

    class Media:
        js = ('js/admin_attribute_presets.js',)

    def stock_display(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color:#dc2626;font-weight:700;">Out of Stock</span>')
        elif obj.stock <= 5:
            return format_html('<span style="color:#d97706;font-weight:600;">Low: {}</span>', obj.stock)
        return obj.stock
    stock_display.short_description = 'Stock'
    stock_display.admin_order_field = 'stock'


@admin.register(FeaturedSlide)
class FeaturedSlideAdmin(admin.ModelAdmin):
    list_display = ['slide_thumb', 'title', 'product', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_display_links = ['title']

    def slide_thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;object-fit:cover;">', obj.image.url)
        return '—'
    slide_thumb.short_description = ''


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_verified_purchase', 'created']
    list_filter = ['rating', 'is_verified_purchase']
    search_fields = ['product__name', 'user__username', 'title']
    readonly_fields = ['created', 'updated']
