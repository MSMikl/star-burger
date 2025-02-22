# Generated by Django 3.2 on 2022-08-11 17:06

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Широта'),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Долгота'),
        ),
        migrations.AlterField(
            model_name='location',
            name='time_refreshed',
            field=models.DateTimeField(default=datetime.datetime(2022, 8, 11, 17, 6, 51, 762880, tzinfo=utc), verbose_name='Время последнего обновления'),
        ),
    ]
