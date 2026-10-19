from django.urls import path

from . import views

urlpatterns = [
    path("cities/", views.city_list, name="city_list"),
    path("cities/new/", views.city_create, name="city_create"),
    path("cities/<int:pk>/", views.city_detail, name="city_detail"),
    path("cities/<int:pk>/edit/", views.city_update, name="city_update"),
    path("cities/<int:pk>/delete/", views.city_delete, name="city_delete"),
]