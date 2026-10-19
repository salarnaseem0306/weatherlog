from django.contrib import admin

from .models import City, Reading


class ReadingInline(admin.TabularInline):
    model = Reading
    extra = 1


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "latitude", "longitude")
    search_fields = ("name", "country")
    inlines = [ReadingInline]


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("city", "date", "max_temp", "min_temp", "humidity", "source")
    list_filter = ("city", "source")
    search_fields = ("city__name",)
    date_hierarchy = "date"