# a_stripe/apps.py
from django.apps import AppConfig


class AStripeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'a_stripe'

    def ready(self):
        import a_stripe.signals
