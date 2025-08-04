# a_stripe/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, Price
from .utils import create_stripe_product, create_stripe_price


@receiver(post_save, sender=Product)
def sync_product_to_stripe(sender, instance, created, **kwargs):
    if created:
        create_stripe_product(instance)


@receiver(post_save, sender=Price)
def sync_price_to_stripe(sender, instance, created, **kwargs):
    if created:
        create_stripe_price(instance)
