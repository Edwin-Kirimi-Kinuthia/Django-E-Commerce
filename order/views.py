from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Order, OrderItem

# Status progression for the tracking timeline
_STATUS_STEPS = [
    (Order.PENDING,   'Order Placed',  'fas fa-shopping-cart'),
    (Order.CONFIRMED, 'Confirmed',     'fas fa-check-circle'),
    (Order.SHIPPED,   'Shipped',       'fas fa-shipping-fast'),
    (Order.DELIVERED, 'Delivered',     'fas fa-box-open'),
]

_STATUS_ORDER = [s[0] for s in _STATUS_STEPS]


def _timeline_steps(current_status):
    """Return list of dicts for the tracking timeline."""
    if current_status in (Order.CANCELLED, Order.REFUNDED):
        # Show all steps as inactive + a final cancelled/refunded step
        steps = [
            {'label': s[1], 'icon': s[2], 'state': 'inactive'}
            for s in _STATUS_STEPS
        ]
        icon = 'fas fa-ban' if current_status == Order.CANCELLED else 'fas fa-undo'
        label = 'Cancelled' if current_status == Order.CANCELLED else 'Refunded'
        steps.append({'label': label, 'icon': icon, 'state': 'active'})
        return steps

    current_idx = _STATUS_ORDER.index(current_status) if current_status in _STATUS_ORDER else 0
    steps = []
    for i, (status, label, icon) in enumerate(_STATUS_STEPS):
        if i < current_idx:
            state = 'done'
        elif i == current_idx:
            state = 'active'
        else:
            state = 'inactive'
        steps.append({'label': label, 'icon': icon, 'state': state})
    return steps


def thanks(request, order_id):
    customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thanks.html', {'customer_order': customer_order})


@login_required
def orderHistory(request):
    order_details = Order.objects.filter(
        emailAddress=request.user.email
    ).order_by('-created')
    return render(request, 'order/orders_list.html', {'order_details': order_details})


@login_required
def viewOrder(request, order_id):
    order = get_object_or_404(Order, id=order_id, emailAddress=request.user.email)
    order_items = OrderItem.objects.filter(order=order)
    timeline = _timeline_steps(order.status)
    return render(request, 'order/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'timeline': timeline,
    })
