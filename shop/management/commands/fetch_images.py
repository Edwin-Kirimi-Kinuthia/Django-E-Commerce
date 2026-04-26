"""
Management command: fetch_images
---------------------------------
Downloads product and carousel-slide images from picsum.photos (CDN).
Each product gets a consistent image via a seeded URL — no internet
dependency on fakestoreapi.com.

Usage:
    python manage.py fetch_images
    python manage.py fetch_images --force   # re-download even if image exists
"""

import urllib.request
import hashlib

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from shop.models import FeaturedSlide, Product


# picsum.photos seed-based URLs — same seed always returns the same photo.
# Seeds are chosen to return category-appropriate looking images.
PRODUCT_SEEDS = {
    "Fjallraven Foldsack Backpack":                           "backpack-brown",
    "Mens Casual Premium Slim Fit T-Shirts":                  "tshirt-mens",
    "Mens Cotton Jacket":                                     "jacket-cotton",
    "Mens Casual Slim Fit Chinos":                            "chinos-mens",
    "John Hardy Women's Gold Bracelet":                       "bracelet-gold",
    "Solid Gold Petite Micropave Earrings":                   "earrings-gold",
    "White Gold Plated Princess Necklace":                    "necklace-silver",
    "Pierced Owl Rose Gold Plated Earrings":                  "earrings-rose",
    "WD 2TB USB 3.0 External Hard Drive":                     "harddrive-wd",
    "SanDisk SSD PLUS 1TB Internal SSD":                      "ssd-sandisk",
    "Silicon Power 256GB SSD":                                "ssd-silicon",
    "WD 4TB Gaming Drive – Works with PS4":                   "gaming-drive",
    'Acer SB220Q 21.5" Full HD IPS Monitor':                  "monitor-acer",
    'Samsung 49" CHG90 144Hz Gaming Monitor':                 "monitor-samsung",
    "MBJ Women's Solid Short Sleeve Boat Neck V Bar Blouse":  "blouse-womens",
    "Opna Women's Short Sleeve Moisture Tunic":               "tunic-womens",
    "DANVOUY Womens T Shirt Casual Cotton Short":             "tshirt-womens",
    "Rain Jacket Women Windbreaker Striped":                  "jacket-rain",
    "Lock and Love Women's Removable Hooded Faux Leather Jacket": "jacket-leather",
    "Mens Casual Athleisure Shorts":                          "shorts-mens",
}

SLIDE_SEEDS = {
    "Today's Best Deals":  "deals-banner",
    "New Season Arrivals": "season-arrivals",
    "Jewellery Sale":      "jewellery-banner",
    "Gaming Peripherals":  "gaming-banner",
}


def _picsum_url(seed: str, w: int = 400, h: int = 400) -> str:
    return f"https://picsum.photos/seed/{seed}/{w}/{h}"


def _fetch(url: str, timeout: int = 20) -> bytes | None:
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/jpeg,image/*',
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        return None


class Command(BaseCommand):
    help = 'Download product/slide images from picsum.photos (seed-consistent CDN photos)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Re-download even if an image already exists')

    def handle(self, *args, **options):
        force = options['force']
        ok = skipped = failed = 0

        # ── Products ──────────────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('=== Products ==='))
        for product in Product.objects.all():
            if product.image and not force:
                self.stdout.write(f'  [=] {product.name}')
                skipped += 1
                continue

            seed = PRODUCT_SEEDS.get(product.name)
            if not seed:
                # Auto-generate a seed from the product slug so every
                # product gets a consistent image even if not in the map
                seed = product.slug[:20]

            url = _picsum_url(seed, 400, 400)
            self.stdout.write(f'  [↓] {product.name}')
            data = _fetch(url)
            if data:
                product.image.save(f'{product.slug}.jpg', ContentFile(data), save=True)
                self.stdout.write(self.style.SUCCESS(f'      ✓ saved'))
                ok += 1
            else:
                self.stdout.write(self.style.WARNING(f'      ✗ failed'))
                failed += 1

        # ── Carousel Slides ───────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('=== Carousel Slides ==='))
        for slide in FeaturedSlide.objects.all():
            if slide.image and not force:
                self.stdout.write(f'  [=] {slide.title}')
                skipped += 1
                continue

            seed = SLIDE_SEEDS.get(slide.title, f'slide-{slide.order}')
            url = _picsum_url(seed, 1200, 450)
            self.stdout.write(f'  [↓] {slide.title}')
            data = _fetch(url)
            if data:
                slide.image.save(f'slide-{slide.order}.jpg', ContentFile(data), save=True)
                self.stdout.write(self.style.SUCCESS(f'      ✓ saved'))
                ok += 1
            else:
                self.stdout.write(self.style.WARNING(f'      ✗ failed'))
                failed += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done — {ok} downloaded, {skipped} already had image, {failed} failed'
        ))
