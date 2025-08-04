import json
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, ListView, View, DeleteView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.timezone import now
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import CustomerProfile, Appointment, Content
from .forms import *

from .utils import enqueue_email

# ======================
# CUSTOM MIXINS
# ======================


class UserGroupContextMixin:
    """Adds user group information to context."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass cards in, mainly for the header.  Only need title and url
        cards = Content.objects.filter(
            content_type='CARD',
            enabled=True
        ).order_by('-created_at')

        context['cards'] = [
            {'id': card.id, 'title': card.title}
            for card in cards
        ]

        user = self.request.user

        if user.is_authenticated:
            context['is_customer'] = user.groups.filter(
                name='Customers Group').exists()
            context['is_manager'] = user.groups.filter(
                name='Managers Group').exists()
            context['is_superuser'] = user.is_superuser
            context['is_manager_or_superuser'] = context['is_manager'] or context['is_superuser']
        else:
            context['is_customer'] = False
            context['is_manager'] = False
            context['is_superuser'] = False
            context['is_manager_or_superuser'] = False

        return context


class ManagerOrSuperuserRequiredMixin(UserPassesTestMixin):
    """Checks if user is manager or superuser."""
    permission_denied_message = "You must be a Manager or Superuser to access this page."
    login_url = 'login'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Managers Group').exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.login_url)
        return redirect('no-permissions')


# ======================
# AUTH VIEWS
# ======================
class MagicLinkLoginView(UserGroupContextMixin, View):
    def get(self, request, token):
        from .models import CustomerProfile
        try:
            profile = CustomerProfile.objects.get(
                magic_link_token=token,
                magic_link_expires__gt=now()
            )
            profile.magic_link_token = None
            profile.magic_link_expires = None
            profile.save()
            login(request, profile.user)
            return redirect('users')
        except CustomerProfile.DoesNotExist:
            messages.error(request, "Invalid or expired login link.")
            return redirect('login')


class CustomLoginView(UserGroupContextMixin, LoginView):
    form_class = LoginForm
    template_name = 'a_main/auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user

        if not user.is_authenticated:
            return super().get_success_url()

        if user.is_superuser:
            return reverse_lazy('admin:index')

        if user.is_staff:
            pass

        if user.groups.filter(name='Managers Group').exists():
            return reverse_lazy('managers')
        elif user.groups.filter(name='Customers Group').exists():
            return reverse_lazy('users')

        return reverse_lazy('index')


class FailedPermissionsView(UserGroupContextMixin, TemplateView):
    template_name = "a_main/auth/no_permissions.html"


# ======================
# CORE VIEWS
# ======================
class IndexView(UserGroupContextMixin, TemplateView):
    template_name = "a_main/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Cards are already passed into context via UserGroupContentMixin
        # But need to override to get images and descriptions.
        cards = Content.objects.filter(
            content_type='CARD',
            enabled=True
        ).order_by('-created_at').order_by('order').prefetch_related('media_files')

        card_data = []

        for card in cards:
            media_file = card.media_files.first()
            card_data.append({
                'id': card.id,
                'title': card.title,
                'description': card.description,
                'image_url': media_file.file.url if media_file else None,
            })
        context['cards'] = card_data
        # Still need to pass in banners and images
        banners = Content.objects.filter(
            content_type='BANNER',
            enabled=True
        ).order_by('-created_at').order_by('order').prefetch_related('media_files')

        banner_data = []

        for banner in banners:
            media_file = banner.media_files.first()
            banner_data.append({
                'id': banner.id,
                'title': banner.title,
                'message': banner.description,
                'image_url': media_file.file.url if media_file else None,
            })
        context['banners'] = banner_data
        return context


class ContactView(UserGroupContextMixin, CreateView):
    form_class = ContactForm
    template_name = "a_main/contact/contact.html"
    success_url = reverse_lazy('sent')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get the subject from URL parameters
        subject = self.request.GET.get('subject', None)
        if subject:
            kwargs['subject'] = subject
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['initial_subject'] = self.request.GET.get('subject', None)
        return context


class ContentView(UserGroupContextMixin, TemplateView):
    model = Content
    template_name = None
    context_type = None
    context_object_name = 'content_items'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            content_type=self.content_type,
            enabled=True
        ).order_by('order').prefetch_related('media_files')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        content_items = Content.objects.filter(
            content_type=self.context_type,
            enabled=True
        ).order_by('order').prefetch_related('media_files')

        # Flatten all content while tracking image positions
        image_position = 0
        content_elements = []

        for item in content_items:
            # Add images first with their alignment
            for media in item.media_files.all():
                if media.media_type == 'IMAGE':
                    alignment = 'left' if image_position % 2 == 0 else 'right'
                    content_elements.append({
                        'type': 'image',
                        'media': media,
                        'alignment': alignment
                    })
                    image_position += 1

            # Then add the text content
            if item.title or item.description:
                content_elements.append({
                    'type': 'text',
                    'item': item
                })

        context['content_elements'] = content_elements
        return context


class AboutView(ContentView):
    context_type = 'ABOUT'
    template_name = "a_main/about.html"


class FAQView(ContentView):
    context_type = 'FAQ'
    template_name = "a_main/faq.html"


class TermsView(ContentView):
    context_type = 'TERMS'
    template_name = "a_main/terms.html"


class PrivacyView(ContentView):
    context_type = 'PRIVACY'
    template_name = "a_main/privacy.html"


class SentView(UserGroupContextMixin, TemplateView):
    template_name = "a_main/contact/message_sent.html"


# ======================
# ROLE-SPECIFIC VIEWS
# ======================
class UsersView(UserGroupContextMixin, LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = "a_main/users/users.html"


class ManagersView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, TemplateView):
    template_name = "a_main/managers/managers.html"


# ======================
# CUSTOMERS VIEWS
# ======================
class CustomersListView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, ListView):
    model = CustomerProfile
    paginate_by = 20
    template_name = 'a_main/managers/customers/customers-list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add annotations for appointment counts or other relevant data
        return queryset.select_related('user').prefetch_related('appointments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Customer Management"
        # Add any additional context data needed for the template
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            profile_id = request.POST.get('profile_id')
            profile = get_object_or_404(CustomerProfile, id=profile_id)
            try:
                token = profile.generate_magic_link()
                login_url = request.build_absolute_uri(
                    reverse('magic-login', kwargs={'token': token})
                )

                # Prepare context for email templates
                context = {
                    'user': profile.user,
                    'login_url': login_url,
                    'instance': profile,
                }

                # Define email templates
                subject_template = "Your Magic Login Link"
                body_template = f'''
                Hello {profile.user.username},

                You requested a magic login link. Click the link below to access your account:

                {login_url}

                This link will expire in 24 hours.

                If you didn't request this, please ignore this email.
                '''

                html_template = f'''
                <p>Hello {profile.user.username},</p>
                <p>You requested a magic login link. Click the button below to access your account:</p>
                <p><a href="{login_url}" class="btn btn-primary">Login Now</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't request this, please ignore this email.</p>
                '''

                # Create a simple object to hold the email data
                class EmailInstance:
                    def __init__(self):
                        self.email = profile.user.email
                        self.subject = subject_template
                        self.message = body_template
                        self.html_message = html_template
                        self.id = profile.id

                email_instance = EmailInstance()

                # Add extra context that might be needed by the email templates
                extra_context = {
                    'html_message': html_template,
                    'login_url': login_url,
                }

                # Queue the email
                enqueue_email(email_instance)

                return JsonResponse({'success': True, 'message': 'Magic link sent successfully!'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
        return super().get(request, *args, **kwargs)


class CustomersUpdateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, UpdateView):
    model = CustomerProfile
    form_class = CustomerUpdateForm
    template_name = 'a_main/managers/customers/customers-update.html'
    success_url = reverse_lazy('customers-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context['title'] = f"Update Customer: {customer.user.get_full_name() or customer.user.username}"
        context['appointments'] = customer.appointments.all().order_by('-date')
        context['appointment_form'] = AppointmentForm(
            initial={'customer': customer}
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        # Handle appointment creation
        if 'create_appointment' in request.POST:
            appointment_form = AppointmentForm(request.POST)
            if appointment_form.is_valid():
                appointment = appointment_form.save(commit=False)
                # Use the view's object (CustomerProfile)
                appointment.customer = self.object
                appointment.save()
                messages.success(request, "Appointment added successfully!")
                return redirect('customers-update', pk=self.object.pk)
            else:
                # If form is invalid, add errors to context
                context = self.get_context_data()
                context['appointment_form'] = appointment_form
                return self.render_to_response(context)

        # Handle regular form submission
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


# ======================
# CUSTOMER APPOINTMENT VIEWS
# ======================

@require_POST
@login_required
def update_appointment_status(request, pk):
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value')

        # Validate input
        if field not in ['invoiced', 'paid']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid field'
            }, status=400)

        # Get appointment
        appointment = Appointment.objects.get(pk=pk)

        # Verify permission - user must be staff or superuser
        if not request.user.is_staff and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Permission denied'
            }, status=403)

        # Update the field
        setattr(appointment, field, value)
        appointment.save()

        return JsonResponse({
            'success': True,
            'message': f'Appointment {field} status updated successfully',
            'new_value': value
        })

    except Appointment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Appointment not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


class AppointmentUpdateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'a_main/managers/customers/appointment-update.html'

    def get_success_url(self):
        return reverse_lazy('customers-update', kwargs={'pk': self.object.customer.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update Appointment for {self.object.customer.user.username}"
        return context


class AppointmentDeleteView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, DeleteView):
    model = Appointment
    template_name = 'a_main/managers/customers/appointment-confirm-delete.html'

    def get_success_url(self):
        return reverse_lazy('customers-update', kwargs={'pk': self.object.customer.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Appointment for {self.object.customer.user.username}"
        return context


# ======================
# CONTENT CONTROL VIEWS
# ======================


class ContentListView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, ListView):
    model = Content
    template_name = 'a_main/managers/content/content-list.html'
    context_object_name = 'contents'
    paginate_by = 10

    def get_type_display_plural(self, content_type):
        # Map of content types to their plural display names
        plural_names = dict(Content.CONTENT_TYPES)
        return plural_names.get(content_type, content_type + 's')

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('media_files')
        # Get valid content types from model
        valid_types = [choice[0] for choice in Content.CONTENT_TYPES]

        # Filter by content_type if provided in URL
        content_type = self.request.GET.get('type', '').upper()
        if content_type:
            if content_type in valid_types:
                queryset = queryset.filter(content_type__iexact=content_type)
                self.normalized_type_name = self.get_type_display_plural(
                    content_type)
            else:
                # Add invalid type flag to context
                self.invalid_type = content_type

        return queryset.order_by('order', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add valid content types to context for template
        context['valid_content_types'] = [choice[0]
                                          for choice in Content.CONTENT_TYPES]

        # Add invalid type message if applicable
        if hasattr(self, 'invalid_type'):
            context['invalid_type'] = self.invalid_type

        # Add normalized type name if filtering
        if hasattr(self, 'normalized_type_name'):
            context['normalized_type_name'] = self.normalized_type_name
        else:
            context['normalized_type_name'] = "All "

        return context


class ContentDeleteView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, DeleteView):
    model = Content
    template_name = None  # Disable template rendering completely

    def get(self, request, *args, **kwargs):
        # Immediately process deletion if we got here (JS already confirmed)
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        content_type = self.request.GET.get('type', '').lower()
        url = reverse('content-list')
        return f"{url}?type={content_type}" if content_type else url


class ContentCreateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, CreateView):
    model = Content
    form_class = ContentCreateForm
    template_name = 'a_main/managers/content/content-create.html'

    def get_initial(self):
        initial = super().get_initial()
        content_type = self.request.GET.get('type', '').upper()
        if content_type in dict(Content.CONTENT_TYPES).keys():
            initial['content_type'] = content_type
        return initial

    def get_success_url(self):
        # Map content types to their respective URLs
        content_type = self.object.content_type.lower()
        return reverse('content-list') + f'?type={content_type}'

    def form_valid(self, form):
        response = super().form_valid(form)
        content_type = form.cleaned_data['content_type']

        # Handle media upload for types that need it
        if content_type in ['BANNER', 'CARD', 'ABOUT']:
            file = form.cleaned_data.get('file')
            if file:
                ContentMedia.objects.create(
                    content=self.object,
                    media_type='IMAGE',
                    file=file
                )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Create New Content"
        return context


class ContentUpdateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, UpdateView):
    model = Content
    form_class = ContentUpdateForm
    template_name = 'a_main/managers/content/content-update.html'

    def get_success_url(self):
        # Map content types to their respective URLs
        content_type = self.object.content_type.lower()
        return reverse('content-list') + f'?type={content_type}'

    def form_valid(self, form):
        response = super().form_valid(form)
        content_type = form.cleaned_data['content_type']

        # Handle media upload for types that need it
        if content_type in ['BANNER', 'CARD', 'ABOUT']:
            file = form.cleaned_data.get('file')
            if file:
                # Delete existing media if it exists
                self.object.media_files.all().delete()
                ContentMedia.objects.create(
                    content=self.object,
                    media_type='IMAGE',
                    file=file
                )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Update {self.object.get_content_type_display()}"

        # Add existing media for preview if it exists
        if self.object.media_files.exists():
            context['existing_media'] = self.object.media_files.first()

        return context
