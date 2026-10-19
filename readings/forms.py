from django import forms

from .models import City, Reading


class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ["name", "country", "latitude", "longitude"]


class ReadingForm(forms.ModelForm):
    class Meta:
        model = Reading
        fields = ["date", "max_temp", "min_temp", "humidity", "notes"]
        widgets = {
            "date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def __init__(self, *args, city=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.city = city

    def clean(self):
        cleaned_data = super().clean()
        max_temp = cleaned_data.get("max_temp")
        min_temp = cleaned_data.get("min_temp")
        if max_temp is not None and min_temp is not None and min_temp > max_temp:
            self.add_error("min_temp", "Minimum temperature cannot be above the maximum.")

        date = cleaned_data.get("date")
        if self.city is not None and date is not None:
            duplicates = Reading.objects.filter(city=self.city, date=date)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error("date", "This city already has a reading for that date.")
        return cleaned_data