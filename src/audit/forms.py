from django import forms

from users.models import User

from .models import AuditActionType, AuditEntityType


class AuditLogFilterForm(forms.Form):
    user = forms.ModelChoiceField(
        required=False,
        label='Користувач',
        queryset=User.objects.none(),
        empty_label='Усі користувачі',
    )
    action_type = forms.ChoiceField(
        required=False,
        label='Тип дії',
        choices=[('', 'Усі дії')] + list(AuditActionType.choices),
    )
    entity_type = forms.ChoiceField(
        required=False,
        label='Тип сутності',
        choices=[('', 'Усі сутності')] + list(AuditEntityType.choices),
    )
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

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is None:
            self.fields['user'].queryset = User.objects.none()
        else:
            self.fields['user'].queryset = User.objects.filter(
                organization=organization,
            ).order_by('username')
