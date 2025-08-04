from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """Represents a digital product or service (equivalent to Stripe's Product)"""

    class ProductType(models.TextChoices):
        SERVICE = 'service', _('Service')
        SOFTWARE = 'software', _('Software')
        SUBSCRIPTION = 'subscription', _('Subscription')

    # Matches Stripe ID format
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.SERVICE
    )
    # For storing additional Stripe-like data
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Price(models.Model):
    """Pricing model for products (equivalent to Stripe's Price)"""

    class BillingScheme(models.TextChoices):
        PER_UNIT = 'per_unit', _('Per unit')
        TIERED = 'tiered', _('Tiered')

    class RecurringInterval(models.TextChoices):
        DAY = 'day', _('Day')
        WEEK = 'week', _('Week')
        MONTH = 'month', _('Month')
        YEAR = 'year', _('Year')

    # Matches Stripe ID format
    id = models.CharField(max_length=255, primary_key=True)
    product = models.ForeignKey(
        Product, related_name='prices', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    currency = models.CharField(
        max_length=3, default='usd')  # ISO currency code
    unit_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Price in the smallest currency unit (e.g., cents for USD)")
    )
    billing_scheme = models.CharField(
        max_length=20,
        choices=BillingScheme.choices,
        default=BillingScheme.PER_UNIT
    )
    recurring = models.JSONField(
        null=True, blank=True)  # For recurring pricing
    lookup_key = models.CharField(
        max_length=255, blank=True)  # For price lookup
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Tiered pricing fields (if billing_scheme is TIERED)
    tiers = models.JSONField(null=True, blank=True)
    tiers_mode = models.CharField(max_length=20, blank=True)

    # Recurring subscription fields
    recurring_interval = models.CharField(
        max_length=10,
        choices=RecurringInterval.choices,
        blank=True,
        null=True
    )
    recurring_interval_count = models.PositiveIntegerField(
        null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.get_currency_display()}{self.unit_amount/100:.2f}"

    class Meta:
        ordering = ['-created_at']


class Feature(models.Model):
    """Features included with products/prices"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    products = models.ManyToManyField(
        Product, related_name='features', blank=True)
    prices = models.ManyToManyField(Price, related_name='features', blank=True)

    def __str__(self):
        return self.name


class Coupon(models.Model):
    """Discount coupons for products/prices"""

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED = 'fixed', _('Fixed amount')

    # Matches Stripe ID format
    id = models.CharField(max_length=255, primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    # Required for fixed amount
    currency = models.CharField(max_length=3, blank=True, null=True)
    active = models.BooleanField(default=True)
    valid_for_products = models.ManyToManyField(Product, blank=True)
    valid_for_prices = models.ManyToManyField(Price, blank=True)
    max_redemptions = models.PositiveIntegerField(null=True, blank=True)
    redeem_by = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    class Meta:
        ordering = ['-created_at']
