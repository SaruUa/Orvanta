from django import forms

from appointments.models import AppointmentStatus
from config.form_ui import BootstrapFormMixin
from services_catalog.models import Service
from users.models import User, UserRole


class FinanceAnalyticsFilterForm(BootstrapFormMixin, forms.Form):
    date_from = forms.DateField(
        required=False,
        label='Дата від',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label='Дата до',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    service = forms.ModelChoiceField(
        required=False,
        label='Послуга',
        queryset=Service.objects.none(),
        empty_label='Усі послуги',
    )
    employee = forms.ModelChoiceField(
        required=False,
        label='Співробітник',
        queryset=User.objects.none(),
        empty_label='Усі співробітники',
    )
    status = forms.ChoiceField(
        required=False,
        label='Статус',
        choices=list(AppointmentStatus.choices),
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].initial = AppointmentStatus.COMPLETED

        if organization is None:
            return

        self.fields['service'].queryset = Service.objects.filter(
            organization=organization,
        ).order_by('name')
        self.fields['employee'].queryset = User.objects.filter(
            organization=organization,
            role=UserRole.EMPLOYEE,
        ).order_by('username')
