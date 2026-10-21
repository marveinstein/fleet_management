from django.apps import AppConfig

class FleetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fleet'
    label = 'fleet'  # Explicitly setting the label allows referencing 'fleet' directly
