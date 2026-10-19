from django.urls import path

from . import views

urlpatterns = [
    path("cities/", views.city_list, name="city_list"),
    path("cities/new/", views.city_create, name="city_create"),
    path("cities/<int:pk>/", views.city_detail, name="city_detail"),
    path("cities/<int:pk>/edit/", views.city_update, name="city_update"),
    path("cities/<int:pk>/delete/", views.city_delete, name="city_delete"),
    path("cities/<int:city_id>/readings/new/", views.reading_create, name="reading_create"),
    path("readings/<int:pk>/edit/", views.reading_update, name="reading_update"),
    path("readings/<int:pk>/delete/", views.reading_delete, name="reading_delete"),
]