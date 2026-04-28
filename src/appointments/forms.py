from django import forms

from clients.models import Client
from services_catalog.models import Service
from users.models import User, UserRole

from .models import Appointment, AppointmentStatus


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'client',
            'service',
            'employee',
            'appointment_date',
            'start_time',
            'end_time',
            'status',
            'comment',
        ]
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

        if organization is None:
            self.fields['client'].queryset = Client.objects.none()
            self.fields['service'].queryset = Service.objects.none()
            self.fields['employee'].queryset = User.objects.none()
        else:
            self.fields['client'].queryset = Client.objects.filter(
                organization=organization,
            ).order_by('full_name')
            self.fields['service'].queryset = Service.objects.filter(
                organization=organization,
            ).order_by('name')
            self.fields['employee'].queryset = User.objects.filter(
                role=UserRole.EMPLOYEE,
                is_active=True,
                organization=organization,
            ).order_by('username')

    def clean(self):
        cleaned_data = super().clean()
        client = cleaned_data.get('client')
        service = cleaned_data.get('service')
        employee = cleaned_data.get('employee')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if self.organization:
            if client and client.organization_id != self.organization.id:
                raise forms.ValidationError('Обраний клієнт не належить вашій організації.')
            if service and service.organization_id != self.organization.id:
                raise forms.ValidationError('Обрана послуга не належить вашій організації.')
            if employee and employee.organization_id != self.organization.id:
                raise forms.ValidationError('Обраний співробітник не належить вашій організації.')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(
                'Час завершення запису повинен бути пізнішим за час початку.'
            )

        return cleaned_data


class AppointmentFilterForm(forms.Form):
    appointment_date = forms.DateField(
        required=False,
        label='Дата',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    status = forms.ChoiceField(
        required=False,
        label='Статус',
        choices=[('', 'Усі статуси')] + list(AppointmentStatus.choices),
    )
    employee = forms.ModelChoiceField(
        required=False,
        label='Співробітник',
        queryset=User.objects.none(),
        empty_label='Усі співробітники',
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is None:
            self.fields['employee'].queryset = User.objects.none()
        else:
            self.fields['employee'].queryset = User.objects.filter(
                role=UserRole.EMPLOYEE,
                is_active=True,
                organization=organization,
            ).order_by('username')
