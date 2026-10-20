from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from django.core.paginator import Paginator

from .forms import CityForm, ReadingForm
from .models import City, Reading


class ReadingOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        reading = self.get_object()
        user = self.request.user
        return user.is_staff or reading.created_by_id == user.id


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
    paginate_by = 31

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        readings = (
            self.object.readings
            .select_related("created_by")
            .order_by("-date")
        )

        year = self.request.GET.get("year", "")
        month = self.request.GET.get("month", "")
        if year.isdigit():
            readings = readings.filter(date__year=int(year))
        if month.isdigit() and 1 <= int(month) <= 12:
            readings = readings.filter(date__month=int(month))

        paginator = Paginator(readings, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        params = self.request.GET.copy()
        params.pop("page", None)

        context["readings"] = page_obj
        context["page_obj"] = page_obj
        context["year"] = year
        context["month"] = month
        context["querystring"] = params.urlencode()
        return context


class CityCreateView(LoginRequiredMixin, CreateView):
    model = City
    form_class = CityForm
    template_name = "readings/city_form.html"
    extra_context = {"title": "Add city"}

    def form_valid(self, form):
        messages.success(self.request, "City saved")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("city_detail", kwargs={"pk": self.object.pk})


class CityUpdateView(LoginRequiredMixin, UpdateView):
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


class CityDeleteView(LoginRequiredMixin, DeleteView):
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


@login_required
def reading_create(request, city_id):
    city = get_object_or_404(City, pk=city_id)

    if request.method == "POST":
        form = ReadingForm(request.POST, city=city)

        if form.is_valid():
            reading = form.save(commit=False)
            reading.city = city
            reading.created_by = request.user
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


class ReadingUpdateView(ReadingOwnerMixin, UpdateView):
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


class ReadingDeleteView(ReadingOwnerMixin, DeleteView):
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