from django import forms
from django.utils.timezone import now
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm
from django.utils.html import format_html

from .models import Contact, CustomerProfile, Appointment, Content, ContentMedia

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
    class Meta:
        model = Contact
        fields = ('name', 'email', 'subject', 'message')
        exclude = ('when_sent', 'replied', 'when_replied')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name',
                'rows': 1,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com',
                'rows': 1,
            }),
            'subject': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Reason for your inquiry...',
                'rows': 1,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your message...',
                'rows': 6,
            }),
        }

    def __init__(self, *args, subject=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields automatically
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        if subject:
            self.fields['subject'].initial = subject

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
    full_name = forms.CharField(
        disabled=True, required=False, label="Full Name")
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
            self.fields['full_name'].initial = self.instance.user.get_full_name(
            ) or self.instance.user.username
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


class BannerCreateForm(forms.ModelForm):
    image = forms.ImageField(required=True, label="Banner Image")

    class Meta:
        model = Content
        fields = ['title', 'description', 'enabled']
        labels = {
            'title': 'Banner Title',
            'description': 'Banner Message',
            'enabled': 'Enable Banner'
        }
        help_texts = {
            'description': 'This text will be displayed to users',
            'enabled': 'Uncheck to temporarily disable this banner'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field == 'image':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})
            elif field != 'enabled':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})
            else:
                self.fields[field].widget.attrs.update(
                    {'class': 'form-check-input'})

            if self.fields[field].help_text:
                self.fields[field].widget.attrs.update({
                    'aria-describedby': f'help_{field}'
                })

    def save(self, commit=True):
        content = super().save(commit=False)
        content.content_type = 'BANNER'
        if commit:
            content.save()
            # Create the associated ContentMedia
            ContentMedia.objects.create(
                content=content,
                file=self.cleaned_data['image'],
                media_type='IMAGE'
            )
        return content


class BannerUpdateForm(forms.ModelForm):
    image = forms.ImageField(required=False, label="Update Banner Image")
    current_image = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Content
        fields = ['title', 'description', 'enabled']
        labels = {
            'title': 'Banner Title',
            'description': 'Banner Message',
            'enabled': 'Enable Banner'
        }
        help_texts = {
            'description': 'This text will be displayed on the Banner',
            'enabled': 'Uncheck to temporarily hide this Banner'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            media = self.instance.media_files.first()
            if media:
                self.fields['current_image'].initial = media.file.url

        for field in self.fields:
            if field == 'image':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})
            elif field != 'enabled' and field != 'current_image':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})
            elif field == 'enabled':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-check-input'})

            if field == 'title':
                self.fields[field].widget.attrs['placeholder'] = 'Enter Banner title'
            elif field == 'description':
                self.fields[field].widget.attrs['placeholder'] = 'Enter Banner description'

            if self.fields[field].help_text:
                self.fields[field].widget.attrs.update({
                    'aria-describedby': f'help_{field}'
                })

    def save(self, commit=True):
        content = super().save(commit=True)
        new_image = self.cleaned_data.get('image')

        if new_image:  # Only update if a new image was provided
            # Delete old media if it exists
            self.instance.media_files.all().delete()
            # Create new media
            ContentMedia.objects.create(
                content=content,
                file=new_image,
                media_type='IMAGE'
            )
        return content


class CardCreateForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'description', 'enabled']
        labels = {
            'title': 'Product Title',
            'description': 'Product Description',
            'enabled': 'Enable Product Card'
        }
        help_texts = {
            'description': 'This text will be displayed to users',
            'enabled': 'Uncheck to temporarily disable this card'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'enabled':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})
            else:
                self.fields[field].widget.attrs.update(
                    {'class': 'form-check-input'})

            # Add aria-describedby for accessibility if help text exists
            if self.fields[field].help_text:
                self.fields[field].widget.attrs.update({
                    'aria-describedby': f'help_{field}'
                })


class CardUpdateForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['title', 'description', 'enabled']
        labels = {
            'title': 'Card Title',
            'description': 'Card Description',
            'enabled': 'Enable Card'
        }
        help_texts = {
            'description': 'This text will be displayed on the card',
            'enabled': 'Uncheck to temporarily hide this card'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'enabled':
                self.fields[field].widget.attrs.update(
                    {'class': 'form-control'})
            else:
                self.fields[field].widget.attrs.update(
                    {'class': 'form-check-input'})

            # Add placeholders
            if field == 'title':
                self.fields[field].widget.attrs['placeholder'] = 'Enter card title'
            elif field == 'description':
                self.fields[field].widget.attrs['placeholder'] = 'Enter card description'

            # Accessibility improvements
            if self.fields[field].help_text:
                self.fields[field].widget.attrs.update({
                    'aria-describedby': f'help_{field}'
                })


class ContentCreateForm(forms.ModelForm):
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'imageUpload',
            'accept': 'image/*'
        })
    )
    url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com'
        })
    )

    class Meta:
        model = Content
        fields = ['title', 'description', 'content_type', 'file', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
            'content_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'contentTypeSelect'
            }),
        }


class ContentUpdateForm(forms.ModelForm):
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'imageUpload',
            'accept': 'image/*'
        })
    )
    url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com'
        })
    )

    class Meta:
        model = Content
        fields = ['title', 'description', 'content_type',
                  'enabled', 'order', 'file', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
            'content_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'contentTypeSelect'
            }),
            'enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }
