import stripe
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.views.decorators.http import require_POST

from coupons.models import Coupon
from order.models import Order, OrderItem
from shop.models import Product, ProductVariant

from .models import Cart, CartItem


# ─── helpers ──────────────────────────────────────────────────────────────────

def _cart_id(request):
    """Return (and create if needed) the session-based cart key."""
    key = request.session.session_key
    if not key:
        request.session.create()
        key = request.session.session_key
    return key


def _get_cart_items(request):
    """Return active CartItems for the current session cart."""
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        return CartItem.objects.filter(cart=cart, active=True)
    except Cart.DoesNotExist:
        return CartItem.objects.none()


def _cart_total(cart_items):
    total = Decimal('0.00')
    for item in cart_items:
        price = item.product.effective_price
        if item.variant_id and item.variant and item.variant.price_modifier:
            price += item.variant.price_modifier
        total += price * item.quantity
    return total


# ─── cart views ───────────────────────────────────────────────────────────────

def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

    # Honour variant selection from the product detail page
    variant = None
    variant_id = request.GET.get('variant_id') or request.POST.get('variant_id')
    if variant_id:
        variant = ProductVariant.objects.filter(id=variant_id, product=product).first()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, variant=variant)
        stock = variant.stock if variant else product.stock
        if cart_item.quantity < stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(product=product, quantity=1, cart=cart, variant=variant)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart_items = _get_cart_items(request)
    total = _cart_total(cart_items)
    counter = sum(item.quantity for item in cart_items)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'counter': counter,
    })


def cart_remove(request, product_id):
    cart = get_object_or_404(Cart, cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart:cart_detail')


def full_remove(request, product_id):
    cart = get_object_or_404(Cart, cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    get_object_or_404(CartItem, product=product, cart=cart).delete()
    return redirect('cart:cart_detail')


# ─── checkout (Stripe Payment Intents) ────────────────────────────────────────

def checkout(request):
    """Show checkout page; create a fresh PaymentIntent for the cart total."""
    cart_items = _get_cart_items(request)
    if not cart_items:
        return redirect('cart:cart_detail')

    total = _cart_total(cart_items)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    intent = stripe.PaymentIntent.create(
        amount=int(total * 100),
        currency='gbp',
        automatic_payment_methods={'enabled': True},
        metadata={'cart_id': _cart_id(request)},
    )

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'client_secret': intent.client_secret,
    })


@require_POST
def validate_coupon(request):
    """AJAX endpoint — returns coupon discount info."""
    code = request.POST.get('code', '').strip().upper()
    cart_items = _get_cart_items(request)
    total = _cart_total(cart_items)

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Coupon code not found.'})

    valid, msg = coupon.is_valid(order_total=total)
    if not valid:
        return JsonResponse({'valid': False, 'error': msg})

    discount = coupon.calculate_discount(total)
    new_total = max(Decimal('0.00'), total - discount)
    return JsonResponse({
        'valid': True,
        'discount': str(discount),
        'new_total': str(new_total),
        'message': f'Coupon applied! You save £{discount}.',
    })


@require_POST
def checkout_confirm(request):
    """
    After Stripe.js confirms payment on the client side, this view receives
    the PaymentIntent ID, verifies it server-side, creates the Order, and
    redirects to the thank-you page.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payment_intent_id = request.POST.get('payment_intent_id', '')
    coupon_code = request.POST.get('coupon_code', '').strip().upper()
    email = request.POST.get('email', '')
    billing_name = request.POST.get('billing_name', '')
    billing_address1 = request.POST.get('billing_address1', '')
    billing_city = request.POST.get('billing_city', '')
    billing_state = request.POST.get('billing_state', '')
    billing_postcode = request.POST.get('billing_postcode', '')
    billing_country = request.POST.get('billing_country', '')
    shipping_name = request.POST.get('shipping_name', '')
    shipping_address1 = request.POST.get('shipping_address1', '')
    shipping_city = request.POST.get('shipping_city', '')
    shipping_state = request.POST.get('shipping_state', '')
    shipping_postcode = request.POST.get('shipping_postcode', '')
    shipping_country = request.POST.get('shipping_country', '')

    # Verify payment with Stripe
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except stripe.error.StripeError:
        return render(request, 'checkout.html', {'error': 'Payment verification failed. Please try again.'})

    if intent.status != 'succeeded':
        return render(request, 'checkout.html', {'error': f'Payment not completed (status: {intent.status}).'})

    cart_items = _get_cart_items(request)
    if not cart_items:
        return redirect('cart:cart_detail')

    total = _cart_total(cart_items)

    # Apply coupon
    discount_amount = Decimal('0.00')
    applied_coupon_code = ''
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code)
            valid, _ = coupon.is_valid(order_total=total)
            if valid:
                discount_amount = coupon.calculate_discount(total)
                applied_coupon_code = coupon.code
                coupon.uses_count += 1
                coupon.save(update_fields=['uses_count'])
        except Coupon.DoesNotExist:
            pass

    final_total = max(Decimal('0.00'), total - discount_amount)

    # Create order
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        token=payment_intent_id,
        total=final_total,
        discount_amount=discount_amount,
        coupon_code=applied_coupon_code,
        emailAddress=email,
        status=Order.CONFIRMED,
        billingName=billing_name,
        billingAddress1=billing_address1,
        billingCity=billing_city,
        billingState=billing_state,
        billingPostcode=billing_postcode,
        billingCountry=billing_country,
        shippingName=shipping_name or billing_name,
        shippingAddress1=shipping_address1 or billing_address1,
        shippingCity=shipping_city or billing_city,
        shippingState=shipping_state or billing_state,
        shippingPostcode=shipping_postcode or billing_postcode,
        shippingCountry=shipping_country or billing_country,
    )

    for item in cart_items:
        OrderItem.objects.create(
            product=item.product.name,
            quantity=item.quantity,
            price=item.product.effective_price,
            order=order,
            vendor=item.product.vendor,
        )
        # Reduce stock
        product = item.product
        product.stock = max(0, product.stock - item.quantity)
        product.save(update_fields=['stock'])
        item.delete()

    # Clear the session cart object too
    try:
        Cart.objects.filter(cart_id=_cart_id(request)).delete()
    except Exception:
        pass

    try:
        _send_order_email(order.id)
    except Exception:
        pass  # Don't fail the order if email fails

    return redirect('order:thanks', order.id)


# ─── email ────────────────────────────────────────────────────────────────────

def _send_order_email(order_id):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)
    subject = f'ShopMart — Order Confirmed #{transaction.id}'
    to = [transaction.emailAddress]
    from_email = 'orders@shopmart.com'
    message = get_template('email/email.html').render({
        'transaction': transaction,
        'order_items': order_items,
    })
    msg = EmailMessage(subject, message, to=to, from_email=from_email)
    msg.content_subtype = 'html'
    msg.send()


# Keep old name for any legacy references
def sendEmail(order_id):
    _send_order_email(order_id)
