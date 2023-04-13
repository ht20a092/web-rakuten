from django.apps import AppConfig

class MyAppConfigTemp(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        from . import tasks
