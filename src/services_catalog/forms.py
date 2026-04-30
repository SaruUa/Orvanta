from django import forms

from .models import Service, ServiceCategory


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'name', 'description', 'price', 'duration_minutes', 'is_active']
        labels = {
            'price': 'Базова вартість',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
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
