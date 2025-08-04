from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import *

appname = "a_main"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('about/', AboutView.as_view(), name='about'),
    #     path('about/', AboutUpdateView.as_view(), name='about'),
    path('faq/', FAQView.as_view(), name='faq'),
    #     path('faq/', FAQUpdateView.as_view(), name='faq'),
    path('terms/', TermsView.as_view(), name='terms'),
    #     path('terms/', TermsUpdateView.as_view(), name='terms'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    #     path('privacy/', PrivacyUpdateView.as_view(), name='privacy'),
    path('sent/', SentView.as_view(), name='sent'),
    path('denied/', FailedPermissionsView.as_view(), name='no-permissions'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', CustomLoginView.as_view(), name='login'),
    # path('managers/', ManagersView.as_view(), name='managers'),
    path('users/', UsersView.as_view(), name='users'),
    path('customers/', CustomersListView.as_view(), name='customers-list'),
    path('customers/<int:pk>/update/',
         CustomersUpdateView.as_view(), name='customers-update'),
    path('appointments/<int:pk>/update/',
         AppointmentUpdateView.as_view(), name='appointment-update'),
    path('appointments/<int:pk>/delete/',
         AppointmentDeleteView.as_view(), name='appointment-delete'),

    # Universal Content Create View
    path('content/create/',
         ContentCreateView.as_view(), name='content-create'),
    path('content/list/', ContentListView.as_view(), name='content-list'),
    path('content/update/<int:pk>/',
         ContentUpdateView.as_view(), name='content-update'),
    path('content/delete/<int:pk>/',
         ContentDeleteView.as_view(), name='content-delete'),
    path('magic-login/<str:token>/',
         MagicLinkLoginView.as_view(), name='magic-login'),
]
