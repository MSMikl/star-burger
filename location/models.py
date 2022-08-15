from urllib.error import HTTPError
import requests

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import models
from django.utils import timezone


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
    except HTTPError:
        return None, None
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None, None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


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
            location.save()
        return {'longitude': location.longitude,
                'latitude': location.latitude
        }


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

    def __str__(self) -> str:
        return f'{self.address}'

    def save(self, *args, **kwargs):
        self.longitude, self.latitude = fetch_coordinates(settings.GEOCODER_API_KEY, self.address)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Местоположение'
        verbose_name_plural = 'Местоположения'