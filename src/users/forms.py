from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q

from .models import Organization, User, UserRole

SAFE_CREATE_ROLE_CHOICES = [
    (UserRole.MANAGER, dict(UserRole.choices)[UserRole.MANAGER]),
    (UserRole.EMPLOYEE, dict(UserRole.choices)[UserRole.EMPLOYEE]),
]


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


class SignupForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=True)
    organization_name = forms.CharField(label='Назва організації', max_length=255)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'organization_name')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Користувач із такою email-адресою вже існує.')
        return email

    def clean_organization_name(self):
        organization_name = self.cleaned_data['organization_name'].strip()
        if not organization_name:
            raise forms.ValidationError('Вкажіть назву організації.')
        if Organization.objects.filter(name__iexact=organization_name).exists():
            raise forms.ValidationError('Організація з такою назвою вже існує.')
        return organization_name


class OrganizationUserCreateForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=True)
    role = forms.ChoiceField(label='Роль', choices=SAFE_CREATE_ROLE_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Користувач із такою email-адресою вже існує.')
        return email

    def clean_role(self):
        role = self.cleaned_data['role']
        if role not in {UserRole.MANAGER, UserRole.EMPLOYEE}:
            raise forms.ValidationError('Недопустима роль для створення користувача.')
        return role


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Email', required=True)

    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Користувач із такою email-адресою вже існує.')
        return email


class OrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control'


class OrganizationAuthenticationForm(AuthenticationForm):
    organization = forms.CharField(
        label='Організація',
        required=False,
        max_length=255,
    )

    error_messages = {
        'invalid_login': 'Невірні дані входу або організація.',
        'inactive': 'Цей обліковий запис неактивний.',
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.order_fields(['username', 'password', 'organization'])

        for field in self.fields.values():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} form-control'.strip()

    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        organization_value = (cleaned_data.get('organization') or '').strip()

        if user is None:
            return cleaned_data

        if user.is_superuser and user.organization_id is None and not organization_value:
            return cleaned_data

        if not organization_value:
            raise self.get_invalid_login_error()

        organization = Organization.objects.filter(
            Q(slug__iexact=organization_value) | Q(name__iexact=organization_value),
        ).first()

        if organization is None:
            raise self.get_invalid_login_error()

        if user.organization_id != organization.id:
            raise self.get_invalid_login_error()

        if user.organization_id is None:
            raise self.get_invalid_login_error()

        return cleaned_data
