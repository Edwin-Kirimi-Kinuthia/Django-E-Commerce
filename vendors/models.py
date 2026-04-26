from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Vendor(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor')
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    logo = models.ImageField(upload_to='vendors/logos', blank=True)
    banner = models.ImageField(upload_to='vendors/banners', blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        help_text='Platform commission percentage (0-100)',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Vendor.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def product_count(self):
        return self.products.filter(available=True).count()

    def get_absolute_url(self):
        return reverse('vendors:storefront', args=[self.slug])

    def __str__(self):
        return self.name


class VendorShipment(models.Model):
    """One shipment record per vendor per order — tracks carrier/tracking details."""

    CARRIER_TPC   = 'tpc'
    CARRIER_DHL   = 'dhl'
    CARRIER_FEDEX = 'fedex'
    CARRIER_ARAMEX = 'aramex'
    CARRIER_COURIER = 'courier'
    CARRIER_SELF  = 'self'
    CARRIER_OTHER = 'other'
    CARRIER_CHOICES = [
        (CARRIER_TPC,    'Tanzania Posts Corporation'),
        (CARRIER_DHL,    'DHL Express'),
        (CARRIER_FEDEX,  'FedEx'),
        (CARRIER_ARAMEX, 'Aramex'),
        (CARRIER_COURIER,'Local Courier'),
        (CARRIER_SELF,   'Self / Hand Delivery'),
        (CARRIER_OTHER,  'Other'),
    ]

    order = models.ForeignKey(
        'order.Order', on_delete=models.CASCADE, related_name='shipments',
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='shipments',
    )
    carrier = models.CharField(max_length=20, choices=CARRIER_CHOICES)
    carrier_other = models.CharField(
        max_length=100, blank=True,
        help_text='Carrier name if "Other" is selected',
    )
    tracking_number = models.CharField(max_length=200, blank=True)
    tracking_url = models.URLField(
        blank=True,
        help_text='Optional direct tracking link (e.g. https://track.dhl.com/...)',
    )
    estimated_delivery = models.DateField(
        null=True, blank=True,
        help_text='Expected delivery date shown to customer',
    )
    notes = models.TextField(
        blank=True,
        help_text='Packing notes or instructions visible to admin',
    )
    shipped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('order', 'vendor')
        ordering = ['-shipped_at']
        verbose_name = 'Vendor Shipment'
        verbose_name_plural = 'Vendor Shipments'

    @property
    def carrier_display(self):
        if self.carrier == self.CARRIER_OTHER:
            return self.carrier_other or 'Other'
        return self.get_carrier_display()

    def __str__(self):
        return f'Shipment #{self.pk} — {self.vendor.name} / Order #{self.order_id}'


class VendorReview(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=250, blank=True)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('vendor', 'user')
        ordering = ['-created']

    def __str__(self):
        return f'{self.user.username} → {self.vendor.name} ({self.rating}★)'
