from django.urls import path, include
from .views import (
    home, 
    HomeView, 
    ProductDetailView, 
    add_to_cart, 
    remove_from_cart,
    OrderSummaryView,
    remove_single_item_from_cart,
    CheckoutView,
    PaymentView,
    AddCouponView,
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>', ProductDetailView.as_view(), name='product'),
    path('add-coupon/<code>', OrderSummaryView.as_view(), name='add-coupon'),
    path('add_to_cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('remove-single-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove-single-item-from-cart'),


    # path('',home, name='home'),
]
