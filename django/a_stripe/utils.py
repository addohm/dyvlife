# a_stripe/utils.py
import stripe
from django.conf import settings
from a_stripe.models import Product

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(django_product):
    """Create a Stripe product from Django model"""
    return stripe.Product.create(
        id=str(django_product.id),
        name=django_product.name,
        description=django_product.description,
        metadata=django_product.metadata
    )


def create_stripe_price(django_price):
    """Create a Stripe price from Django model"""
    return stripe.Price.create(
        product=str(django_price.product.id),
        unit_amount=django_price.unit_amount,
        currency=django_price.currency,
        recurring={
            'interval': django_price.recurring_interval,
            'interval_count': django_price.recurring_interval_count
        } if django_price.recurring_interval else None
    )
