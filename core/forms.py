from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        label="Логин",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Придумайте логин"}),
    )
    email = forms.EmailField(
        label="Email (необязательно)",
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите пароль"}),
    )
    password2 = forms.CharField(
        label="Повтор пароля",
        widget=forms.PasswordInput(attrs={"placeholder": "Повторите пароль"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
