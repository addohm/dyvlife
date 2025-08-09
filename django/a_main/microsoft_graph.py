import msal
import requests
import base64
from typing import List, Optional
from decouple import config


class MicrosoftGraphEmailSender:
    def __init__(self):
        self.CLIENT_ID = config("CLIENT_ID")
        self.CLIENT_SECRET = config("CLIENT_SECRET")
        self.TENANT_ID = config("TENANT_ID")
        self.USER_EMAIL = config("EMAIL_HOST_USER")  # Sender email

    def _acquire_token(self) -> Optional[str]:
        """Get an access token for Microsoft Graph API."""
        authority_url = f'https://login.microsoftonline.com/{self.TENANT_ID}'
        app = msal.ConfidentialClientApplication(
            authority=authority_url,
            client_id=self.CLIENT_ID,
            client_credential=self.CLIENT_SECRET
        )
        token = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"])
        return token.get("access_token")

    @staticmethod
    def _read_file_as_base64(file_path: str) -> str:
        """Read a file and return its base64-encoded content."""
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode('utf-8')

    def send_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        attachments: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        cc_recipients: Optional[List[str]] = None,
        is_html: bool = False  # Add this new parameter
    ) -> bool:
        """
        Send an email via Microsoft Graph API.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            message: Email body content.
            attachments: List of file paths to attach.
            is_html: Whether the message content is HTML (default: False)
        """
        access_token = self._acquire_token()
        if not access_token:
            print("Failed to acquire access token.")
            return False

        endpoint = f'https://graph.microsoft.com/v1.0/users/{self.USER_EMAIL}/sendMail'

        # Prepare email payload
        email_msg = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",  # Changed this line
                    "content": message
                },
                "toRecipients": [{
                    "emailAddress": {
                        "address": to_email
                    }
                }],
                "attachments": []
            },
            "saveToSentItems": "true"
        }

        if bcc_recipients:
            email_msg["message"]["bccRecipients"] = [{
                "emailAddress": {
                    "address": email
                }
            } for email in bcc_recipients]

        # Add CC recipients if provided
        if cc_recipients:
            email_msg["message"]["ccRecipients"] = [{
                "emailAddress": {
                    "address": email
                }
            } for email in cc_recipients]
        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                file_name = file_path.split("/")[-1]
                email_msg["message"]["attachments"].append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": file_name,
                    "contentType": "application/octet-stream",
                    "contentBytes": self._read_file_as_base64(file_path)
                })

        # Send the email
        response = requests.post(
            endpoint,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            json=email_msg
        )

        if response.ok:
            print(f"Email sent successfully to {to_email}!")
            return True
        else:
            print(f"Failed to send email. Error: {response.json()}")
            return False
