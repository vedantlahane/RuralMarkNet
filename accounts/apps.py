from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self) -> None:
        """Import signals when the app is ready."""
        from . import signals  # noqa: F401
