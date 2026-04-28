from django import forms

from .models import User, UserRole


class UserFilterForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='Пошук',
        widget=forms.TextInput(attrs={'placeholder': 'Username або email'}),
    )
    role = forms.ChoiceField(
        required=False,
        label='Роль',
        choices=[('', 'Усі ролі')] + list(UserRole.choices),
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


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role']
