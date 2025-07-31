from django import forms
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils.timezone import now
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm
from django.utils.html import format_html
from decouple import config

from .models import Contact, CustomerProfile, Appointment
from .utils import enqueue_email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class ContactForm(forms.ModelForm):
    SUBJECT_CHOICES = [
        ('Executive Coaching', 'Executive Coaching'),
        ('HR Advisory & Consultation', 'HR Advisory & Consultation'),
    ]

    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Subject'
    )

    class Meta:
        model = Contact
        fields = ('name', 'email', 'subject', 'message')
        exclude = ('when_sent', 'replied', 'when_replied')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your message...',
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields automatically
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        instance = super().save(commit=commit)

        if commit:
            self._process_contact_submission(instance)

        return instance

    def _process_contact_submission(self, instance):
        """Handle all post-save operations for a contact submission"""
        email = self.cleaned_data['email']
        name = self.cleaned_data['name']
        interest = self.cleaned_data['subject']

        # Create or get user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': name.split(' ')[0],
                'last_name': ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else '',
            }
        )

        # Create or update user profile
        from .models import CustomerProfile
        profile, profile_created = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                'first_contact': now(),
                'interest': interest,
                'recent_contact': now()
            }
        )

        if not profile_created:
            # Update recent contact for existing users
            profile.recent_contact = now()
            profile.save()

        if profile_created:
            profile.generate_magic_link()

        # Add to customers group
        customers_group, _ = Group.objects.get_or_create(name='Customers')
        user.groups.add(customers_group)

        # Queue the email to be sent after transaction commits
        enqueue_email(instance)


class CustomerUpdateForm(forms.ModelForm):
    # Add read-only fields to display user info
    username = forms.CharField(disabled=True, required=False)
    email = forms.EmailField(disabled=True, required=False)
    first_contact_display = forms.CharField(
        disabled=True,
        required=False,
        label="First Contact"
    )

    class Meta:
        model = CustomerProfile
        fields = ['recent_contact', 'first_session', 'interest', 'custnotes']
        widgets = {
            'recent_contact': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'first_session': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'interest': forms.TextInput(attrs={'placeholder': 'Customer interests or focus areas'}),
            'custnotes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values for read-only fields
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_contact_display'].initial = self.instance.first_contact.strftime(
                '%Y-%m-%d %H:%M')

        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

            # Set current datetime as default for empty datetime fields
            if isinstance(field, forms.DateTimeField) and not self.initial.get(field_name):
                field.initial = now().strftime('%Y-%m-%dT%H:%M')

            # Add help text for interest field
            if field_name == 'interest':
                field.help_text = format_html(
                    '<span class="text-muted">{}</span>', "Customer's primary interest or focus area")


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'invoiced', 'paid', 'kp_notes', 'fu_notes']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'kp_notes': forms.Textarea(attrs={'rows': 3}),
            'fu_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs.update({'class': 'form-control'})
        self.fields['kp_notes'].widget.attrs.update({'class': 'form-control'})
        self.fields['fu_notes'].widget.attrs.update({'class': 'form-control'})
        self.fields['invoiced'].widget.attrs.update(
            {'class': 'form-check-input'})
        self.fields['paid'].widget.attrs.update({'class': 'form-check-input'})
