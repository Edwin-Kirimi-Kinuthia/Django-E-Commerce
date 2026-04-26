from django.urls import path
from . import views

app_name='shop'

urlpatterns = [
    path('', views.allProdCat, name='allProdCat'),
    path('review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('set-currency/', views.set_currency, name='set_currency'),
    path('set-language/', views.set_language_view, name='set_language'),
    path('<slug:c_slug>/', views.allProdCat, name='products_by_category'),
    path('<slug:c_slug>/<slug:product_slug>/', views.ProdCatDetail, name='ProdCatDetail'),
]
