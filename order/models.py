from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
        (REFUNDED, 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    token = models.CharField(max_length=250, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Order Total')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True)
    emailAddress = models.EmailField(max_length=250, blank=True, verbose_name='Email Address')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Billing
    billingName = models.CharField(max_length=250, blank=True)
    billingAddress1 = models.CharField(max_length=250, blank=True)
    billingCity = models.CharField(max_length=250, blank=True)
    billingState = models.CharField(max_length=5, blank=True)
    billingPostcode = models.CharField(max_length=10, blank=True)
    billingCountry = models.CharField(max_length=200, blank=True)

    # Shipping
    shippingName = models.CharField(max_length=250, blank=True)
    shippingAddress1 = models.CharField(max_length=250, blank=True)
    shippingCity = models.CharField(max_length=250, blank=True)
    shippingState = models.CharField(max_length=5, blank=True)
    shippingPostcode = models.CharField(max_length=10, blank=True)
    shippingCountry = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'Order'
        ordering = ['-created']

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    product = models.CharField(max_length=250)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    vendor = models.ForeignKey(
        'vendors.Vendor', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='order_items',
    )

    class Meta:
        db_table = 'OrderItem'

    def sub_total(self):
        return self.quantity * self.price

    def __str__(self):
        return self.product


class ShippingRate(models.Model):
    STANDARD = 'standard'
    EXPRESS = 'express'
    FREE = 'free'
    METHOD_CHOICES = [
        (STANDARD, 'Standard Shipping'),
        (EXPRESS, 'Express Shipping'),
        (FREE, 'Free Shipping'),
    ]

    name = models.CharField(max_length=100)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=STANDARD)
    country = models.CharField(max_length=100, blank=True, help_text='Leave blank to apply to all countries')
    rate = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           help_text='Minimum order amount to qualify for this rate')
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                  help_text='Orders above this amount get free shipping (leave blank to disable)')
    estimated_days = models.CharField(max_length=50, blank=True, help_text='e.g. 3-5 business days')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'ShippingRate'
        ordering = ['rate']
        verbose_name = 'Shipping Rate'
        verbose_name_plural = 'Shipping Rates'

    def __str__(self):
        return f'{self.name} ({self.get_method_display()})'
