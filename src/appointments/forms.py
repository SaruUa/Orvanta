from django import forms

from .models import Appointment


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

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(
                'Час завершення запису повинен бути пізнішим за час початку.'
            )

        return cleaned_data
