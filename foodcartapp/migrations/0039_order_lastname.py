# Generated by Django 3.2 on 2022-07-22 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_order_orderelement'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='lastname',
            field=models.CharField(default='sfdg', max_length=50, verbose_name='Фамилия клиента'),
            preserve_default=False,
        ),
    ]
