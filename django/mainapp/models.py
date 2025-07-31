from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User, Group
from django.utils.crypto import get_random_string
from datetime import timedelta


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    first_contact = models.DateTimeField(default=now, editable=False)
    recent_contact = models.DateTimeField(blank=True, null=True)
    interest = models.CharField(max_length=100)
    first_session = models.DateTimeField(blank=True, null=True)
    custnotes = models.TextField(
        blank=True, null=True, verbose_name="Customer General Notes")

    # Magic link for future possible user interaction
    magic_link_token = models.CharField(max_length=100, blank=True, null=True)
    magic_link_expires = models.DateTimeField(blank=True, null=True)

    def generate_magic_link(self):
        self.magic_link_token = get_random_string(50)
        self.magic_link_expires = now() + timedelta(hours=24)
        self.save()
        return self.magic_link_token

    def __str__(self):
        return f"{self.user.username}'s profile"


class Appointment(models.Model):
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    date = models.DateTimeField()
    kp_notes = models.TextField(
        blank=True, null=True, verbose_name="Key Points")
    fu_notes = models.TextField(
        blank=True, null=True, verbose_name="Follow Up Actions")
    invoiced = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    # You might want to track when the appointment was created/modified
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment for {self.customer.user.username} on {self.date}"

    class Meta:
        ordering = ['-date']  # Most recent appointments first


class Banner(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    image = models.ImageField(upload_to='banners/')
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']


class Card(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='cards/')
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']


class Contact(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name')
    email = models.EmailField(verbose_name='E-Mail')
    subject = models.CharField(max_length=255, verbose_name='Subject')
    message = models.TextField(verbose_name='Message')
    when_sent = models.DateTimeField(default=now, editable=False)
    replied = models.BooleanField(default=False)
    when_replied = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
