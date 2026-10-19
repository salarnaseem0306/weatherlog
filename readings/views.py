from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CityForm
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
def city_create(request):
    if request.method == "POST":
        form = CityForm(request.POST)
        if form.is_valid():
            city = form.save()
            messages.success(request, "City saved")
            return redirect("city_detail", pk=city.pk)
    else:
        form = CityForm()
    return render(request, "readings/city_form.html", {"form": form, "title": "Add city"})


def city_update(request, pk):
    city = get_object_or_404(City, pk=pk)
    if request.method == "POST":
        form = CityForm(request.POST, instance=city)
        if form.is_valid():
            form.save()
            messages.success(request, "City saved")
            return redirect("city_detail", pk=city.pk)
    else:
        form = CityForm(instance=city)
    return render(
        request,
        "readings/city_form.html",
        {"form": form, "title": f"Edit {city.name}"},
    )
def city_delete(request, pk):
    city = get_object_or_404(City, pk=pk)
    if request.method == "POST":
        city.delete()
        messages.success(request, "City deleted")
        return redirect("city_list")
    return render(
        request,
        "readings/city_confirm_delete.html",
        {"city": city, "reading_count": city.readings.count()},
    )