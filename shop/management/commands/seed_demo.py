"""
Management command: seed_demo
------------------------------
Populates the database with demo categories, products (with real images
fetched from the free FakeStore API), a vendor, featured slides, and a
superuser so you can test the site immediately.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # wipe existing data first
"""

import io
import os
import urllib.request

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from shop.models import Category, FeaturedSlide, Product
from vendors.models import Vendor


# ---------------------------------------------------------------------------
# Product data — uses free images from FakeStore API + picsum for banners
# ---------------------------------------------------------------------------

CATEGORIES = [
    {'name': 'Electronics',    'slug': 'electronics'},
    {'name': 'Clothing',       'slug': 'clothing'},
    {'name': 'Jewellery',      'slug': 'jewellery'},
    {'name': "Men's Fashion",  'slug': 'mens-fashion'},
    {"name": "Women's Fashion", "slug": "womens-fashion"},
]

# Each entry: name, category_slug, price, discount_price, stock, brand, description, img_url, is_featured
PRODUCTS = [
    # Electronics
    (
        "Fjallraven Foldsack Backpack", "electronics", 109.95, 89.95, 120, "Fjallraven",
        "Your perfect pack for everyday use and walks in the forest. Stash your laptop up to 15\" and all your epicurean assets.",
        "https://fakestoreapi.com/img/81fAn1w4lML._AC_UY879_.jpg", True,
    ),
    (
        "Mens Casual Premium Slim Fit T-Shirts", "clothing", 22.30, None, 200, "H&M",
        "Slim-fitting style, contrast raglan long sleeve, three-button henley placket. Light weight and soft fabric for breathable wear.",
        "https://fakestoreapi.com/img/71-3HjGNDUL._AC_SY879._SX._UX._SY._UY_.jpg", True,
    ),
    (
        "Mens Cotton Jacket", "mens-fashion", 55.99, 49.99, 80, "Calvin Klein",
        "Great outerwear jackets for Spring/Autumn/Winter. Fully Lined, lightweight, and warm. Adjustable hood for windy days.",
        "https://fakestoreapi.com/img/71li-ujtlUL._AC_UX679_.jpg", True,
    ),
    (
        "Mens Casual Slim Fit Chinos", "mens-fashion", 15.99, None, 300, "Levi's",
        "The color could be slightly different between on the screen and in practice. Please note that body builds vary by person, therefore, we highly recommend to review the size chart before making your purchase.",
        "https://fakestoreapi.com/img/71YXzeOuslL._AC_UY879_.jpg", False,
    ),
    (
        "John Hardy Women's Gold Bracelet", "jewellery", 695.00, 599.00, 30, "John Hardy",
        "From our Legends Collection, the Naga Dragon is a symbol of good luck. The real gold accents on the traditional bracelet represent wealth and prosperity.",
        "https://fakestoreapi.com/img/71pWzhdJNwL._AC_UL640_FMwebp_QL65_.jpg", True,
    ),
    (
        "Solid Gold Petite Micropave Earrings", "jewellery", 168.00, None, 50, "Stud Republic",
        "Satisfaction Guaranteed. Return or exchange any order within 30 days. Designed and sold by Hafeez Center in the United States.",
        "https://fakestoreapi.com/img/61sbMiUnoGL._AC_UL640_FMwebp_QL65_.jpg", False,
    ),
    (
        "White Gold Plated Princess Necklace", "jewellery", 9.99, None, 150, "Zaveri Pearls",
        "Classic Created Wedding Engagement Solitaire Diamond Promise Ring for Her. Size 7, 8, 9, 10.",
        "https://fakestoreapi.com/img/71YAIFU48IL._AC_UL640_FMwebp_QL65_.jpg", False,
    ),
    (
        "Pierced Owl Rose Gold Plated Earrings", "jewellery", 10.99, None, 200, "Pierced Owl",
        "Rose Gold Plated Double Flared Tunnel Plug Earrings. Made of 316L Stainless Steel.",
        "https://fakestoreapi.com/img/51UDEzMJVpL._AC_UL640_FMwebp_QL65_.jpg", False,
    ),
    (
        "WD 2TB USB 3.0 External Hard Drive", "electronics", 64.00, 54.00, 90, "Western Digital",
        "USB 3.0 and USB 2.0 Compatibility. Fast data transfers. Improve PC Performance. High Capacity; Compatibility Formatted NTFS for Windows 10.",
        "https://fakestoreapi.com/img/61IBBVJvSDL._AC_SY879_.jpg", True,
    ),
    (
        "SanDisk SSD PLUS 1TB Internal SSD", "electronics", 109.00, 94.99, 60, "SanDisk",
        "Easy installation. Internal drive; connect to any standard SATA III port. Transfer speeds up to 535 MB/s.",
        "https://fakestoreapi.com/img/61U7T1koQqL._AC_SX679_.jpg", False,
    ),
    (
        "Silicon Power 256GB SSD", "electronics", 109.00, None, 75, "Silicon Power",
        "3D NAND flash are applied to deliver high transfer speeds. TRIM and GC Technologies, Wear Leveling.",
        "https://fakestoreapi.com/img/71kWymZ+c+L._AC_SX679_.jpg", False,
    ),
    (
        "WD 4TB Gaming Drive – Works with PS4", "electronics", 114.00, 99.00, 45, "Western Digital",
        "Expand your PS4 gaming experience. Play anywhere. Keep it simple. Double Tap to Wake.",
        "https://fakestoreapi.com/img/61mtL65D4cL._AC_SX679_.jpg", True,
    ),
    (
        "Acer SB220Q 21.5\" Full HD IPS Monitor", "electronics", 599.00, 549.00, 20, "Acer",
        "21.5 inches Full HD (1920 x 1080) widescreen IPS display. AMD FreeSyncTM premium technology. Refresh rate: 75Hz.",
        "https://fakestoreapi.com/img/81QpkIctqPL._AC_SX679_.jpg", True,
    ),
    (
        "Samsung 49\" CHG90 144Hz Gaming Monitor", "electronics", 999.99, 899.99, 15, "Samsung",
        "49 INCH SUPER ULTRAWIDE: Expand your view with a 49 inch curved gaming monitor. Immerse yourself with a 32:9 aspect ratio.",
        "https://fakestoreapi.com/img/81Zt42ioCgL._AC_SX679_.jpg", True,
    ),
    (
        "MBJ Women's Solid Short Sleeve Boat Neck V Bar Blouse", "womens-fashion", 9.85, None, 250, "MBJ",
        "95% RAYON 5% SPANDEX. Made in USA or Imported. Machine wash cold. Lightweight and soft.",
        "https://fakestoreapi.com/img/71z3kpMAYsL._AC_UY879_.jpg", False,
    ),
    (
        "Opna Women's Short Sleeve Moisture Tunic", "womens-fashion", 7.95, None, 300, "Opna",
        "100% Polyester. Machine wash cold with like colors. Moisture wicking active technology.",
        "https://fakestoreapi.com/img/51eg55uWmdL._AC_UX679_.jpg", False,
    ),
    (
        "DANVOUY Womens T Shirt Casual Cotton Short", "womens-fashion", 12.99, None, 180, "DANVOUY",
        "95%Cotton,5%Spandex. Features: Casual, Short Sleeve, Letter Print,V-Neck,Fashion Tees.",
        "https://fakestoreapi.com/img/61pHAEJ4NML._AC_UX679_.jpg", True,
    ),
    (
        "Rain Jacket Women Windbreaker Striped", "clothing", 39.99, 34.99, 95, "Chouyatou",
        "Lightweight perfect for trip or casual wear. And it's a great fit. Casual style with striped design.",
        "https://fakestoreapi.com/img/71HblAHs1xL._AC_UY879_-2.jpg", False,
    ),
    (
        "Lock and Love Women's Removable Hooded Faux Leather Jacket", "clothing", 29.95, None, 70, "Lock and Love",
        "100% POLYURETHANE(shell) 100% POLYESTER(lining). Front button zipper closure. Detachable hood with adjustable drawstrings.",
        "https://fakestoreapi.com/img/81XH0e8fefL._AC_UY879_.jpg", True,
    ),
    (
        "Mens Casual Athleisure Shorts", "mens-fashion", 15.00, None, 220, "Champion",
        "Slim fitting shorts, multi-pocket design, lightweight and breathable fabric.",
        "https://fakestoreapi.com/img/71-3HjGNDUL._AC_SY879._SX._UX._SY._UY_.jpg", False,
    ),
]

