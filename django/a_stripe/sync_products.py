# a_stripe/management/commands/sync_products.py
from django.core.management.base import BaseCommand
from django.conf import settings
import stripe
from a_stripe.models import Product, Price

stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = 'Sync products and prices from Stripe'

    def handle(self, *args, **options):
        # Sync Products
        for stripe_product in stripe.Product.list().auto_paging_iter():
            product, _ = Product.objects.update_or_create(
                id=stripe_product.id,
                defaults={
                    'name': stripe_product.name,
                    'description': stripe_product.description,
                    'active': stripe_product.active,
                    'metadata': stripe_product.metadata
                }
            )

            # Sync Prices for each product
            for stripe_price in stripe.Price.list(product=stripe_product.id).auto_paging_iter():
                Price.objects.update_or_create(
                    id=stripe_price.id,
                    defaults={
                        'product': product,
                        'active': stripe_price.active,
                        'currency': stripe_price.currency,
                        'unit_amount': stripe_price.unit_amount,
                        'recurring': stripe_price.recurring,
                        'metadata': stripe_price.metadata
                    }
                )
        self.stdout.write(self.style.SUCCESS(
            'Successfully synced with Stripe'))
