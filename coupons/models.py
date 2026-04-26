from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Coupon(models.Model):
    PERCENTAGE = 'percentage'
    FLAT = 'flat'
    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, 'Percentage'),
        (FLAT, 'Flat Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=250, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default=PERCENTAGE)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Percentage (0-100) or flat GBP amount',
    )
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text='Leave blank for unlimited')
    uses_count = models.PositiveIntegerField(default=0, editable=False)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True, help_text='Leave blank for no expiry')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-valid_from']

    def is_valid(self, order_total=0):
        now = timezone.now()
        if not self.is_active:
            return False, 'Coupon is inactive.'
        if now < self.valid_from:
            return False, 'Coupon is not yet valid.'
        if self.valid_to and now > self.valid_to:
            return False, 'Coupon has expired.'
        if self.max_uses and self.uses_count >= self.max_uses:
            return False, 'Coupon usage limit reached.'
        if order_total < self.min_order_amount:
            return False, f'Minimum order amount is £{self.min_order_amount}.'
        return True, 'Valid.'

    def calculate_discount(self, order_total):
        if self.discount_type == self.PERCENTAGE:
            return round(order_total * (self.discount_value / 100), 2)
        return min(self.discount_value, order_total)

    def __str__(self):
        return self.code
