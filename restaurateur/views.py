from collections import defaultdict

import requests

from django import forms
from django.conf import settings
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from geopy import distance


from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem, OrderElement


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })

def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.exclude(status='Finished').full_price().order_by('-status')
    menu_items = RestaurantMenuItem.objects.select_related().all()
    product_availability = defaultdict(set)
    restaurants_coordinates = {}
    for item in menu_items:
        if item.product.id not in product_availability[item.restaurant]:
            product_availability[item.restaurant].add(item.product.id)
        if not restaurants_coordinates.get(item.restaurant):
            restaurants_coordinates[item.restaurant] = fetch_coordinates(settings.GEOCODER_API_KEY, item.restaurant.address) or 'ERROR'
    
    order_elements = OrderElement.objects.filter(order__status='Unhandled').select_related()
    order_elements_dict = defaultdict(set)
    for order_element in order_elements:
        order_elements_dict[order_element.order].add(order_element.product.id)
    print(order_elements_dict)

    data = {'orders': []}

    for order in orders:
        data['orders'].append(
            {
                'id': order.id,
                'full_price': order.full_price,
                'client': f"{order.firstname} {order.lastname}",
                'phonenumber': order.phonenumber,
                'address': order.address,
                'status': order.get_status_display(),
                'comments': order.comments,
                'payment_method': order.get_payment_method_display(),
                'restaurant': order.produced_at.name if order.produced_at else None
            }
        )
        if not order.status == 'Unhandled':
            continue
        order_coordinates = fetch_coordinates(settings.GEOCODER_API_KEY, order.address) or 'ERROR'
        available_rests = []
        for (restaurant, menu) in product_availability.items():
            if order_elements_dict[order].issubset(menu):
                if restaurants_coordinates[restaurant] == 'ERROR' or order_coordinates == 'ERROR':
                    dist = 'Ошибка определения координат'
                else:
                    dist = round(distance.distance(restaurants_coordinates[restaurant], order_coordinates).km, 2)
                available_rests.append((restaurant.name, dist))
        data['orders'][-1]['available_rests'] = available_rests

    return render(request, template_name='order_items.html', context=data)
