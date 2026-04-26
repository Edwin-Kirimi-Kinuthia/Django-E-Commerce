"""
Currency and language middleware for ShopMart.

Currency is auto-detected from the visitor's IP via ip-api.com (free, no key
needed) and cached in the session.  Users can override it manually via the
?set_currency= param or the currency picker in the header.

Language is resolved the same way: IP → country → preferred locale, stored in
session, and activated with Django's translation machinery each request.
"""

import json
import urllib.request

from django.utils import translation


# ---------------------------------------------------------------------------
# Currency catalogue
# code, symbol, rate-from-GBP, flag emoji, display label
# ---------------------------------------------------------------------------
CURRENCIES = {
    'TZS': ('TSh', 3100.0,  '🇹🇿', 'Tanzanian Shilling'),
    'GBP': ('£',   1.00,    '🇬🇧', 'British Pound'),
    'USD': ('$',   1.27,    '🇺🇸', 'US Dollar'),
    'EUR': ('€',   1.17,    '🇪🇺', 'Euro'),
    'NGN': ('₦',   2050.0,  '🇳🇬', 'Nigerian Naira'),
    'GHS': ('GH₵', 17.5,   '🇬🇭', 'Ghanaian Cedi'),
    'KES': ('KSh', 165.0,   '🇰🇪', 'Kenyan Shilling'),
    'UGX': ('USh', 4680.0,  '🇺🇬', 'Ugandan Shilling'),
    'ZAR': ('R',   23.5,    '🇿🇦', 'South African Rand'),
    'INR': ('₹',   106.0,   '🇮🇳', 'Indian Rupee'),
    'AUD': ('A$',  1.95,    '🇦🇺', 'Australian Dollar'),
    'CAD': ('CA$', 1.73,    '🇨🇦', 'Canadian Dollar'),
    'AED': ('AED', 4.67,    '🇦🇪', 'UAE Dirham'),
    'SAR': ('SAR', 4.77,    '🇸🇦', 'Saudi Riyal'),
    'PKR': ('₨',   353.0,   '🇵🇰', 'Pakistani Rupee'),
    'BRL': ('R$',  6.30,    '🇧🇷', 'Brazilian Real'),
    'JPY': ('¥',   191.0,   '🇯🇵', 'Japanese Yen'),
}

# country code → preferred currency code
COUNTRY_CURRENCY = {
    'TZ': 'TZS', 'KE': 'KES', 'UG': 'UGX',
    'GB': 'GBP', 'US': 'USD', 'CA': 'CAD', 'AU': 'AUD',
    'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR',
    'NL': 'EUR', 'BE': 'EUR', 'AT': 'EUR', 'PT': 'EUR',
    'IE': 'EUR', 'GR': 'EUR', 'FI': 'EUR',
    'NG': 'NGN', 'GH': 'GHS',
    'ZA': 'ZAR', 'IN': 'INR', 'PK': 'PKR',
    'AE': 'AED', 'SA': 'SAR', 'JP': 'JPY', 'BR': 'BRL',
}

# country code → Django locale code
COUNTRY_LANGUAGE = {
    'GB': 'en', 'US': 'en', 'CA': 'en', 'AU': 'en', 'IE': 'en',
    'FR': 'fr', 'DE': 'de', 'ES': 'es', 'IT': 'it',
    'PT': 'pt', 'BR': 'pt-br',
    'JP': 'ja', 'IN': 'hi', 'NG': 'en', 'GH': 'en',
}


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _lookup_country(ip: str) -> str:
    """Return ISO-3166-1 alpha-2 country code for the given IP."""
    if ip in ('127.0.0.1', '::1', 'localhost', ''):
        return 'TZ'
    try:
        url = f'http://ip-api.com/json/{ip}?fields=countryCode'
        req = urllib.request.Request(url, headers={'User-Agent': 'ShopMart/1.0'})
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.loads(r.read()).get('countryCode', 'TZ')
    except Exception:
        return 'TZ'


class CurrencyMiddleware:
    """
    Attach currency info to every request:
        request.currency_code   e.g. 'USD'
        request.currency_symbol e.g. '$'
        request.currency_rate   e.g. 1.27  (multiply GBP price by this)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Manual override via query param
        qs_currency = request.GET.get('set_currency', '').upper()
        if qs_currency and qs_currency in CURRENCIES:
            request.session['currency'] = qs_currency

        code = request.session.get('currency')

        if not code:
            # Auto-detect once per session
            country = request.session.get('detected_country')
            if not country:
                country = _lookup_country(_client_ip(request))
                request.session['detected_country'] = country
            code = COUNTRY_CURRENCY.get(country, 'TZS')
            request.session['currency'] = code

        symbol, rate, flag, label = CURRENCIES.get(code, CURRENCIES['TZS'])
        request.currency_code   = code
        request.currency_symbol = symbol
        request.currency_rate   = rate
        request.currency_flag   = flag
        request.currency_label  = label

        return self.get_response(request)


class LanguageMiddleware:
    """
    Activate Django's translation for the detected/chosen locale each request.
    Users can override via ?set_language= or the language picker.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        qs_lang = request.GET.get('set_language', '')
        if qs_lang:
            request.session['django_language'] = qs_lang

        lang = request.session.get('django_language')
        if not lang:
            country = request.session.get('detected_country', 'GB')
            lang = COUNTRY_LANGUAGE.get(country, 'en')
            request.session['django_language'] = lang

        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        response = self.get_response(request)
        return response
