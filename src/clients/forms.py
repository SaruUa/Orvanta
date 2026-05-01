from django import forms

from config.form_ui import BootstrapFormMixin

from .models import Client


class ClientForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Client
        fields = ['full_name', 'phone', 'email', 'birth_date', 'notes', 'is_active']
        labels = {
            'full_name': 'ПІБ',
            'phone': 'Телефон',
            'email': 'Email',
            'birth_date': 'Дата народження',
            'notes': 'Примітки',
            'is_active': 'Активний',
        }
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Наприклад, Іваненко Іван'}),
            'phone': forms.TextInput(attrs={'placeholder': '+380XXXXXXXXX'}),
            'email': forms.EmailInput(attrs={'placeholder': 'client@example.com'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Додаткова інформація про клієнта',
            }),
        }


class ClientFilterForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='Пошук',
        widget=forms.TextInput(attrs={'placeholder': 'ПІБ, телефон або email'}),
    )
    is_active = forms.ChoiceField(
        required=False,
        label='Статус',
        choices=[
            ('', 'Усі'),
            ('true', 'Активні'),
            ('false', 'Неактивні'),
        ],
    )
