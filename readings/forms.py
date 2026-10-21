from django import forms

from .models import City, Reading


class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ["name", "country", "latitude", "longitude"]


class ReadingForm(forms.ModelForm):
    # The city comes from the URL, not from the form, so it is passed in.
    # min above max and humidity 0 to 100 are enforced by the model
    # (Reading.clean and the field validators), not repeated here.
    def __init__(self, *args, city=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.city = city

    class Meta:
        model = Reading
        fields = ["date", "max_temp", "min_temp", "humidity", "notes"]
        widgets = {
            "date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get("date")
        if self.city and date:
            duplicates = Reading.objects.filter(city=self.city, date=date)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error("date", "This city already has a reading for that date.")
        return cleaned