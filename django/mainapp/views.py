from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, ListView, View, DeleteView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.timezone import now
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse

from .models import Contact, Banner, Card, CustomerProfile, Appointment
from .forms import ContactForm, LoginForm, CustomerUpdateForm, AppointmentForm, BannerCreateForm, BannerUpdateForm, CardCreateForm, CardUpdateForm

from project.utils import enqueue_email

# ======================
# CUSTOM MIXINS
# ======================


class UserGroupContextMixin:
    """Adds user group information to context."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
class MagicLinkLoginView(View):
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


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'mainapp/auth/login.html'
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
    template_name = "mainapp/auth/no_permissions.html"


# ======================
# CORE VIEWS
# ======================
class IndexView(UserGroupContextMixin, TemplateView):
    template_name = "mainapp/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['banners'] = Banner.objects.all()
        context['cards'] = Card.objects.all()
        return context


class ContactView(UserGroupContextMixin, CreateView):
    form_class = ContactForm
    template_name = "mainapp/contact/contact.html"
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
        context['cards'] = Card.objects.all()
        # Pass the subject to template if needed
        context['initial_subject'] = self.request.GET.get('subject', None)
        return context


class AboutView(UserGroupContextMixin, TemplateView):
    template_name = "mainapp/about.html"


class FAQView(UserGroupContextMixin, TemplateView):
    template_name = "mainapp/faq.html"


class TermsView(UserGroupContextMixin, TemplateView):
    template_name = "mainapp/terms.html"


class PrivacyView(UserGroupContextMixin, TemplateView):
    template_name = "mainapp/privacy.html"


class SentView(UserGroupContextMixin, TemplateView):
    template_name = "mainapp/contact/message_sent.html"


# ======================
# ROLE-SPECIFIC VIEWS
# ======================
class UsersView(UserGroupContextMixin, LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = "mainapp/users/users.html"


class ManagersView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, TemplateView):
    template_name = "mainapp/managers/managers.html"


# ======================
# CUSTOMERS VIEWS
# ======================
class CustomersListView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, ListView):
    model = CustomerProfile
    paginate_by = 20
    template_name = 'mainapp/managers/customers/customers-list.html'
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
    template_name = 'mainapp/managers/customers/customers-update.html'
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

class AppointmentUpdateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'mainapp/managers/customers/appointment-update.html'

    def get_success_url(self):
        return reverse_lazy('customers-update', kwargs={'pk': self.object.customer.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Update Appointment for {self.object.customer.user.username}"
        return context


class AppointmentDeleteView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, DeleteView):
    model = Appointment
    template_name = 'mainapp/managers/customers/appointment-confirm-delete.html'

    def get_success_url(self):
        return reverse_lazy('customers-update', kwargs={'pk': self.object.customer.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Appointment for {self.object.customer.user.username}"
        return context


# ======================
# BANNER VIEWS
# ======================
class BannerListView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, ListView):
    model = Banner
    paginate_by = 20
    template_name = 'mainapp/managers/banners/banners-list.html'
    context_object_name = 'banners'


class BannerCreateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, CreateView):
    model = Banner
    form_class = BannerCreateForm  # Use your custom form
    template_name = 'mainapp/managers/banners/banners-create.html'
    success_url = reverse_lazy('banners-list')


class BannerUpdateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, UpdateView):
    model = Banner
    form_class = BannerUpdateForm  # Use your custom form
    template_name = 'mainapp/managers/banners/banners-update.html'
    success_url = reverse_lazy('banners-list')


# ======================
# CARD VIEWS
# ======================
class CardListView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, ListView):
    model = Card
    paginate_by = 20
    template_name = 'mainapp/managers/cards/cards-list.html'
    context_object_name = 'cards'


class CardCreateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, CreateView):
    model = Card
    form_class = CardCreateForm  # Use your custom form
    template_name = 'mainapp/managers/cards/cards-create.html'
    success_url = reverse_lazy('cards-list')


class CardUpdateView(ManagerOrSuperuserRequiredMixin, UserGroupContextMixin, UpdateView):
    model = Card
    form_class = CardUpdateForm  # Use your custom form
    template_name = 'mainapp/managers/cards/cards-update.html'
    success_url = reverse_lazy('cards-list')
