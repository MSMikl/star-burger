from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import models
from django.utils import timezone

from fetch_coordinates import fetch_coordinates


class LocationManager(models.Manager):
    def get_or_create_location(self, address):
        try:
            location = self.get(address=address)
        except ObjectDoesNotExist:
            lon, lat = fetch_coordinates(settings.GEOCODER_API_KEY, address)
            location = self.create(
                address=address,
                longitude=lon,
                latitude=lat,
            )
        return location


class Location(models.Model):
    address = models.CharField(
        verbose_name='Адрес',
        max_length=100,
        unique=True
    )
    longitude = models.CharField(
        'Долгота',
        max_length=20,
        null=True,
        blank=True,
    )
    latitude = models.CharField(
        'Широта',
        max_length=20,
        null=True,
        blank=True
    )
    time_refreshed = models.DateTimeField(
        'Время последнего обновления',
        default=timezone.now()
    )

    objects = LocationManager()
    
    class Meta:
        verbose_name = 'Местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self) -> str:
        return self.address
