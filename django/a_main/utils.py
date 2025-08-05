# utils.py
import logging
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from django.core.mail import EmailMessage
from django.db import transaction

logger = logging.getLogger(__name__)


def send_email(instance, subject_template=None, body_template=None, html_template=None, extra_context=None):
    """
    Sends an email with configurable templates and logging.

    Args:
        instance: The model instance with email information
        subject_template: Optional template string for subject
        body_template: Optional template string for body
        html_template: Optional template string for HTML content
        extra_context: Additional context dict for template rendering
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Prepare context for templates
        context = {
            'email': getattr(instance, 'email', ''),
            'subject': getattr(instance, 'subject', ''),
            'message': getattr(instance, 'message', ''),
            'name': getattr(instance, 'name', ''),
            'instance': instance,
        }
        if extra_context:
            context.update(extra_context)

        # Use provided templates or defaults
        subject = subject_template or "From: {email} Regarding: {subject}"
        body = body_template or "Contact Form Submission:\n\nFrom: {name} <{email}>\nSubject: {subject}\n\nMessage:\n{message}"

        # Format templates with context
        formatted_subject = subject.format(**context)
        formatted_body = body.format(**context)

        print("===================================DEBUG START====================================")
        print(f"DEBUG - Instance contents: {vars(instance)}")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print(f"DEBUG - Formatted subject: {formatted_subject}")
        print(f"DEBUG - Formatted subject: {formatted_body}")
        print(
            f"DEBUG - Attempting to send from e-mail address: {settings.EMAIL_HOST_USER}")
        print(f"DEBUG - Attempting to send to: {instance.email}")
        print(f"DEBUG - Reply to: {settings.EMAIL_HOST_USER}")
        print("====================================DEBUG END=====================================")

        # Create and send email
        email = EmailMessage(
            subject=formatted_subject,
            body=formatted_body,
            from_email=settings.EMAIL_HOST_USER,
            to=[settings.EMAIL_HOST_USER],
            reply_to=[instance.email],
        )

        # Add HTML content if provided
        if hasattr(instance, 'html_message') or html_template:
            html_content = getattr(
                instance, 'html_message', None) or html_template
            if html_content:
                formatted_html = html_content.format(**context)
                email.content_subtype = "html"
                email.body = formatted_html

        sent_count = email.send(fail_silently=False)
        logger.info(
            f"Successfully sent email to {instance.email} (ID: {getattr(instance, 'id', 'unknown')}")
        return sent_count > 0

    except Exception as e:
        logger.error(
            f"Failed to send email to {getattr(instance, 'email', 'unknown')}. "
            f"Error: {str(e)}",
            exc_info=True
        )
        return False


def enqueue_email(instance):
    """
    Wrapper function to queue the email sending after transaction commits
    """
    transaction.on_commit(lambda: send_email(instance))
