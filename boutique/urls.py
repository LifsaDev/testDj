from django.contrib import admin
from django.urls import path, include
from boutique import views  
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
    path('oauth/', include('social_django.urls', namespace='social')), 
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/password/', views.password, name='password'),

    path('update_item/', views.updateItem, name="update_item"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('process_order/', views.processOrder, name="process_order"),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('shipping_address/', views.shipping_address, name="shipping_address"),
    path('paymentmode/', views.paymentmode, name="payment-mode"),
    path('OrangeMoney/', views.OrangeMoney, name="OrangeMoney"),
    path('Paypal/', views.Paypal, name="Paypal"),
    path('Cash/', views.Cash, name="Cash"),
    path('Creditcard/', views.Creditcard, name="Creditcard"),
    path('initiate-payment_orange/', views.initiate_payment_orange, name='initiate_payment_orange'),
    path('initiate-payment_paypal/', views.initiate_payment_paypal, name='initiate_payment_paypal'),
    path('initiate-payment_credit/', views.initiate_payment_credit, name='initiate_payment_credit'),
    path('search_products/', views.search_products, name="search_products"),


]
 

