import json

import phonenumbers

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


from .models import Product, Order, OrderElement


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    data = request.data
    print(data.get('products'))
    if (not isinstance(data.get('products'), list)) or (not data.get('products')):
        content = {'products': 'некорректные данные в поле'}
        return Response(content, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    for field in ['firstname', 'lastname', 'address']:
        if (not isinstance(data.get(field), str)) or (not data.get(field)):
            content = {f'{field}': 'некорректные данные в поле'}
            return Response(content, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if not phonenumbers.is_valid_number(phonenumbers.parse(data.get('phonenumber'), 'RU')):
        content = {'phonenumber': 'некорректный номер телефона'}
        return Response(content, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    order = Order.objects.create(
        firstname=data.get('firstname', 'N/A'),
        lastname=data.get('lastname', 'N/A'),
        phonenumber=data.get('phonenumber', 'N/A'),
        address=data.get('address', 'N/A')
    )
    try:
        for product in data.get('products', []):
            OrderElement.objects.create(
                product=Product.objects.get(id=product['product']),
                quantity=product['quantity'],
                order=order,
            )
    except Product.DoesNotExist:
        order.delete()
        content = {'products': 'несуществующий id продукта в заказе'}
        return Response(content, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    print(order)
    return JsonResponse({})
