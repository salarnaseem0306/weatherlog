
from django.urls import path

from . import views

urlpatterns = [
    path("cities/", views.CityListView.as_view(), name="city_list"),
    path("cities/new/", views.CityCreateView.as_view(), name="city_create"),
    path("cities/<int:pk>/", views.CityDetailView.as_view(), name="city_detail"),
    path("cities/<int:pk>/edit/", views.CityUpdateView.as_view(), name="city_update"),
    path("cities/<int:pk>/delete/", views.CityDeleteView.as_view(), name="city_delete"),
    path(
        "cities/<int:city_id>/readings/new/",
        views.reading_create,
        name="reading_create",
    ),
    path(
        "readings/<int:pk>/edit/",
        views.ReadingUpdateView.as_view(),
        name="reading_update",
    ),
    path(
        "readings/<int:pk>/delete/",
        views.ReadingDeleteView.as_view(),
        name="reading_delete",
    ),
]