# Carousel slides: title, subtitle, cta, picsum image id, product index (0-based, or None)
SLIDES = [
    ("Today's Best Deals",      "Up to 40% off electronics",           "Shop Electronics", "https://fakestoreapi.com/img/81QpkIctqPL._AC_SX679_.jpg",  8),
    ("New Season Arrivals",     "Fresh styles just landed",            "Explore Fashion",  "https://fakestoreapi.com/img/71li-ujtlUL._AC_UX679_.jpg",   2),
    ("Jewellery Sale",          "Luxury at unbeatable prices",         "Shop Now",         "https://fakestoreapi.com/img/71pWzhdJNwL._AC_UL640_FMwebp_QL65_.jpg", 4),
    ("Gaming Peripherals",      "Level up your setup",                 "See Deals",        "https://fakestoreapi.com/img/81Zt42ioCgL._AC_SX679_.jpg",   13),
]


def _download_image(url: str, timeout: int = 10) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        return None


class Command(BaseCommand):
    help = 'Seed the database with demo products, images, categories, vendor, and superuser'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete existing demo data before seeding')
        parser.add_argument('--no-images', action='store_true', help='Skip image downloads (faster, uses blank images)')

    def handle(self, *args, **options):
        flush = options['flush']
        skip_images = options['no_images']

        if flush:
            self.stdout.write(self.style.WARNING('Flushing existing products, categories, and slides…'))
            FeaturedSlide.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()

        # ── Superuser ──────────────────────────────────────────────────────
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@shopmart.com', 'admin1234')
            self.stdout.write(self.style.SUCCESS('Superuser created  →  admin / admin1234'))
        else:
            self.stdout.write('Superuser already exists — skipped.')

        # ── Categories ────────────────────────────────────────────────────
        cat_map = {}
        for c in CATEGORIES:
            obj, created = Category.objects.get_or_create(
                slug=c['slug'],
                defaults={'name': c['name']},
            )
            cat_map[c['slug']] = obj
            if created:
                self.stdout.write(f'  Category created: {obj.name}')

        # ── Demo vendor ───────────────────────────────────────────────────
        vendor_user, _ = User.objects.get_or_create(
            username='demo_vendor',
            defaults={'email': 'vendor@shopmart.com', 'first_name': 'Demo', 'last_name': 'Vendor'},
        )
        if not hasattr(vendor_user, 'vendor'):
            vendor = Vendor.objects.create(
                user=vendor_user,
                name='ShopMart Official',
                description='Official ShopMart store — curated quality products at the best prices.',
                status=Vendor.STATUS_APPROVED,
                commission_rate=0,
            )
            self.stdout.write(self.style.SUCCESS(f'Vendor created: {vendor.name}'))
        else:
            vendor = vendor_user.vendor
            self.stdout.write(f'Vendor already exists: {vendor.name}')

        # ── Products ──────────────────────────────────────────────────────
        created_products = []
        for idx, (name, cat_slug, price, discount_price, stock, brand, desc, img_url, is_featured) in enumerate(PRODUCTS):
            slug = slugify(name)
            # Ensure slug uniqueness
            base = slug
            n = 1
            while Product.objects.filter(slug=slug).exists():
                # Check if it's the same product name
                if Product.objects.filter(slug=slug, name=name).exists():
                    break
                slug = f'{base}-{n}'
                n += 1

            prod, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slug,
                    'category': cat_map.get(cat_slug, list(cat_map.values())[0]),
                    'vendor': vendor,
                    'price': price,
                    'discount_price': discount_price,
                    'stock': stock,
                    'brand': brand,
                    'description': desc,
                    'available': True,
                    'is_featured': is_featured,
                },
            )

            if created and not skip_images:
                self.stdout.write(f'  [{idx+1}/{len(PRODUCTS)}] Downloading image for: {name}')
                img_data = _download_image(img_url)
                if img_data:
                    ext = img_url.split('.')[-1].split('?')[0]
                    if ext not in ('jpg', 'jpeg', 'png', 'webp'):
                        ext = 'jpg'
                    filename = f'{slug}.{ext}'
                    prod.image.save(filename, ContentFile(img_data), save=True)
                else:
                    self.stdout.write(self.style.WARNING(f'    Could not download image — skipped'))
            elif created:
                self.stdout.write(f'  [{idx+1}/{len(PRODUCTS)}] Created (no image): {name}')

            created_products.append(prod)

        self.stdout.write(self.style.SUCCESS(f'{len(created_products)} products ready.'))

        # ── Featured Slides ───────────────────────────────────────────────
        if not FeaturedSlide.objects.exists():
            self.stdout.write('Creating carousel slides…')
            for order_idx, (title, subtitle, cta, img_url, prod_idx) in enumerate(SLIDES):
                slide = FeaturedSlide(
                    title=title,
                    subtitle=subtitle,
                    cta_text=cta,
                    order=order_idx,
                    is_active=True,
                )
                if prod_idx is not None and prod_idx < len(created_products):
                    slide.product = created_products[prod_idx]

                if not skip_images:
                    self.stdout.write(f'  Downloading slide image: {title}')
                    img_data = _download_image(img_url)
                    if img_data:
                        ext = img_url.split('.')[-1].split('?')[0]
                        if ext not in ('jpg', 'jpeg', 'png', 'webp'):
                            ext = 'jpg'
                        slide.save()
                        slide.image.save(f'slide-{order_idx}.{ext}', ContentFile(img_data), save=True)
                    else:
                        slide.save()
                        self.stdout.write(self.style.WARNING(f'    Could not download slide image'))
                else:
                    slide.save()

            self.stdout.write(self.style.SUCCESS(f'{len(SLIDES)} carousel slides created.'))
        else:
            self.stdout.write('Carousel slides already exist — skipped.')

        # ── Summary ───────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('  Demo data loaded! Ready to test.'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('  Admin login:')
        self.stdout.write('    URL:       http://127.0.0.1:8000/admin/')
        self.stdout.write('    Username:  admin')
        self.stdout.write('    Password:  admin1234')
        self.stdout.write('')
        self.stdout.write('  Site:       http://127.0.0.1:8000/')
        self.stdout.write('')
