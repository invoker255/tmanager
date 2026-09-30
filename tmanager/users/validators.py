import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _



class ComplexityValidator:
    @staticmethod
    def validate(password, _user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Password must contain at least one uppercase letter'))
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Password must contain at least one lowercase letter'))
        if not re.search(r'[0-9]', password):
            raise ValidationError(_('Password must contain at least one number'))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\/]', password):
            raise ValidationError(_('Password must contain at least one special character'))
    @staticmethod
    def get_help_text():
        return _(
            "Your password must contain at least one uppercase letter, one lowercase letter, one number, and one special character."
        )