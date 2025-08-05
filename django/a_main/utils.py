import logging
from ics import Calendar, Event
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction

logger = logging.getLogger(__name__)


def generate_ics_for_appointment(appointment):
    """Generate ICS file content for an appointment."""
    cal = Calendar()
    event = Event()
    event.name = f"Appointment with {appointment.customer.user.get_full_name() or appointment.customer.user.username}"
    event.begin = appointment.date
    event.end = appointment.date + \
        timedelta(hours=1)  # Assuming 1 hour duration
    event.description = f"Key Points: {appointment.kp_notes}\n\nFollow Up: {appointment.fu_notes}"
    event.organizer = settings.EMAIL_HOST_USER
    cal.events.add(event)
    return str(cal)


def send_appointment_invite(appointment):
    """Send email with calendar invite for an appointment."""
    try:
        customer = appointment.customer
        user = customer.user

        # Generate ICS content
        ics_content = generate_ics_for_appointment(appointment)

        # Create email
        subject = f"Appointment Confirmation: {appointment.date.strftime('%Y-%m-%d %H:%M')}"
        body = f"""
        Hello {user.get_full_name() or user.username},

        This is a confirmation for your appointment on {appointment.date.strftime('%Y-%m-%d at %H:%M')}.

        Key Points: {appointment.kp_notes or 'None'}
        Follow Up Actions: {appointment.fu_notes or 'None'}

        Please find the calendar invite attached.
        """

        print("===================================DEBUG START====================================")
        print(f"DEBUG - Instance contents: {vars(appointment)}")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print(f"DEBUG - Formatted subject: {subject}")
        print(f"DEBUG - Formatted subject: {body}")
        print(
            f"DEBUG - Attempting to send from e-mail address: {settings.EMAIL_HOST_USER}")
        print(f"DEBUG - Attempting to send to: {user.email}")
        print(f"DEBUG - Reply to: {settings.EMAIL_HOST_USER}")
        print("====================================DEBUG END=====================================")

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email, settings.EMAIL_HOST_USER],
            reply_to=[settings.EMAIL_HOST_USER],
        )

        # Attach ICS file
        email.attach(
            filename='appointment.ics',
            content=ics_content,
            mimetype='text/calendar'
        )

        email.send()
        logger.info(f"Successfully sent appointment invite to {user.email}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send appointment invite: {str(e)}", exc_info=True)
        return False


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
