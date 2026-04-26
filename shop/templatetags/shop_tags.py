from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def star_rating(rating):
    """Render 5 Font Awesome stars filled/empty based on rating (0-5)."""
    try:
        filled = round(float(rating))
    except (TypeError, ValueError):
        filled = 0
    stars = ''
    for i in range(1, 6):
        if i <= filled:
            stars += '<i class="fas fa-star"></i>'
        else:
            stars += '<i class="far fa-star"></i>'
    return mark_safe(f'<span class="amz-stars">{stars}</span>')


@register.simple_tag(takes_context=True)
def price(context, value):
    """
    Convert a GBP price to the visitor's currency and render with symbol.
    Usage: {% price product.effective_price %}
    """
    try:
        amount = float(value)
        rate   = float(context.get('currency_rate', 3100.0))
        symbol = context.get('currency_symbol', 'TSh')
        converted = amount * rate
        # Show decimals unless they're zero (e.g. JPY)
        if converted == int(converted) and rate > 50:
            return mark_safe(f'<span class="price-symbol">{symbol}</span>{int(converted):,}')
        return mark_safe(f'<span class="price-symbol">{symbol}</span>{converted:,.2f}')
    except (TypeError, ValueError):
        return value


@register.filter
def currency(value):
    """Legacy filter — plain GBP. Use {% price %} tag in new templates."""
    try:
        return f'£{float(value):.2f}'
    except (TypeError, ValueError):
        return value


@register.simple_tag
def status_badge(status):
    classes = {
        'pending': 'amz-status-pending',
        'confirmed': 'amz-status-confirmed',
        'shipped': 'amz-status-shipped',
        'delivered': 'amz-status-delivered',
        'cancelled': 'amz-status-cancelled',
        'refunded': 'amz-status-cancelled',
    }
    css = classes.get(status, 'amz-status-pending')
    label = status.capitalize()
    return mark_safe(f'<span class="amz-status-badge {css}">{label}</span>')
