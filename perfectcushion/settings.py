"""
Django settings for perfectcushion project.
"""

from pathlib import Path
from decouple import config, Csv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Installed Apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Jazzmin must come before django.contrib.admin
    'jazzmin',

    # Project apps
    'shop.apps.ShopConfig',
    'search_app.apps.SearchAppConfig',
    'cart.apps.CartConfig',
    'order.apps.OrderConfig',
    'accounts.apps.AccountsConfig',
    'coupons.apps.CouponsConfig',
    'wishlist.apps.WishlistConfig',
    'vendors.apps.VendorsConfig',
    'api.apps.ApiConfig',

    # REST framework
    'rest_framework',
    'django_filters',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',

    # Auth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Forms
    'crispy_forms',
    'crispy_bootstrap4',

    # Stripe
    'stripe',

    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

SITE_ID = 1


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',          # must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',      # i18n locale from session/header
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'shop.middleware.CurrencyMiddleware',
    'shop.middleware.LanguageMiddleware',
]

ROOT_URLCONF = 'perfectcushion.urls'


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'shop' / 'templates',
            BASE_DIR / 'search_app' / 'templates',
            BASE_DIR / 'cart' / 'templates',
            BASE_DIR / 'order' / 'templates',
            BASE_DIR / 'accounts' / 'templates',
            BASE_DIR / 'wishlist' / 'templates',
            BASE_DIR / 'vendors' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.menu_links',
                'cart.context_processors.counter',
            ],
        },
    },
]

WSGI_APPLICATION = 'perfectcushion.wsgi.application'


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
_db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')
_db_name   = config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3'))

if _db_engine == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': _db_engine,
            'NAME': BASE_DIR / _db_name if not _db_name.startswith('/') and ':' not in _db_name else _db_name,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': _db_engine,
            'NAME': _db_name,
            'USER': config('DB_USER', default=''),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }


# ---------------------------------------------------------------------------
# Password Validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'

LANGUAGES = [
    ('en',    'English'),
    ('fr',    'Français'),
    ('de',    'Deutsch'),
    ('es',    'Español'),
    ('it',    'Italiano'),
    ('pt',    'Português'),
    ('pt-br', 'Português (Brasil)'),
    ('hi',    'हिन्दी'),
    ('ja',    '日本語'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static & Media Files
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'static' / 'media'


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # keeps admin/browser working
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}


# ---------------------------------------------------------------------------
# JWT Settings
# ---------------------------------------------------------------------------
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# ---------------------------------------------------------------------------
# CORS (for mobile / frontend clients)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True


# ---------------------------------------------------------------------------
# dj-rest-auth / allauth
# ---------------------------------------------------------------------------
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_HTTPONLY': False,  # send refresh token in response body (mobile-friendly)
}

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'


# ---------------------------------------------------------------------------
# API Docs (drf-spectacular)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'Perfect Cushion API',
    'DESCRIPTION': 'E-commerce REST API for Perfect Cushion store',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# ---------------------------------------------------------------------------
# Crispy Forms
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_TEMPLATE_PACK = 'bootstrap4'


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')


# ---------------------------------------------------------------------------
# Email (Mailgun SMTP)
# ---------------------------------------------------------------------------
EMAIL_HOST = config('EMAIL_HOST', default='smtp.mailgun.org')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')


# ---------------------------------------------------------------------------
# Jazzmin Admin UI
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    # Title & branding
    'site_title': 'ShopMart Admin',
    'site_header': 'ShopMart',
    'site_brand': 'ShopMart',
    'welcome_sign': 'Welcome to ShopMart Admin',
    'copyright': 'ShopMart Ltd',

    # Icons (Font Awesome 5 free)
    'site_icon': None,
    'site_logo': None,

    # Top navigation links
    'topmenu_links': [
        {'name': 'Storefront', 'url': '/', 'new_window': True, 'icon': 'fas fa-store'},
        {'name': 'Seller Applications', 'model': 'vendors.vendor', 'icon': 'fas fa-user-tie'},
    ],

    # User menu
    'usermenu_links': [
        {'name': 'Storefront', 'url': '/', 'new_window': True, 'icon': 'fas fa-store'},
    ],

    # Sidebar
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],

    # Model icons
    'icons': {
        'auth':                     'fas fa-users-cog',
        'auth.user':                'fas fa-user',
        'auth.group':               'fas fa-users',
        'shop.category':            'fas fa-th-large',
        'shop.product':             'fas fa-box',
        'shop.review':              'fas fa-star',
        'order.order':              'fas fa-shopping-bag',
        'order.orderitem':          'fas fa-list',
        'cart.cart':                'fas fa-shopping-cart',
        'cart.cartitem':            'fas fa-cart-plus',
        'vendors.vendor':           'fas fa-store',
        'vendors.vendorreview':     'fas fa-store-alt',
        'coupons.coupon':           'fas fa-tag',
        'accounts.userprofile':     'fas fa-id-card',
        'accounts.address':         'fas fa-map-marker-alt',
        'wishlist.wishlistitem':    'fas fa-heart',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',

    # UI tweaks
    'related_modal_active': True,
    'custom_css': None,
    'custom_js': None,
    'use_google_fonts_cdn': False,
    'show_ui_builder': False,

    # Order of apps in sidebar
    'order_with_respect_to': [
        'order',
        'vendors',
        'shop',
        'cart',
        'coupons',
        'accounts',
        'wishlist',
        'auth',
    ],

    # Changeform format
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'auth.user': 'collapsible',
        'auth.group': 'vertical_tabs',
    },
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-indigo',
    'accent': 'accent-indigo',
    'navbar': 'navbar-dark',
    'no_navbar_border': True,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-indigo',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'dark_mode_theme': None,
    'button_classes': {
        'primary':   'btn-primary',
        'secondary': 'btn-secondary',
        'info':      'btn-info',
        'warning':   'btn-warning',
        'danger':    'btn-danger',
        'success':   'btn-success',
    },
}
