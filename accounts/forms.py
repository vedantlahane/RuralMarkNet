"""Forms for account management."""
from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class UserRegistrationForm(UserCreationForm):
    """Form used for farmer and customer sign-up."""

    role = forms.ChoiceField(choices=User.Roles.choices, label=_("Account Type"))
    preferred_language = forms.ChoiceField(
        choices=[("en", _("English")), ("hi", _("Hindi"))],
        label=_("Preferred Language"),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "preferred_language",
            "password1",
            "password2",
        )


class ProfileForm(forms.ModelForm):
    """Allow users to update contact details."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "address")


class LoginForm(AuthenticationForm):
    """Customized login form with remember-me option."""

    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Keep me signed in"),
    )
