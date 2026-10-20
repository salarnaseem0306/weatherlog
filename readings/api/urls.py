from django.urls import path

from . import views

urlpatterns = [
    path("cities/", views.city_list, name="api-city-list"),
]