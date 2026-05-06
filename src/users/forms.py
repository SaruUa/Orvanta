from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.db import transaction
from django.db.models import Q

from config.form_ui import BootstrapFormMixin

from .models import Organization, User, UserRole

SAFE_CREATE_ROLE_CHOICES = [
    (UserRole.MANAGER, dict(UserRole.choices)[UserRole.MANAGER]),
    (UserRole.EMPLOYEE, dict(UserRole.choices)[UserRole.EMPLOYEE]),
]


class UserFilterForm(forms.Form):
    query = forms.CharField(
        required=False,
        label='Пошук',
        widget=forms.TextInput(attrs={'placeholder': 'Ім’я користувача або email'}),
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


def _configure_user_creation_fields(fields):
    fields['username'].label = 'Ім’я користувача'
    fields['username'].help_text = 'До 150 символів. Дозволені літери, цифри та @/./+/-/_.'
    fields['username'].widget.attrs.setdefault('placeholder', 'username')

    fields['email'].widget.attrs.setdefault('placeholder', 'user@example.com')

    fields['password1'].label = 'Пароль'
    fields['password1'].help_text = 'Використайте надійний пароль, який відповідає вимогам системи.'
    fields['password1'].widget.attrs.setdefault('placeholder', 'Пароль')

    fields['password2'].label = 'Підтвердження пароля'
    fields['password2'].help_text = 'Введіть той самий пароль ще раз.'
    fields['password2'].widget.attrs.setdefault('placeholder', 'Підтвердження пароля')


class UserRoleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['role']
        labels = {
            'role': 'Роль',
        }


class SignupForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label='Email', required=True)
    organization_name = forms.CharField(label='Назва організації', max_length=255)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'organization_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _configure_user_creation_fields(self.fields)
        self.fields['password1'].widget.attrs['placeholder'] = 'A–Z, a–z, 0–9, ! @ # $ % ^ & * ( ) _ - + ='
        self.fields['organization_name'].widget.attrs.setdefault(
            'placeholder',
            'Назва вашої організації',
        )

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


class OrganizationUserCreateForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label='Email', required=True)
    role = forms.ChoiceField(label='Роль', choices=SAFE_CREATE_ROLE_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _configure_user_creation_fields(self.fields)

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


class UserProfileForm(BootstrapFormMixin, forms.ModelForm):
    email = forms.EmailField(label='Email', required=True)

    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.setdefault('placeholder', 'user@example.com')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Користувач із такою email-адресою вже існує.')
        return email


class OrganizationSettingsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']
        labels = {
            'name': 'Назва організації',
        }
        help_texts = {
            'name': 'Slug організації використовується для входу та не змінюється автоматично.',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Назва організації'}),
        }


class ConfirmDeleteUserForm(forms.Form):
    confirm = forms.BooleanField(widget=forms.HiddenInput, required=True)

    def __init__(self, *args, actor=None, target_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.target_user = target_user

    def clean(self):
        cleaned_data = super().clean()

        if self.actor is None or self.actor.role != UserRole.ADMIN:
            raise forms.ValidationError('У вас немає прав видаляти користувачів.')

        if self.actor.organization_id is None:
            raise forms.ValidationError('Неможливо видаляти користувачів без організації.')

        if self.target_user is None:
            raise forms.ValidationError('Користувача не знайдено в межах вашої організації.')

        if self.target_user.organization_id != self.actor.organization_id:
            raise forms.ValidationError('Користувача не знайдено в межах вашої організації.')

        if self.target_user.role == UserRole.ADMIN:
            admins_count = User.objects.filter(
                organization=self.actor.organization,
                role=UserRole.ADMIN,
            ).count()
            if admins_count <= 1:
                raise forms.ValidationError(
                    'Неможливо видалити останнього адміністратора організації.',
                )

        if self.target_user.pk == self.actor.pk:
            raise forms.ValidationError('Ви не можете видалити власний обліковий запис.')

        if self.target_user.employee_appointments.exists():
            raise forms.ValidationError(
                'Користувача не можна видалити, доки за ним закріплені записи. '
                'Спочатку перепризначте або видаліть ці записи.',
            )

        return cleaned_data

    def delete(self):
        self.target_user.delete()


class ConfirmDeleteOrganizationForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField(label='Ім’я користувача', max_length=150)
    organization = forms.CharField(label='Назва або slug організації', max_length=255)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.organization_obj = getattr(user, 'organization', None)
        self.fields['username'].widget.attrs.setdefault('placeholder', 'username')
        self.fields['organization'].widget.attrs.setdefault('placeholder', 'назва або slug')
        self.fields['password'].widget.attrs.setdefault('placeholder', 'password')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if self.user is None or username != self.user.username:
            raise forms.ValidationError('Ім’я користувача не збігається з поточним обліковим записом.')
        return username

    def clean_organization(self):
        organization_value = self.cleaned_data['organization'].strip()
        organization = self.organization_obj
        if organization is None:
            raise forms.ValidationError('Ваш користувач не прив’язаний до організації.')

        if organization_value not in {organization.name, organization.slug}:
            raise forms.ValidationError('Назва або slug організації не збігається.')

        return organization_value

    def clean_password(self):
        password = self.cleaned_data['password']
        if self.user is None:
            raise forms.ValidationError('Пароль не підтверджено.')

        authenticated_user = authenticate(username=self.user.username, password=password)
        if authenticated_user is None or authenticated_user.pk != self.user.pk:
            raise forms.ValidationError('Пароль не підтверджено.')

        return password

    def clean(self):
        cleaned_data = super().clean()

        if self.user is None or self.user.role != UserRole.ADMIN:
            raise forms.ValidationError('У вас немає прав видаляти організацію.')

        if self.organization_obj is None:
            raise forms.ValidationError('Ваш користувач не прив’язаний до організації.')

        return cleaned_data

    def delete(self):
        from appointments.models import Appointment, AppointmentStatusHistory
        from audit.models import AuditLog
        from clients.models import Client
        from services_catalog.models import Service, ServiceCategory

        organization = Organization.objects.get(pk=self.organization_obj.pk)
        user_ids = list(
            User.objects.filter(organization=organization).values_list('pk', flat=True),
        )
        appointment_ids = list(
            Appointment.objects.filter(
                Q(organization=organization) |
                Q(client__organization=organization) |
                Q(service__organization=organization) |
                Q(employee__organization=organization),
            ).values_list('pk', flat=True)
        )

        with transaction.atomic():
            AppointmentStatusHistory.objects.filter(
                Q(organization=organization) |
                Q(appointment_id__in=appointment_ids),
            ).delete()
            Appointment.objects.filter(pk__in=appointment_ids).delete()
            Client.objects.filter(organization=organization).delete()
            Service.objects.filter(organization=organization).delete()
            ServiceCategory.objects.filter(organization=organization).delete()
            AuditLog.objects.filter(
                Q(organization=organization) |
                Q(user_id__in=user_ids),
            ).delete()
            User.objects.filter(organization=organization).delete()
            AuditLog.objects.filter(organization=organization).delete()
            organization.delete()


class ProfilePasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['old_password'].label = 'Поточний пароль'
        self.fields['old_password'].widget.attrs.setdefault('placeholder', 'Поточний пароль')

        self.fields['new_password1'].label = 'Новий пароль'
        self.fields['new_password1'].help_text = (
            'Використайте надійний пароль, який відповідає вимогам системи.'
        )
        self.fields['new_password1'].widget.attrs.setdefault('placeholder', 'Новий пароль')

        self.fields['new_password2'].label = 'Підтвердження нового пароля'
        self.fields['new_password2'].help_text = 'Введіть новий пароль ще раз.'
        self.fields['new_password2'].widget.attrs.setdefault(
            'placeholder',
            'Підтвердження нового пароля',
        )


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
        self.fields['username'].label = 'Ім’я користувача'
        self.fields['username'].widget.attrs.setdefault('placeholder', 'username')
        self.fields['password'].label = 'Пароль'
        self.fields['password'].widget.attrs.setdefault('placeholder', 'password')
        self.fields['organization'].widget.attrs.setdefault('placeholder', 'slug або назва')

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
