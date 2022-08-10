from django.db import models
from django.db.models import F, Sum
from django.core.validators import MinValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def full_price(self):
        return (
            self
            .select_related()
            .annotate(full_price=Sum(F('elements__price') * F('elements__quantity')))
            .order_by('-id')
        )


class Order(models.Model):
    firstname = models.CharField(
        'Имя клиента',
        max_length=50,
        db_index=True,
    )
    lastname = models.CharField(
        'Фамилия клиента',
        max_length=50,
        db_index=True,
    )
    phonenumber = PhoneNumberField(
        db_index=True
    )
    address = models.CharField(
        'Адрес доставки',
        max_length=100,
        db_index=True,
    )
    status_choices = [
        ('Unhandled', 'Необработанный'),
        ('Preparing', 'Готовится'),
        ('Delivering', 'Доставляется'),
        ('Finished', 'Завершенный'),
    ]
    status = models.CharField(
        'Статус заказа',
        max_length=20,
        choices=status_choices,
        default='Unhandled',
        db_index=True,
    )
    comments = models.TextField(
        'Комментарии',
        blank=True,
        db_index=True
    )
    created_at = models.DateTimeField(
        'Время создания заказа',
        default=timezone.now()
    )
    called_at = models.DateTimeField(
        'Время звонка клиенту',
        blank=True,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'Время доставки клиенту',
        blank=True,
        null=True,
        db_index=True
    )
    payment_method_choices = [
        ('online', 'Онлайн'),
        ('cash', 'Наличными'),
    ]
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=payment_method_choices,
        default='cash',
        db_index=True
    )
    produced_at = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Приготовить в ресторане',
        null=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ {self.id}"


def default_price(product: Product):
    return product.price


class OrderElement(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='продукт',
    )
    quantity = models.IntegerField(
        'Количество',
        default=0,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='elements',
        verbose_name='заказ',
    )
    price = models.DecimalField(
        'стоимость продукта',
        decimal_places=2,
        max_digits=8,
        default=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Пункт заказа'
        verbose_name_plural = 'Пункты заказа'
        unique_together = [
            ['order', 'product']
        ]

    def __str__(self):
        return f"{self.product.name} - {self.quantity} шт."
