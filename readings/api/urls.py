from django.urls import path

from . import views

urlpatterns = [
        path("cities/", views.CityList.as_view(), name="api-city-list"),
]