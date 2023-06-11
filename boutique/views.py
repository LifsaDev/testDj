from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from social_django.models import UserSocialAuth
from django.http import JsonResponse
import json
import requests
import paypalrestsdk
from django.conf import settings
from django.views.generic import ListView
from django.db.models import Q
import base64
from django.views.generic import DetailView
import stripe
import datetime
from django.db.models import Prefetch,Count
from .models import * 
from .utils import cookieCart, cartData, guestOrder

def home(request):
    query = request.GET.get('q')
    if query:
        items = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query)).distinct()
    else:
        items = Product.objects.all()

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']

    categories = Category.objects.annotate(num_products=Count('category_products')).exclude(
        num_products=0).prefetch_related(Prefetch('category_products', queryset=items.order_by('name')))
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'categories': categories, 'query': query}
    return render(request, 'boutique/home.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    products_in_same_category = Product.objects.filter(categorie=product.categorie).exclude(id=pk)

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'product': product, 'products_in_same_category': products_in_same_category,'items':items, 'order':order, 'cartItems':cartItems}

    return render(request, 'boutique/product_detail.html', context)

def search_products(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    query = request.GET.get('q')
    products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    context = {'products': products, 'query': query,'items':items,'cartItems':cartItems}
    return render(request, 'boutique/search_products.html', context)



def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'boutique/cart.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	 
	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

class SettingsView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            facebook_login = user.social_auth.get(provider='facebook')
        except UserSocialAuth.DoesNotExist:
            facebook_login = None

        can_disconnect = (user.social_auth.count() > 1 or user.has_usable_password())

        return render(request, 'boutique/settings.html', {
            'facebook_login': facebook_login,
            'can_disconnect': can_disconnect
        })


def shipping_address(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zipcode = request.POST.get('zipcode')

        # Enregistrer les données dans la base de données
        shipping_address = ShippingAddress(
            customer=request.user.customer,
            address=address,
            city=city,
            state=state,
            zipcode=zipcode
        )
        shipping_address.save()
        data = cartData(request)

        cartItems = data['cartItems']
        order = data['order']
        items = data['items']

        context = {'items': items, 'order': order, 'cartItems': cartItems}

        return render(request, 'boutique/paymentmode.html', context)
    else:
        return render(request, 'boutique/checkout.html')

def initiate_payment_credit(request):
    # Récupérer les informations de paiement depuis le formulaire
    amount = request.POST.get('amount')
    description = request.POST.get('description')
    card_number = request.POST.get('card_number')
    exp_month = request.POST.get('exp_month')
    exp_year = request.POST.get('exp_year')
    cvc = request.POST.get('cvc')

    # Configurer l'API Stripe avec les informations d'API
    stripe.api_key = '<api_key>'

    # Créer un objet Charge pour initier la transaction de paiement
    charge = stripe.Charge.create(
        amount=amount,
        currency='usd',
        description=description,
        source={
            'object': 'card',
            'number': card_number,
            'exp_month': exp_month,
            'exp_year': exp_year,
            'cvc': cvc,
        },
    )

    # Traiter la réponse de l'API Stripe
    if charge['status'] == 'succeeded':
        # La transaction de paiement a été approuvée
        return redirect('<return_url>')
    else:
        # La transaction de paiement a échoué
        error_message = charge['failure_message']
        return render(request, 'boutique/payment_error.html', {'error_message': error_message})



def initiate_payment_paypal(request):
    # Récupérer les informations de paiement depuis le formulaire
    amount = request.POST.get('amount')
    description = request.POST.get('description')

    # Configurer l'API PayPal avec les informations d'API
    paypalrestsdk.configure({
        'mode': 'sandbox', # Utiliser le mode sandbox pour les tests
        'client_id': '<client_id>',
        'client_secret': '<client_secret>',
    })

    # Créer un objet Payment pour initier la transaction de paiement
    payment = paypalrestsdk.Payment({
        'intent': 'sale',
        'payer': {
            'payment_method': 'paypal',
        },
        'transactions': [{
            'amount': {
                'total': amount,
                'currency': 'USD',
            },
            'description': description,
        }],
        'redirect_urls': {
            'return_url': '<return_url>',
            'cancel_url': '<cancel_url>',
        },
    })

    # Envoyer la requête de paiement à l'API PayPal
    if payment.create():
        # La transaction de paiement a été initiée avec succès
        for link in payment.links:
            if link.method == 'REDIRECT':
                redirect_url = str(link.href)
                return redirect(redirect_url)
    else:
        # La transaction de paiement a échoué
        error_message = payment.error['message']
        return render(request, 'boutique/payment_error.html', {'error_message': error_message})


def initiate_payment_orange(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # Récupérer les informations de paiement depuis le formulaire
    amount = request.POST.get('amount')
    phone_number = request.POST.get('phone_number')

    # Construire la requête HTTP pour initier la transaction de paiement
    url = 'https://api.orange.com/orange-money-webpay/dev/v1/webpayment'
    headers = {
        'Authorization': 'Bearer <access_token>',
        'Content-Type': 'application/json',
    }
    data = {
        'merchant_key': '<merchant_key>',
        'currency': 'XOF',
        'order_id': '<order_id>',
        'amount': amount,
        'return_url': '<return_url>',
        'cancel_url': '<cancel_url>',
        'notif_url': '<notif_url>',
        'lang': 'fr',
        'reference': '<reference>',
        'description': '<description>',
        'payer': {
            'phone_number': phone_number,
        },
    }

    # Encoder les clés d'API Client ID et Client Secret en base64
    client_id = 'BeW88FKO2g3e3HPWJ7708IuaO5HzxIss'
    client_secret = 'Xl9qOYbi7QtH2Bsk'
    auth_header = base64.b64encode(f'{client_id}:{client_secret}'.encode('ascii')).decode('ascii')

    # Envoyer la requête HTTP pour obtenir le token d'accès
    auth_url = 'https://api.orange.com/oauth/v2/token'
    auth_headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    auth_data = {
        'grant_type': 'client_credentials',
    }
    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)

    # Traiter la réponse de l'API pour obtenir le token d'accès
    if auth_response.status_code == 200:
        access_token = auth_response.json()['access_token']
        headers['Authorization'] = f'Bearer {access_token}'

        # Envoyer la requête HTTP pour initier la transaction de paiement
        response = requests.post(url, headers=headers, json=data)

        # Traiter la réponse de l'API "Pay with Orange Bill Europe"
        if response.status_code == 201:
            # La transaction de paiement a été initiée avec succès
            payment_url = response.json()['payment_url']
            return redirect(payment_url)
        else:
            # La transaction de paiement a échoué
            error_message = response.json()['error_message']
            context = {'items': items, 'order': order, 'cartItems': cartItems,'error_message': error_message}
            return render(request, 'boutique/payment_error.html',context )
    else:
        # La récupération du token d'accès a échoué
        if 'error_description' in auth_response.json():
            error_message = auth_response.json()['error_description']
        else:
            error_message = 'Une erreur s\'est produite lors de la récupération du token d\'accès.'
            context = {'items': items, 'order': order, 'cartItems': cartItems, 'error_message': error_message}
        return render(request, 'boutique/payment_error.html', context)


def paymentmode(request):
    if request.method == 'POST':
        data = cartData(request)
        order = data["order"]
        payment_method = request.POST.get('payment_method')
        print(payment_method)
        payment = Payment.objects.create(order=order, payment_method=payment_method)
        if payment_method == "orange money":
             return redirect('OrangeMoney')
        elif payment_method == "paypal":
            return  redirect('Paypal')
        elif payment_method == "credit card":
            return  redirect('Creditcard')
        elif payment_method == "cash":
            return  redirect('Cash')
    else:
         return render(request, 'boutique/paymentmode.html')


def OrangeMoney(request):
    data = cartData(request)
    order = data["order"]
    order_items = OrderItem.objects.filter(order=order)
    total = order.get_cart_total

    cartItems = data['cartItems']
    items = data['items']

    # Calcul des frais de livraison en fonction de la catégorie de produit
    shipping_cost = 0
    for order_item in order_items:
        product = order_item.product
        if "Homme" in str(product.categorie) or "Femme" in str(product.categorie):
            shipping_cost += settings.OTHERS_SHIPPING_COST
        else:
            shipping_cost += settings.ELECTRONICS_SHIPPING_COST

    # Ajout des frais de livraison au total
    total += float(shipping_cost)

    context = {
        'order': order,
        'order_items': order_items,
        'total': total,
        'items': items,
        'cartItems': cartItems,
        'shipping_cost': float(shipping_cost),
    }
    return render(request,'boutique/OrangeMoney.html',context)
def Paypal(request):
    data = cartData(request)
    order = data["order"]
    order_items = OrderItem.objects.filter(order=order)
    total = order.get_cart_total

    cartItems = data['cartItems']
    items = data['items']

    # Calcul des frais de livraison en fonction de la catégorie de produit
    shipping_cost = 0
    for order_item in order_items:
        product = order_item.product
        if "Homme" in str(product.categorie) or "Femme" in str(product.categorie):
            shipping_cost += settings.OTHERS_SHIPPING_COST
        else:
            shipping_cost += settings.ELECTRONICS_SHIPPING_COST

    # Ajout des frais de livraison au total
    total += float(shipping_cost)

    context = {
        'order': order,
        'order_items': order_items,
        'total': total,
        'items': items,
        'cartItems': cartItems,
        'shipping_cost': float(shipping_cost),
    }
    return render(request,'boutique/Paypal.html',context)

def Cash(request):
    data = cartData(request)
    order = data["order"]
    order_items = OrderItem.objects.filter(order=order)
    total = order.get_cart_total

    cartItems = data['cartItems']
    items = data['items']

    # Calcul des frais de livraison en fonction de la catégorie de produit
    shipping_cost = 0
    for order_item in order_items:
        product = order_item.product
        if "Homme" in str(product.categorie) or "Femme" in str(product.categorie):
            shipping_cost += settings.OTHERS_SHIPPING_COST
        else:
            shipping_cost += settings.ELECTRONICS_SHIPPING_COST

    # Ajout des frais de livraison au total
    total += float(shipping_cost)

    context = {
        'order': order,
        'order_items': order_items,
        'total': total,
        'items': items,
        'cartItems': cartItems,
        'shipping_cost': float(shipping_cost),
    }
    return render(request,'boutique/Cash.html',context)
def Creditcard(request):
    data = cartData(request)
    order = data["order"]
    order_items = OrderItem.objects.filter(order=order)
    total = order.get_cart_total

    cartItems = data['cartItems']
    items = data['items']

    # Calcul des frais de livraison en fonction de la catégorie de produit
    shipping_cost = 0
    for order_item in order_items:
        product = order_item.product
        if "Homme" in str(product.categorie) or "Femme" in str(product.categorie):
            shipping_cost += settings.OTHERS_SHIPPING_COST
        else:
            shipping_cost += settings.ELECTRONICS_SHIPPING_COST

    # Ajout des frais de livraison au total
    total += float(shipping_cost)

    context = {
        'order': order,
        'order_items': order_items,
        'total': total,
        'items': items,
        'cartItems': cartItems,
        'shipping_cost': float(shipping_cost),
    }
    return render(request,'boutique/Creditcard.html',context)
def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)

def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'boutique/checkout.html', context)


@login_required
def password(request):
    if request.user.has_usable_password():
        PasswordForm = PasswordChangeForm
    else:
        PasswordForm = AdminPasswordChangeForm

    if request.method == 'POST':
        form = PasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordForm(request.user)
    return render(request, 'boutique/password.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.customer.email = form.cleaned_data.get('email')
            user.customer.phone_number = form.cleaned_data.get('phone_number')
            user.customer.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    return render(request, 'registration/signup.html', {'form': form,'cartItems':cartItems})
