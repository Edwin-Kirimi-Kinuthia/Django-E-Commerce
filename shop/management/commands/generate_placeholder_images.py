"""
Management command: generate_placeholder_images
------------------------------------------------
Creates styled placeholder product images and carousel slide images
locally using Pillow — no internet connection required.

Usage:
    python manage.py generate_placeholder_images
    python manage.py generate_placeholder_images --force   # overwrite existing
"""

import io
import textwrap

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from shop.models import FeaturedSlide, Product

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


# Colour palette per category slug
CATEGORY_PALETTE = {
    'electronics':   ('#1a1a2e', '#e94560', '#ffffff'),   # dark navy / red
    'clothing':      ('#2d6a4f', '#52b788', '#ffffff'),   # forest green
    'jewellery':     ('#4a1942', '#c77dff', '#ffffff'),   # deep purple / violet
    'mens-fashion':  ('#1d3557', '#457b9d', '#ffffff'),   # steel blue
    'womens-fashion':('#9d0208', '#f48c06', '#ffffff'),   # crimson / amber
}
DEFAULT_PALETTE = ('#2b2d42', '#8d99ae', '#ffffff')

# Slide accent colours
SLIDE_PALETTE = {
    "Today's Best Deals":  ('#0d1b2a', '#1b4332', '#ffffff'),
    "New Season Arrivals": ('#3d405b', '#81b29a', '#ffffff'),
    "Jewellery Sale":      ('#240046', '#9d4edd', '#ffffff'),
    "Gaming Peripherals":  ('#03071e', '#e85d04', '#ffffff'),
}


def _wrap(text, max_chars=18):
    """Break long text into lines."""
    return '\n'.join(textwrap.wrap(text, max_chars))


def _make_product_image(name: str, brand: str, category_slug: str, size=(400, 400)) -> bytes:
    bg, accent, fg = CATEGORY_PALETTE.get(category_slug, DEFAULT_PALETTE)
    w, h = size

    img = Image.new('RGB', (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Accent bar at bottom
    draw.rectangle([0, h - 80, w, h], fill=accent)

    # Decorative circles
    draw.ellipse([-60, -60, 180, 180], outline=accent, width=6)
    draw.ellipse([w - 120, h - 200, w + 40, h - 40], outline=accent, width=3)

    # Product name (large)
    lines = _wrap(name, 16)
    try:
        font_big = ImageFont.truetype("arial.ttf", 26)
        font_sm  = ImageFont.truetype("arial.ttf", 18)
        font_brand = ImageFont.truetype("arial.ttf", 15)
    except Exception:
        font_big = ImageFont.load_default()
        font_sm  = font_big
        font_brand = font_big

    # Draw name centred
    y = 130
    for line in lines.split('\n'):
        bbox = draw.textbbox((0, 0), line, font=font_big)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) / 2, y), line, font=font_big, fill=fg)
        y += 34

    # Brand in accent bar
    if brand:
        b_bbox = draw.textbbox((0, 0), brand, font=font_brand)
        bw = b_bbox[2] - b_bbox[0]
        draw.text(((w - bw) / 2, h - 55), brand, font=font_brand, fill='#ffffff')

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def _make_slide_image(title: str, subtitle: str, size=(900, 350)) -> bytes:
    bg, accent, fg = SLIDE_PALETTE.get(title, ('#1d3557', '#e63946', '#ffffff'))
    w, h = size

    img = Image.new('RGB', (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Diagonal accent stripe
    draw.polygon([(w * 0.55, 0), (w, 0), (w, h), (w * 0.7, h)], fill=accent)

    # Decorative shapes
    draw.ellipse([w * 0.6, -50, w * 0.95, h * 0.8], outline='#ffffff22', width=40)

    try:
        font_title    = ImageFont.truetype("arial.ttf", 48)
        font_subtitle = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_title    = ImageFont.load_default()
        font_subtitle = font_title

    # Title
    t_bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text((60, h // 2 - 50), title, font=font_title, fill=fg)

    # Subtitle
    if subtitle:
        draw.text((60, h // 2 + 20), subtitle, font=font_subtitle, fill='#cccccc')

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


class Command(BaseCommand):
    help = 'Generate placeholder product and slide images locally using Pillow'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Overwrite images even if one already exists')

    def handle(self, *args, **options):
        if not HAS_PILLOW:
            self.stdout.write(self.style.ERROR(
                'Pillow is not installed. Run:  pip install Pillow'
            ))
            return

        force = options['force']
        ok = skipped = 0

        # ── Products ──────────────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('=== Products ==='))
        for product in Product.objects.select_related('category').all():
            if product.image and not force:
                self.stdout.write(f'  [=] skip (has image): {product.name}')
                skipped += 1
                continue

            cat_slug = product.category.slug if product.category else ''
            data = _make_product_image(product.name, product.brand or '', cat_slug)
            filename = f'{product.slug}.jpg'
            product.image.save(filename, ContentFile(data), save=True)
            self.stdout.write(self.style.SUCCESS(f'  [✓] {product.name}'))
            ok += 1

        # ── Carousel Slides ───────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('=== Carousel Slides ==='))
        for slide in FeaturedSlide.objects.all():
            if slide.image and not force:
                self.stdout.write(f'  [=] skip (has image): {slide.title}')
                skipped += 1
                continue

            data = _make_slide_image(slide.title, slide.subtitle)
            filename = f'slide-{slide.order}.jpg'
            slide.image.save(filename, ContentFile(data), save=True)
            self.stdout.write(self.style.SUCCESS(f'  [✓] {slide.title}'))
            ok += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done — {ok} generated, {skipped} skipped.'
        ))
