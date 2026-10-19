from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import CityForm, ReadingForm
from .models import City, Reading


class CityListView(ListView):
    model = City
    template_name = "readings/city_list.html"
    context_object_name = "cities"

    def get_queryset(self):
        return City.objects.annotate(
            reading_count=Count("readings")
        ).order_by("name")


class CityDetailView(DetailView):
    model = City
    template_name = "readings/city_detail.html"
    context_object_name = "city"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["readings"] = self.object.readings.order_by("-date")[:30]
        return context


class CityCreateView(CreateView):
    model = City
    form_class = CityForm
    template_name = "readings/city_form.html"
    extra_context = {"title": "Add city"}

    def form_valid(self, form):
        messages.success(self.request, "City saved")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("city_detail", kwargs={"pk": self.object.pk})


class CityUpdateView(UpdateView):
    model = City
    form_class = CityForm
    template_name = "readings/city_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "City saved")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("city_detail", kwargs={"pk": self.object.pk})


class CityDeleteView(DeleteView):
    model = City
    template_name = "readings/city_confirm_delete.html"
    context_object_name = "city"
    success_url = reverse_lazy("city_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reading_count"] = self.object.readings.count()
        return context

    def form_valid(self, form):
        messages.success(self.request, "City deleted")
        return super().form_valid(form)


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


class ReadingUpdateView(UpdateView):
    model = Reading
    form_class = ReadingForm
    template_name = "readings/reading_form.html"

    def get_queryset(self):
        return Reading.objects.select_related("city")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["city"] = self.object.city
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["city"] = self.object.city
        context["title"] = f"Edit reading for {self.object.city.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Reading saved")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "city_detail", kwargs={"pk": self.object.city.pk}
        )


class ReadingDeleteView(DeleteView):
    model = Reading
    template_name = "readings/reading_confirm_delete.html"

    def get_queryset(self):
        return Reading.objects.select_related("city")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["city"] = self.object.city
        return context

    def form_valid(self, form):
        messages.success(self.request, "Reading deleted")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "city_detail", kwargs={"pk": self.object.city.pk}
        )
