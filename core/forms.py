from django import forms


class CitySearchForm(forms.Form):
    city = forms.CharField(
        label="Город",
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Например: Москва"}),
    )

    def clean_city(self):
        value = (self.cleaned_data.get("city") or "").strip()
        if not value:
            raise forms.ValidationError("Введите название города.")
        return value
