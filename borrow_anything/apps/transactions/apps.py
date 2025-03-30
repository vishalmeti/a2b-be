from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.transactions"
    # Add this method to import signals when the app is ready
    def ready(self):
        import apps.transactions.signals  # Import your signals module

        # The noqa comment below is sometimes used if linters complain about unused imports,
        # but the import itself is necessary to register the signals.
        # import apps.transactions.signals  # noqa F401
