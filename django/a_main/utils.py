import logging
from ics import Calendar, Event
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
import tempfile
import os
from typing import List, Optional

from .microsoft_graph import MicrosoftGraphEmailSender

logger = logging.getLogger(__name__)


def send_contact_email(context):
    email_sender = MicrosoftGraphEmailSender()
    if email_sender.send_email(
        to_email=settings.EMAIL_HOST_USER,
        is_html=True,
        subject=f"{context.interest} - {context.name} - {context.email}",
        message=f"""
            <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
            <html lang="en">
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <title>Message Received</title>
                </head>
                <body style="margin:0; padding:0; background-color:#F2F2F2; font-family: Arial, sans-serif; color:#333333;">
                    <center>
                        <!-- Main Wrapper -->
                        <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#F2F2F2">
                            <tr>
                                <td align="center" valign="top">
                                    <!-- Header Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width:600px;">
                                        <tr>
                                            <td align="center" valign="top" style="padding:20px 0;">
                                                <img src="https://dyvlife.your-voyage.life/static/images/header_brand.png" width="200" height="auto" alt="Your-Voyage Logo" style="display:block; height:auto;">
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Content Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF" style="max-width:600px; border-radius:4px; box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                                        <tr>
                                            <td align="left" valign="top" style="padding:40px 30px;">
                                                <h1 style="margin:0 0 20px 0; font-size:24px; color:#333333;">
                                                {context.name} has reached out with the following interest: {context.interest}.
                                                </h1>

                                                <p style="margin:0 0 20px 0; font-size:16px; line-height:24px;">
                                                    Hello {context.name},
                                                </p>

                                                <p style="margin:0 0 20px 0; font-size:16px; line-height:24px;">
                                                    Here is what they had to say:\n\n{context.instance.message}.
                                                </p>
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Footer Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width:600px;">
                                        <tr>
                                            <td align="center" valign="top" style="padding:20px 0; color:#999999; font-size:12px;">
                                                &copy; 2025 Your-Voyage.life All rights reserved.
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
        """
    ) and email_sender.send_email(
        to_email=context.email,
        is_html=True,
        subject="Your-Voyage has Received Your Message",
        message=f"""
            <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
            <html lang="en">
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <title>Message Received</title>
                </head>
                <body style="margin:0; padding:0; background-color:#F2F2F2; font-family: Arial, sans-serif; color:#333333;">
                    <center>
                        <!-- Main Wrapper -->
                        <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#F2F2F2">
                            <tr>
                                <td align="center" valign="top">
                                    <!-- Header Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width:600px;">
                                        <tr>
                                            <td align="center" valign="top" style="padding:20px 0;">
                                                <img src="https://dyvlife.your-voyage.life/static/images/header_brand.png" width="200" height="auto" alt="Your-Voyage Logo" style="display:block; height:auto;">
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Content Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF" style="max-width:600px; border-radius:4px; box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                                        <tr>
                                            <td align="left" valign="top" style="padding:40px 30px;">
                                                <h1 style="margin:0 0 20px 0; font-size:24px; color:#333333;">Message Received!</h1>

                                                <p style="margin:0 0 20px 0; font-size:16px; line-height:24px;">
                                                    Hello {context.name},
                                                </p>

                                                <p style="margin:0 0 20px 0; font-size:16px; line-height:24px;">
                                                    Thank you for reaching out to Your-Voyage regarding {context.interest}.<br>
                                                    We have received your message and will get back to you shortly.
                                                </p>

                                                <p style="margin:0 0 10px 0; font-size:16px; line-height:24px;">
                                                    Best Regards,
                                                </p>

                                                <p style="margin:0; font-size:16px; line-height:24px;">
                                                    Xiaoyang
                                                </p>
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Footer Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width:600px;">
                                        <tr>
                                            <td align="center" valign="top" style="padding:20px 0; color:#999999; font-size:12px;">
                                                &copy; 2025 Your-Voyage.life All rights reserved.
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
        """,
    ):
        return redirect('sent')
    else:
        return redirect('send-fail')


def generate_ics_for_appointment(appointment):
    """Generate ICS file content for an appointment."""
    cal = Calendar()
    event = Event()
    event.name = f"Appointment with {appointment.customer.user.get_full_name() or appointment.customer.user.username}"
    event.begin = appointment.date
    event.end = appointment.date + \
        timedelta(hours=1)  # Assuming 1 hour duration
    event.description = f"A Zoom link will be emailed to you on the day of the appointment."
    event.organizer = settings.EMAIL_HOST_USER
    cal.events.add(event)
    return str(cal)


