# Generated by Django 3.2 on 2022-08-15 06:00

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0048_auto_20220815_0857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2022, 8, 15, 6, 0, 48, 312202, tzinfo=utc), verbose_name='Время создания заказа'),
        ),
        migrations.AlterField(
            model_name='orderelement',
            name='quantity',
            field=models.IntegerField(default=1, verbose_name='Количество'),
        ),
    ]
