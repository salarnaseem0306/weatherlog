from django.db.models import Count
from django.shortcuts import render

from .models import City


def city_list(request):
    cities = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    return render(request, "readings/city_list.html", {"cities": cities})