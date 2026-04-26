''' 
A context processor has a very simple interface: It’s a Python function that takes one argument, an HttpRequest object, and returns a dictionary that gets added to the template context. Each context processor must return a dictionary.

Custom context processors can live anywhere in your code base. All Django cares about is that your custom context processors are pointed to by the 'context_processors' option in your TEMPLATES setting — or the context_processors argument of Engine if you’re using it directly.
'''

#using in order to make category links available accross the website

from .models import Category
from .middleware import CURRENCIES


def menu_links(request):
    from wishlist.models import WishlistItem
    links = Category.objects.all()
    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    ctx = dict(links=links, wishlist_count=wishlist_count)

    # Currency info (set by CurrencyMiddleware; fall back gracefully)
    ctx['currency_code']   = getattr(request, 'currency_code',   'TZS')
    ctx['currency_symbol'] = getattr(request, 'currency_symbol', 'TSh')
    ctx['currency_rate']   = getattr(request, 'currency_rate',   3100.0)
    ctx['currency_flag']   = getattr(request, 'currency_flag',   '🇹🇿')
    ctx['currency_label']  = getattr(request, 'currency_label',  'Tanzanian Shilling')
    ctx['all_currencies']  = [
        (code, sym, flag, label)
        for code, (sym, rate, flag, label) in CURRENCIES.items()
    ]

    # Language
    ctx['active_language'] = getattr(request, 'LANGUAGE_CODE', 'en')

    return ctx