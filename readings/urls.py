from django.urls import path

from . import views

urlpatterns = [
    path("cities/", views.city_list, name="city_list"),
]