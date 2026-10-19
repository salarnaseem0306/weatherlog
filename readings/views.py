from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CityForm
from .models import City

from .forms import CityForm, ReadingForm
from .models import City, Reading


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


def reading_create(request, city_id):
    city = get_object_or_404(City, pk=city_id)
    if request.method == "POST":
        form = ReadingForm(request.POST, city=city)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.city = city
            reading.save()
            messages.success(request, "Reading saved")

            return redirect("city_detail", pk=city.pk)

                        

        
    else:
        form = ReadingForm(city=city)
    return render(
        request,
        "readings/reading_form.html",
        {"form": form, "city": city, "title": f"Add reading for {city.name}"},
    )


def reading_update(request, pk):
    reading = get_object_or_404(Reading.objects.select_related("city"), pk=pk)
    city = reading.city
    if request.method == "POST":
        form = ReadingForm(request.POST, instance=reading, city=city)
        if form.is_valid():
            form.save()
            messages.success(request, "Reading saved")
            return redirect("city_detail", pk=city.pk)
    else:
        form = ReadingForm(instance=reading, city=city)
    return render(
        request,
        "readings/reading_form.html",
        {"form": form, "city": city, "title": f"Edit reading for {city.name}"},
    )


def reading_delete(request, pk):
    reading = get_object_or_404(Reading.objects.select_related("city"), pk=pk)
    city = reading.city
    if request.method == "POST":
        reading.delete()
        messages.success(request, "Reading deleted")
        return redirect("city_detail", pk=city.pk)
    return render(
        request,
        "readings/reading_confirm_delete.html",
        {"reading": reading, "city": city},
    )

