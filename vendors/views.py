from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from order.models import Order, OrderItem
from shop.models import Category, Product

from .models import Vendor, VendorReview, VendorShipment


# ── Decorator ────────────────────────────────────────────────────────────────

def vendor_required(view_func):
    """Require the logged-in user to have an approved Vendor profile."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            vendor = request.user.vendor
        except Vendor.DoesNotExist:
            messages.info(request, 'You need to apply as a vendor first.')
            return redirect('vendors:apply')
        if not vendor.is_approved:
            return render(request, 'vendors/pending.html', {'vendor': vendor})
        return view_func(request, *args, vendor=vendor, **kwargs)
    return wrapper


# ── Public views ─────────────────────────────────────────────────────────────

def vendor_list(request):
    vendors = Vendor.objects.filter(status=Vendor.STATUS_APPROVED)
    # Simple search
    q = request.GET.get('q', '').strip()
    if q:
        vendors = vendors.filter(name__icontains=q)

    paginator = Paginator(vendors, 12)
    try:
        page = paginator.page(int(request.GET.get('page', 1)))
    except (EmptyPage, InvalidPage, ValueError):
        page = paginator.page(paginator.num_pages)

    return render(request, 'vendors/vendor_list.html', {
        'vendors': page,
        'paginator': paginator,
        'page_obj': page,
        'query': q,
    })


def storefront(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug, status=Vendor.STATUS_APPROVED)
    products = vendor.products.filter(available=True)

    # Sort
    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'newest': '-created',
        'price_asc': 'price',
        'price_desc': '-price',
        'name': 'name',
    }
    products = products.order_by(sort_map.get(sort, '-created'))

    paginator = Paginator(products, 12)
    try:
        page = paginator.page(int(request.GET.get('page', 1)))
    except (EmptyPage, InvalidPage, ValueError):
        page = paginator.page(paginator.num_pages)

    # Vendor review form handling
    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating', '').strip()
        body = request.POST.get('body', '').strip()
        if rating and body:
            VendorReview.objects.update_or_create(
                vendor=vendor, user=request.user,
                defaults={'rating': int(rating), 'title': request.POST.get('title', ''), 'body': body}
            )
            messages.success(request, 'Your review has been submitted.')
        return redirect('vendors:storefront', slug=slug)

    return render(request, 'vendors/storefront.html', {
        'vendor': vendor,
        'products': page,
        'page_obj': page,
        'paginator': paginator,
        'sort': sort,
        'reviews': vendor.reviews.all()[:10],
    })


# ── Vendor application ────────────────────────────────────────────────────────

@login_required
def apply(request):
    # Redirect if already a vendor
    if hasattr(request.user, 'vendor'):
        if request.user.vendor.is_approved:
            return redirect('vendors:dashboard')
        return render(request, 'vendors/pending.html', {'vendor': request.user.vendor})

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        website = request.POST.get('website', '').strip()
        logo = request.FILES.get('logo')
        if name:
            vendor = Vendor(
                user=request.user,
                name=name,
                description=description,
                address=address,
                phone=phone,
                website=website,
            )
            if logo:
                vendor.logo = logo
            vendor.save()
            messages.success(request, 'Application submitted! We will review and approve your store soon.')
            return redirect('vendors:pending')
        messages.error(request, 'Store name is required.')

    return render(request, 'vendors/apply.html')


@login_required
def pending(request):
    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        return redirect('vendors:apply')
    if vendor.is_approved:
        return redirect('vendors:dashboard')
    return render(request, 'vendors/pending.html', {'vendor': vendor})


# ── Vendor dashboard ─────────────────────────────────────────────────────────

@vendor_required
def dashboard(request, vendor):
    from django.utils.timezone import now
    from datetime import timedelta
    thirty_days_ago = now() - timedelta(days=30)

    # Revenue = sum of order items sold by this vendor (confirmed/shipped/delivered)
    sold_items = OrderItem.objects.filter(
        vendor=vendor,
        order__status__in=[Order.CONFIRMED, Order.SHIPPED, Order.DELIVERED],
    )
    recent_sold = sold_items.filter(order__created__gte=thirty_days_ago)

    stats = {
        'revenue_30d': recent_sold.aggregate(
            total=Sum('price')
        )['total'] or Decimal('0.00'),
        'orders_30d': recent_sold.values('order').distinct().count(),
        'total_products': vendor.products.count(),
        'active_products': vendor.products.filter(available=True).count(),
        'low_stock': vendor.products.filter(stock__lte=5, available=True).count(),
        'avg_rating': vendor.average_rating,
        'review_count': vendor.review_count,
    }

    # Recent orders containing this vendor's items
    recent_orders = (
        Order.objects.filter(items__vendor=vendor)
        .distinct()
        .order_by('-created')[:10]
    )

    return render(request, 'vendors/dashboard.html', {
        'vendor': vendor,
        'stats': stats,
        'recent_orders': recent_orders,
    })


@vendor_required
def product_list(request, vendor):
    products = vendor.products.all().order_by('-created')

    # Filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        products = products.filter(available=True)
    elif status_filter == 'inactive':
        products = products.filter(available=False)
    elif status_filter == 'low_stock':
        products = products.filter(stock__lte=5)

    paginator = Paginator(products, 20)
    try:
        page = paginator.page(int(request.GET.get('page', 1)))
    except (EmptyPage, InvalidPage, ValueError):
        page = paginator.page(paginator.num_pages)

    return render(request, 'vendors/product_list.html', {
        'vendor': vendor,
        'products': page,
        'page_obj': page,
        'status_filter': status_filter,
    })


@vendor_required
def product_add(request, vendor):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Product name is required.')
            return render(request, 'vendors/product_form.html', {'vendor': vendor, 'categories': categories, 'action': 'Add'})

        slug = slugify(name)
        # Ensure unique slug
        base_slug = slug
        n = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{n}'
            n += 1

        product = Product(
            name=name,
            slug=slug,
            description=request.POST.get('description', ''),
            price=request.POST.get('price', 0),
            discount_price=request.POST.get('discount_price') or None,
            stock=request.POST.get('stock', 0),
            brand=request.POST.get('brand', ''),
            sku=request.POST.get('sku') or None,
            weight=request.POST.get('weight') or None,
            vendor=vendor,
            available=bool(request.POST.get('available')),
        )
        cat_id = request.POST.get('category')
        if cat_id:
            product.category = get_object_or_404(Category, id=cat_id)
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, f'"{product.name}" added successfully.')
        return redirect('vendors:product_list')

    return render(request, 'vendors/product_form.html', {
        'vendor': vendor, 'categories': categories, 'action': 'Add',
    })


@vendor_required
def product_edit(request, vendor, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.discount_price = request.POST.get('discount_price') or None
        product.stock = request.POST.get('stock', product.stock)
        product.brand = request.POST.get('brand', product.brand)
        product.sku = request.POST.get('sku') or None
        product.weight = request.POST.get('weight') or None
        product.available = bool(request.POST.get('available'))
        cat_id = request.POST.get('category')
        if cat_id:
            product.category = get_object_or_404(Category, id=cat_id)
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, f'"{product.name}" updated.')
        return redirect('vendors:product_list')

    return render(request, 'vendors/product_form.html', {
        'vendor': vendor, 'product': product,
        'categories': categories, 'action': 'Edit',
    })


@vendor_required
@require_POST
def product_delete(request, vendor, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    name = product.name
    product.delete()
    messages.success(request, f'"{name}" deleted.')
    return redirect('vendors:product_list')


@vendor_required
def orders(request, vendor):
    order_qs = (
        Order.objects.filter(items__vendor=vendor)
        .distinct()
        .order_by('-created')
    )

    status_filter = request.GET.get('status', '')
    if status_filter:
        order_qs = order_qs.filter(status=status_filter)

    paginator = Paginator(order_qs, 20)
    try:
        page = paginator.page(int(request.GET.get('page', 1)))
    except (EmptyPage, InvalidPage, ValueError):
        page = paginator.page(paginator.num_pages)

    return render(request, 'vendors/orders.html', {
        'vendor': vendor,
        'orders': page,
        'page_obj': page,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    })


@vendor_required
def order_detail(request, vendor, order_id):
    order = get_object_or_404(
        Order.objects.filter(items__vendor=vendor).distinct(),
        id=order_id,
    )
    my_items = order.items.filter(vendor=vendor)
    my_revenue = my_items.aggregate(total=Sum('price'))['total'] or Decimal('0.00')
    shipment = VendorShipment.objects.filter(order=order, vendor=vendor).first()

    return render(request, 'vendors/order_detail.html', {
        'vendor': vendor,
        'order': order,
        'my_items': my_items,
        'my_revenue': my_revenue,
        'shipment': shipment,
        'carrier_choices': VendorShipment.CARRIER_CHOICES,
        # Non-ship transitions a vendor can still do (confirm, cancel, deliver)
        'can_confirm': order.status == Order.PENDING,
        'can_cancel':  order.status in (Order.PENDING, Order.CONFIRMED),
        'can_deliver': order.status == Order.SHIPPED and shipment is not None,
        'can_ship':    order.status == Order.CONFIRMED and shipment is None,
    })


@vendor_required
@require_POST
def update_order_status(request, vendor, order_id):
    """Handle simple status transitions (confirm, cancel, mark delivered)."""
    order = get_object_or_404(
        Order.objects.filter(items__vendor=vendor).distinct(),
        id=order_id,
    )
    new_status = request.POST.get('status', '').strip()

    # Allowed non-shipping transitions
    transitions = {
        Order.PENDING:   [Order.CONFIRMED, Order.CANCELLED],
        Order.CONFIRMED: [Order.CANCELLED],
        Order.SHIPPED:   [Order.DELIVERED],
    }
    allowed = transitions.get(order.status, [])
    if new_status in allowed:
        order.status = new_status
        order.save(update_fields=['status', 'updated'])
        messages.success(request, f'Order #{order.id} marked as {order.get_status_display()}.')
    else:
        messages.error(request, 'Invalid status transition.')
    return redirect('vendors:order_detail', order_id=order.id)


@vendor_required
@require_POST
def ship_order(request, vendor, order_id):
    """Mark an order as shipped: capture shipment details and email the customer."""
    order = get_object_or_404(
        Order.objects.filter(items__vendor=vendor, status=Order.CONFIRMED).distinct(),
        id=order_id,
    )
    # Guard: only one shipment per vendor per order
    if VendorShipment.objects.filter(order=order, vendor=vendor).exists():
        messages.error(request, 'This order has already been marked as shipped.')
        return redirect('vendors:order_detail', order_id=order.id)

    carrier = request.POST.get('carrier', '').strip()
    if not carrier:
        messages.error(request, 'Please select a carrier.')
        return redirect('vendors:order_detail', order_id=order.id)

    shipment = VendorShipment.objects.create(
        order=order,
        vendor=vendor,
        carrier=carrier,
        carrier_other=request.POST.get('carrier_other', '').strip(),
        tracking_number=request.POST.get('tracking_number', '').strip(),
        tracking_url=request.POST.get('tracking_url', '').strip(),
        notes=request.POST.get('notes', '').strip(),
        estimated_delivery=request.POST.get('estimated_delivery') or None,
    )

    # Advance the order status to Shipped
    order.status = Order.SHIPPED
    order.save(update_fields=['status', 'updated'])

    # Email the customer
    if order.emailAddress:
        try:
            shipped_items = order.items.filter(vendor=vendor)
            html_body = render_to_string('vendors/email/shipment_notification.html', {
                'order': order,
                'shipment': shipment,
                'shipped_items': shipped_items,
            })
            email = EmailMessage(
                subject=f'Your ShopMart order #{order.id} has shipped!',
                body=html_body,
                to=[order.emailAddress],
            )
            email.content_subtype = 'html'
            email.send(fail_silently=True)
        except Exception:
            pass  # Never let email failure block the shipping action

    messages.success(
        request,
        f'Order #{order.id} marked as shipped.'
        + (f' Tracking: {shipment.tracking_number}' if shipment.tracking_number else '')
    )
    return redirect('vendors:order_detail', order_id=order.id)


@vendor_required
def profile_edit(request, vendor):
    if request.method == 'POST':
        vendor.name = request.POST.get('name', vendor.name).strip()
        vendor.description = request.POST.get('description', vendor.description)
        vendor.address = request.POST.get('address', vendor.address)
        vendor.phone = request.POST.get('phone', vendor.phone)
        vendor.website = request.POST.get('website', vendor.website)
        if 'logo' in request.FILES:
            vendor.logo = request.FILES['logo']
        if 'banner' in request.FILES:
            vendor.banner = request.FILES['banner']
        vendor.save()
        messages.success(request, 'Store profile updated.')
        return redirect('vendors:dashboard')

    return render(request, 'vendors/profile_edit.html', {'vendor': vendor})
