from django import forms

from config.form_ui import BootstrapFormMixin

from .models import Service, ServiceCategory


class ServiceCategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description']
        labels = {
            'name': 'Назва',
            'description': 'Опис',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Наприклад, Консультації'}),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Короткий опис категорії',
            }),
        }


class ServiceForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'name', 'description', 'price', 'duration_minutes', 'is_active']
        labels = {
            'category': 'Категорія',
            'name': 'Назва',
            'description': 'Опис',
            'price': 'Базова вартість',
            'duration_minutes': 'Тривалість, хв',
            'is_active': 'Активна',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Назва послуги'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Що входить до послуги',
            }),
            'price': forms.NumberInput(attrs={
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'min': '1',
                'step': '1',
                'placeholder': '60',
            }),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Без категорії'
        if organization is None:
            self.fields['category'].queryset = ServiceCategory.objects.none()
        else:
            self.fields['category'].queryset = ServiceCategory.objects.filter(
                organization=organization,
            ).order_by('name')


class ServiceFilterForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='Пошук',
        widget=forms.TextInput(attrs={'placeholder': 'Назва або опис послуги'}),
    )
    category = forms.ModelChoiceField(
        required=False,
        label='Категорія',
        queryset=ServiceCategory.objects.none(),
        empty_label='Усі категорії',
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

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is None:
            self.fields['category'].queryset = ServiceCategory.objects.none()
        else:
            self.fields['category'].queryset = ServiceCategory.objects.filter(
                organization=organization,
            ).order_by('name')
