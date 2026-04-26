from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category', blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('shop:products_by_category', args=[self.slug])

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    vendor = models.ForeignKey(
        'vendors.Vendor', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products',
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='product', blank=True)
    stock = models.IntegerField()
    available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text='Show in homepage carousel')
    brand = models.CharField(max_length=250, blank=True)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Weight in kg')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'product'
        verbose_name_plural = 'products'

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def get_percent_discount(self):
        if self.discount_price and self.price:
            return round((1 - float(self.discount_price) / float(self.price)) * 100)
        return 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= 5

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    @property
    def review_count(self):
        return self.reviews.count()

    def get_url(self):
        return reverse('shop:ProdCatDetail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.name


class FeaturedSlide(models.Model):
    """Manually curated carousel slides for the homepage."""
    title = models.CharField(max_length=250)
    subtitle = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to='carousel')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='slides',
        help_text='Link slide to this product (leave blank to use custom URL)',
    )
    custom_url = models.CharField(
        max_length=500, blank=True,
        help_text='Used only when no product is selected',
    )
    cta_text = models.CharField(max_length=100, default='Shop Now')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    @property
    def link(self):
        if self.product:
            return self.product.get_url()
        return self.custom_url or '/'

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product/gallery')
    alt_text = models.CharField(max_length=250, blank=True)
    is_feature = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        # Ensure only one featured image per product
        if self.is_feature:
            ProductImage.objects.filter(
                product=self.product, is_feature=True
            ).exclude(pk=self.pk).update(is_feature=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.name} image {self.id}'


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text='e.g. Size, Color')
    value = models.CharField(max_length=100, help_text='e.g. XL, Red')
    price_modifier = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Added to base product price (can be negative)',
    )
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('product', 'name', 'value')
        ordering = ['name', 'value']

    def __str__(self):
        return f'{self.product.name} — {self.name}: {self.value}'


class ProductAttribute(models.Model):
    """
    Flexible key-value attributes for any product type.
    Clothing: Color, Material, Fit, Care…
    Electronics: RAM, Storage, Display…
    Jewellery: Metal Type, Stone, Purity…
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    name    = models.CharField(max_length=100, help_text='e.g. Material, Color, Care Instructions')
    value   = models.CharField(max_length=500, help_text='e.g. 100% Cotton, Navy Blue, Machine wash 30°C')

    class Meta:
        ordering = ['name']
        unique_together = ('product', 'name')

    def __str__(self):
        return f'{self.product.name} — {self.name}: {self.value}'


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=250, blank=True)
    body = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created']

    def __str__(self):
        return f'{self.user.username} — {self.product.name} ({self.rating}★)'
