from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        # Receivers live at module level in api.signals: declared inside this
        # method they would be garbage collected as soon as it returns.
        from api import signals  # noqa: F401
