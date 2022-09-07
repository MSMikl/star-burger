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
from location.models import Location


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


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.exclude(status='Finished').add_full_price().order_by('-id', '-status').with_coordinates()
    menu_items = RestaurantMenuItem.objects.select_related()
    product_availability = defaultdict(set)
    restaurants_coordinates = {}
    for restaurant in Restaurant.objects.with_coordinates():
        restaurants_coordinates[restaurant] = {
            'longitude': restaurant.longitude,
            'latitude': restaurant.latitude
        }
    for item in menu_items:
        if item.product.id not in product_availability[item.restaurant]:
            product_availability[item.restaurant].add(item.product.id)
    order_elements = OrderElement.objects.filter(order__status='Unhandled').select_related()
    order_elements_dict = defaultdict(set)
    for order_element in order_elements:
        order_elements_dict[order_element.order].add(order_element.product.id)

    data_to_render = {'orders': []}

    for order in orders:
        data_to_render['orders'].append(
            {
                'id': order.id,
                'full_price': order.full_price,
                'client': f"{order.firstname} {order.lastname}",
                'phonenumber': order.phonenumber,
                'address': order.address,
                'status': order.get_status_display(),
                'comments': order.comments,
                'payment_method': order.get_payment_method_display(),
                'restaurant': order.assigned_at.name if order.assigned_at else None
            }
        )
        if not order.status == 'Unhandled':
            continue
        available_rests = []
        for (restaurant, menu) in product_availability.items():
            if not order_elements_dict[order].issubset(menu):
                continue
            if not restaurants_coordinates[restaurant]['longitude'] or not order.longitude:
                distance_text = 'Ошибка определения координат'
            else:
                distance_text = f"""{round(distance.distance(
                    tuple(restaurants_coordinates[restaurant].values()),
                    (order.longitude, order.latitude)
                ).km, 2)} км"""
            available_rests.append((restaurant.name, distance_text))
        data_to_render['orders'][-1]['available_rests'] = available_rests

    return render(request, template_name='order_items.html', context=data_to_render)
