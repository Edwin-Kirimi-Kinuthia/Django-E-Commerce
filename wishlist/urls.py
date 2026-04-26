from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist, name='wishlist'),
    path('toggle/<int:product_id>/', views.toggle_wishlist, name='toggle'),
    path('remove/<int:product_id>/', views.remove_wishlist, name='remove'),
]