def send_calendar_invite(request, appointment):
    customer = appointment.customer
    user = customer.user

    # Generate ICS content
    ics_content = generate_ics_for_appointment(appointment)

    subject_template = f"Your-Voyage Appointment Confirmation: {appointment.date.strftime('%Y-%m-%d %H:%M')}"
    body_template = f"""
                <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
            <html lang="en">
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <title>Message Received</title>
                </head>
                <body style="margin:0; padding:0; background-color:#F2F2F2; font-family: Arial, sans-serif; color:#333333;">
                    <center>
                        <!-- Main Wrapper -->
                        <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#F2F2F2">
                            <tr>
                                <td align="center" valign="top">
                                    <!-- Header Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width:600px;">
                                        <tr>
                                            <td align="center" valign="top" style="padding:20px 0;">
                                                <img src="https://dyvlife.your-voyage.life/static/images/header_brand.png" width="200" height="auto" alt="Your-Voyage Logo" style="display:block; height:auto;">
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Content Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF" style="max-width:600px; border-radius:4px; box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                                        <tr>
                                            <td align="left" valign="top" style="padding:40px 30px;">
                                                <h1 style="margin:0 0 20px 0; font-size:24px; color:#333333;">Appointment Confirmation</h1>

                                                <p style="margin:0 0 20px 0; font-size:16px; line-height:24px;">
                                                    Hello {user.get_full_name() or user.username},,
                                                </p>

                                                <p style="margin:0 0 20px 0; font-size:16px; line-height:24px;">
                                                    This is a confirmation for your appointment on {appointment.date.strftime('%Y-%m-%d at %H:%M')}.<br>
                                                    For your convienience, a calendar invite is attached.
                                                </p>

                                                <p style="margin:0 0 10px 0; font-size:16px; line-height:24px;">
                                                    Best Regards,
                                                </p>

                                                <p style="margin:0; font-size:16px; line-height:24px;">
                                                    Xiaoyang
                                                </p>
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Footer Section -->
                                    <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width:600px;">
                                        <tr>
                                            <td align="center" valign="top" style="padding:20px 0; color:#999999; font-size:12px;">
                                                &copy; 2025 Your-Voyage.life All rights reserved.
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </center>
                </body>
            </html>
    """
    # Create email
    email_sender = MicrosoftGraphEmailSender()

    with tempfile.NamedTemporaryFile(mode='w', prefix=f"appointment-{appointment.date.strftime('%Y-%m-%d')}", suffix='.ics', delete=False) as temp_file:
        temp_file.write(ics_content)
        temp_file.flush()  # Force write to disk
        temp_path = temp_file.name

        # DEBUG: Verify file content
        # with open(temp_path, 'r') as check_file:
        #   print("FILE CONTENTS:", check_file.read())

        try:
            success = email_sender.send_email(
                to_email=user.email,
                subject=subject_template,
                message=body_template,
                bcc_recipients=[settings.EMAIL_HOST_USER],
                attachments=[temp_path],
                is_html=True
            )
        except Exception as e:
            print("Error sending email:", str(e))
            success = False
        finally:
            # DEBUG: Verify file still exists before deletion
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                messages.success(request, "Calendar invite sent successfully!")
                return redirect('customers-update', pk=appointment.customer.pk)
            else:
                print("Warning: Temp file already deleted")
                messages.error(request, "Failed to send calendar invite.")
                return redirect('send-fail')


def send_magic_link_email(request, context):
    customer = context.customer
    user = customer.user
    subject_template = "Your Magic Login Link"
    body_template = f'''
    Hello {context.profile.user.username},

    You requested a magic login link. Click the link below to access your account:

    {context.login_url}

    This link will expire in 24 hours.

    If you didn't request this, please ignore this email.
    '''

    html_template = f'''
    <p>Hello {context.profile.user.username},</p>
    <p>You requested a magic login link. Click the button below to access your account:</p>
    <p><a href="{context.login_url}" class="btn btn-primary">Login Now</a></p>
    <p>This link will expire in 24 hours.</p>
    <p>If you didn't request this, please ignore this email.</p>
    '''
    email_sender = MicrosoftGraphEmailSender()
    if email_sender.send_email(
        to_email=user.email,
        subject=subject_template,
        message=body_template,
        # attachments=ics_content
    ):
        messages.success(request, "Magic link sent successfully!")
    else:
        messages.error(request, "Failed to send magic link.")


# def send_appointment_invite(appointment):
#     """Send email with calendar invite for an appointment."""
#     try:
#         customer = appointment.customer
#         user = customer.user

#         # Generate ICS content
#         ics_content = generate_ics_for_appointment(appointment)

