from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _register_schedules(sender, **kwargs):
    # Re-assert the nightly catalog sync after every migrate, so a fresh
    # database gets the beat schedule without touching project settings.
    from malahi_extension.tasks import register_nightly_sync
    try:
        register_nightly_sync()
    except Exception:  # django_celery_beat tables may not exist yet mid-migrate
        import logging
        logging.getLogger(__name__).warning(
            "Could not register Malahi nightly sync schedule", exc_info=True
        )


class MalahiExtensionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'malahi_extension'

    def ready(self):
        post_migrate.connect(_register_schedules, sender=self)
