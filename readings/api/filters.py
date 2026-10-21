import django_filters

from readings.models import City, Reading


class ReadingFilter(django_filters.FilterSet):
    city = django_filters.ModelChoiceFilter(queryset=City.objects.all())
    # both ends are inclusive: date_after=2023-03-01 includes 1 March
    date_after = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    source = django_filters.ChoiceFilter(choices=Reading.Source.choices)

    class Meta:
        model = Reading
        fields = ["city", "date_after", "date_before", "source"]