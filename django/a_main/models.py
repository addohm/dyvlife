from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User, Group
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
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


class Content(models.Model):
    CONTENT_TYPES = [
        ('BANNER', 'Banners'),
        ('CARD', 'Product Cards'),
        ('ABOUT', 'About Us'),
        ('FAQ', 'Frequently Asked Questions'),
        ('PRIVACY', 'Privacy Policies'),
        ('TERMS', 'Terms of Service'),
    ]

    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()  # More generic than 'message'
    content_type = models.CharField(
        max_length=50,
        choices=CONTENT_TYPES,
        default='CARD'
    )
    enabled = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Content'
        verbose_name_plural = 'Contents'

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"


def content_media_upload_path(instance, filename):
    # Get the content_type from the parent Content instance
    content_type = instance.content.content_type.lower()
    # Return the path with content_type and date-based folders
    return f'{content_type}/{filename}'


class ContentMedia(models.Model):
    MEDIA_TYPES = [
        ('IMAGE', 'Image'),
        # ('VIDEO', 'Video'),
    ]

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    media_type = models.CharField(
        max_length=50,
        choices=MEDIA_TYPES,
        default='IMAGE'
    )
    file = models.FileField(upload_to=content_media_upload_path)
    thumbnail = ImageSpecField(
        source='file',
        processors=[ResizeToFill(400, 300)],
        format='JPEG',
        options={'quality': 80}
    )
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Content Media'
        verbose_name_plural = 'Content Media'

    def __str__(self):
        return f"Media for {self.content.title}"
