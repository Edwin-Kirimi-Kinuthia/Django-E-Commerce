from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from api.views.products import (
    CategoryListView,
    CategoryProductListView,
    ProductListView,
    ProductDetailView,
    ReviewListCreateView,
)
from api.views.cart import (
    CartView,
    CartAddView,
    CartUpdateView,
    CartRemoveView,
    CartClearView,
)
from api.views.orders import (
    OrderListView,
    OrderDetailView,
    OrderCancelView,
    CheckoutView,
)
from api.views.wishlist import WishlistView
from api.views.coupons import CouponValidateView
from api.views.search import SearchView
from api.views.auth import ProfileView, ProfileUpdateView, AddressListCreateView, AddressDetailView

urlpatterns = [

    # --- Auth ---
    path('auth/', include('dj_rest_auth.urls')),                   # login, logout, password
    path('auth/register/', include('dj_rest_auth.registration.urls')),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/profile/details/', ProfileUpdateView.as_view(), name='profile_details'),
    path('auth/addresses/', AddressListCreateView.as_view(), name='address_list'),
    path('auth/addresses/<int:pk>/', AddressDetailView.as_view(), name='address_detail'),

    # --- Categories ---
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/products/', CategoryProductListView.as_view(), name='category_products'),

    # --- Products ---
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<slug:slug>/reviews/', ReviewListCreateView.as_view(), name='product_reviews'),

    # --- Search ---
    path('search/', SearchView.as_view(), name='search'),

    # --- Cart ---
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', CartAddView.as_view(), name='cart_add'),
    path('cart/clear/', CartClearView.as_view(), name='cart_clear'),
    path('cart/<int:item_id>/', CartUpdateView.as_view(), name='cart_update'),
    path('cart/<int:item_id>/remove/', CartRemoveView.as_view(), name='cart_remove'),

    # --- Orders ---
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order_cancel'),

    # --- Wishlist ---
    path('wishlist/', WishlistView.as_view(), name='wishlist'),

    # --- Coupons ---
    path('coupons/validate/', CouponValidateView.as_view(), name='coupon_validate'),

    # --- API Docs ---
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger_ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