#         # Create email
#         subject = f"Appointment Confirmation: {appointment.date.strftime('%Y-%m-%d %H:%M')}"
#         body = f"""
#         Hello {user.get_full_name() or user.username},

#         This is a confirmation for your appointment on {appointment.date.strftime('%Y-%m-%d at %H:%M')}.

#         Key Points: {appointment.kp_notes or 'None'}
#         Follow Up Actions: {appointment.fu_notes or 'None'}

#         Please find the calendar invite attached.
#         """

#         print("===================================DEBUG START====================================")
#         print(f"DEBUG - Instance contents: {vars(appointment)}")
#         print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
#         print(f"DEBUG - Formatted subject: {subject}")
#         print(f"DEBUG - Formatted subject: {body}")
#         print(
#             f"DEBUG - Attempting to send from e-mail address: {settings.EMAIL_HOST_USER}")
#         print(f"DEBUG - Attempting to send to: {user.email}")
#         print(f"DEBUG - Reply to: {settings.EMAIL_HOST_USER}")
#         print("====================================DEBUG END=====================================")

#         email = EmailMessage(
#             subject=subject,
#             body=body,
#             from_email=settings.EMAIL_HOST_USER,
#             to=[user.email, settings.EMAIL_HOST_USER],
#             reply_to=[settings.EMAIL_HOST_USER],
#         )

#         # Attach ICS file
#         email.attach(
#             filename='appointment.ics',
#             content=ics_content,
#             mimetype='text/calendar'
#         )

#         email.send()
#         logger.info(f"Successfully sent appointment invite to {user.email}")
#         return True

#     except Exception as e:
#         logger.error(
#             f"Failed to send appointment invite: {str(e)}", exc_info=True)
#         return False


# def send_email(instance, subject_template=None, body_template=None, html_template=None, extra_context=None):
#     """
#     Sends an email with configurable templates and logging.

#     Args:
#         instance: The model instance with email information
#         subject_template: Optional template string for subject
#         body_template: Optional template string for body
#         html_template: Optional template string for HTML content
#         extra_context: Additional context dict for template rendering
#     Returns:
#         bool: True if email was sent successfully, False otherwise
#     """
#     try:
#         # Prepare context for templates
#         context = {
#             'email': getattr(instance, 'email', ''),
#             'subject': getattr(instance, 'subject', ''),
#             'message': getattr(instance, 'message', ''),
#             'name': getattr(instance, 'name', ''),
#             'instance': instance,
#         }
#         if extra_context:
#             context.update(extra_context)

#         # Use provided templates or defaults
#         subject = subject_template or "From: {email} Regarding: {subject}"
#         body = body_template or "Contact Form Submission:\n\nFrom: {name} <{email}>\nSubject: {subject}\n\nMessage:\n{message}"

#         # Format templates with context
#         formatted_subject = subject.format(**context)
#         formatted_body = body.format(**context)

#         print("===================================DEBUG START====================================")
#         print(f"DEBUG - Instance contents: {vars(instance)}")
#         print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
#         print(f"DEBUG - Formatted subject: {formatted_subject}")
#         print(f"DEBUG - Formatted subject: {formatted_body}")
#         print(
#             f"DEBUG - Attempting to send from e-mail address: {settings.EMAIL_HOST_USER}")
#         print(f"DEBUG - Attempting to send to: {instance.email}")
#         print(f"DEBUG - Reply to: {settings.EMAIL_HOST_USER}")
#         print("====================================DEBUG END=====================================")

#         # Create and send email
#         email = EmailMessage(
#             subject=formatted_subject,
#             body=formatted_body,
#             from_email=settings.EMAIL_HOST_USER,
#             to=[settings.EMAIL_HOST_USER],
#             reply_to=[instance.email],
#         )

#         # Add HTML content if provided
#         if hasattr(instance, 'html_message') or html_template:
#             html_content = getattr(
#                 instance, 'html_message', None) or html_template
#             if html_content:
#                 formatted_html = html_content.format(**context)
#                 email.content_subtype = "html"
#                 email.body = formatted_html

#         sent_count = email.send(fail_silently=False)
#         logger.info(
#             f"Successfully sent email to {instance.email} (ID: {getattr(instance, 'id', 'unknown')}")
#         return sent_count > 0

#     except Exception as e:
#         logger.error(
#             f"Failed to send email to {getattr(instance, 'email', 'unknown')}. "
#             f"Error: {str(e)}",
#             exc_info=True
#         )
#         return False


# def enqueue_email(instance):
#     """
#     Wrapper function to queue the email sending after transaction commits
#     """
#     transaction.on_commit(lambda: send_email(instance))
