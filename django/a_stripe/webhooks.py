# a_stripe/webhooks.py
import json
import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from a_stripe.models import Product, Price

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Handle events
    if event['type'] == 'product.created':
        product = event['data']['object']
        Product.objects.update_or_create(
            id=product.id,
            defaults={
                'name': product.name,
                'active': product.active
            }
        )

    elif event['type'] == 'price.created':
        price = event['data']['object']
        Product.objects.filter(id=price.product).exists():
            Price.objects.update_or_create(
                id=price.id,
                defaults={
                    'product_id': price.product,
                    'currency': price.currency,
                    'unit_amount': price.unit_amount
                }
            )

    return HttpResponse(status=200)
