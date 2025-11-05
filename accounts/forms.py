"""Forms for account management."""
from __future__ import annotations

from typing import cast

from django import forms
from django.apps import apps
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class StyledFormMixin:
    """Apply consistent Tailwind classes to form widgets."""

    input_class = (
        "mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm "
        "text-slate-800 shadow-sm focus:border-emerald-500 focus:outline-none "
        "focus:ring-2 focus:ring-emerald-200"
    )
    checkbox_class = "mt-2 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
    checkbox_group_class = "mt-3 space-y-3"

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._apply_widget_styling()

    def _apply_widget_styling(self) -> None:
        text_like_inputs = {"text", "email", "password", "tel", "number", "url", "search"}
        fields = getattr(self, "fields", {})
        for name, field in fields.items():
            widget = field.widget
            css_class = self.input_class
            if isinstance(widget, forms.CheckboxSelectMultiple):
                existing_classes = widget.attrs.get("class", "").strip()
                widget.attrs["class"] = f"{existing_classes} {self.checkbox_group_class}".strip()
                continue
            if isinstance(widget, forms.CheckboxInput):
                css_class = self.checkbox_class
            existing_classes = widget.attrs.get("class", "").strip()
            widget.attrs["class"] = f"{existing_classes} {css_class}".strip()

            input_type = getattr(widget, "input_type", None)
            if input_type in text_like_inputs or isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("placeholder", field.label or "")
                widget.attrs.setdefault("autocomplete", name)


class UserRegistrationForm(StyledFormMixin, UserCreationForm):
    """Form used for farmer and customer sign-up."""

    role = forms.ChoiceField(choices=User.Roles.choices, label=_("Account Type"))
    preferred_language = forms.ChoiceField(
        choices=User.PREFERRED_LANGUAGE_CHOICES,
        label=_("Preferred Language"),
    )

    class Meta(UserCreationForm.Meta):  # type: ignore[attr-defined]
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


class ProfileForm(StyledFormMixin, forms.ModelForm):
    """Allow users to update contact details."""

    payment_methods = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Payment methods you accept"),
        help_text=_("Applies to customers purchasing your listings."),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "address")

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        instance = cast(User | None, getattr(self, "instance", None))
        field = self.fields.get("payment_methods")
        if instance and instance.role == User.Roles.FARMER and field is not None:
            payment_model = apps.get_model("payments", "Payment")
            if payment_model is not None:
                choices = cast(list[tuple[str, str]], payment_model.Providers.choices)  # type: ignore[attr-defined]
                field.choices = choices
                configured = instance.accepted_payment_methods
                if not configured:
                    configured = [code for code, _ in choices]
                field.initial = configured
        else:
            self.fields.pop("payment_methods", None)

    def clean_payment_methods(self):
        methods = self.cleaned_data.get("payment_methods")
        if self.instance.role == User.Roles.FARMER:
            if not methods:
                raise forms.ValidationError(_("Select at least one payment method."))
            payment_model = apps.get_model("payments", "Payment")
            if payment_model is not None:
                valid_methods = {code for code, _ in payment_model.Providers.choices}  # type: ignore[attr-defined]
                invalid = [code for code in methods if code not in valid_methods]
                if invalid:
                    raise forms.ValidationError(_("Unknown payment method selected."))
        return methods

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        if user.role == User.Roles.FARMER:
            methods = self.cleaned_data.get("payment_methods") or []
            user.accepted_payment_methods = sorted(methods)
        else:
            user.accepted_payment_methods = None
        if commit:
            user.save()
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    """Customized login form with remember-me option."""

    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Keep me signed in"),
    )
