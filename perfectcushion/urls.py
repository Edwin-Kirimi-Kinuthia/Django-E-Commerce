from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # REST API v1
    path('api/v1/', include('api.urls')),

    # Account management
    path('account/', include('accounts.urls')),
    path('account/create/', views.signupView, name='signup'),
    path('account/login/', views.signinView, name='signin'),
    path('account/logout/', views.signoutView, name='signout'),

    # Password reset (Django built-in)
    path('account/password-reset/',
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('account/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('account/password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('account/password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),

    # Vendors
    path('vendors/', include('vendors.urls')),

    # Wishlist
    path('wishlist/', include('wishlist.urls')),

    # Cart & Orders
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),

    # Search
    path('search/', include('search_app.urls')),

    # Shop (keep last — catches slugs)
    path('', include('shop.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
