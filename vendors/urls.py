from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Public
    path('', views.vendor_list, name='list'),
    path('apply/', views.apply, name='apply'),
    path('apply/pending/', views.pending, name='pending'),
    path('<slug:slug>/', views.storefront, name='storefront'),

    # Vendor dashboard (approved vendors only)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/profile/', views.profile_edit, name='profile_edit'),
    path('dashboard/products/', views.product_list, name='product_list'),
    path('dashboard/products/add/', views.product_add, name='product_add'),
    path('dashboard/products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('dashboard/products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('dashboard/orders/', views.orders, name='orders'),
    path('dashboard/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('dashboard/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('dashboard/orders/<int:order_id>/ship/', views.ship_order, name='ship_order'),
]
