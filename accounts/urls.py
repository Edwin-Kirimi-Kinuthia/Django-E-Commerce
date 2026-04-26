from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('profile/addresses/', views.address_list, name='addresses'),
    path('profile/addresses/add/', views.address_add, name='address_add'),
    path('profile/addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('profile/addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
]
