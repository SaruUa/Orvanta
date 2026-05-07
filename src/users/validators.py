import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class SymbolPasswordValidator:
    """
    Перевіряє що пароль містить хоча б одну велику літеру,
    одну малу літеру, одну цифру і один спецсимвол.
    Відповідає підказці у формі: A–Z, a–z, 0–9, ! @ # $ % ^ & * ( ) _ - + =
    """
    SYMBOLS = r'[!@#$%^&*()\-_+=]'

    def validate(self, password, user=None):
        errors = []
        if not re.search(r'[A-Z]', password):
            errors.append('Пароль повинен містити хоча б одну велику літеру (A–Z).')
        if not re.search(r'[a-z]', password):
            errors.append('Пароль повинен містити хоча б одну малу літеру (a–z).')
        if not re.search(r'[0-9]', password):
            errors.append('Пароль повинен містити хоча б одну цифру (0–9).')
        if not re.search(self.SYMBOLS, password):
            errors.append('Пароль повинен містити хоча б один спецсимвол (! @ # $ % ^ & * ( ) _ - + =).')
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            'Пароль повинен містити: велику літеру, малу літеру, '
            'цифру та спецсимвол (! @ # $ % ^ & * ( ) _ - + =).'
        )
