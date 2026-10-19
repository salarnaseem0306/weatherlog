from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import City


def city_list(request):
    cities = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    return render(request, "readings/city_list.html", {"cities": cities})


def city_detail(request, pk):
    city = get_object_or_404(City, pk=pk)
    readings = city.readings.order_by("-date")[:30]
    return render(
        request,
        "readings/city_detail.html",
        {"city": city, "readings": readings},
    )