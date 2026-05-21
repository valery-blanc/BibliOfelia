from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Comptes utilisateurs"

    def ready(self):
        # Active le signal post_save → sync role/is_staff/group
        from . import signals  # noqa: F401
