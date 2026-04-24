from django import forms

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = User.objects.filter(
            role=UserRole.EMPLOYEE,
            is_active=True,
        ).order_by('username')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

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
        queryset=User.objects.filter(role=UserRole.EMPLOYEE, is_active=True).order_by('username'),
        empty_label='Усі співробітники',
    )