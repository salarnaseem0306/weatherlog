from django.urls import path

from . import views

urlpatterns = [
    path("cities/", views.city_list, name="city_list"),
]

urlpatterns = [
    path("cities/", views.city_list, name="city_list"),
    path("cities/<int:pk>/", views.city_detail, name="city_detail"),
]