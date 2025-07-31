from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import *

appname = "mainapp"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('faq/', FAQView.as_view(), name='faq'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('sent/', SentView.as_view(), name='sent'),
    path('denied/', FailedPermissionsView.as_view(), name='no-permissions'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('managers/', ManagersView.as_view(), name='managers'),
    path('users/', UsersView.as_view(), name='users'),
    path('customers/', CustomersListView.as_view(), name='customers-list'),
    path('customers/<int:pk>/update/',
         CustomersUpdateView.as_view(), name='customers-update'),
    path('appointments/<int:pk>/update/',
         AppointmentUpdateView.as_view(), name='appointment-update'),
    path('appointments/<int:pk>/delete/',
         AppointmentDeleteView.as_view(), name='appointment-delete'),
    path('banners/', BannerListView.as_view(), name='banners-list'),
    path('banners/create/', BannerCreateView.as_view(), name='banners-create'),
    path('banners/<int:pk>/update/',
         BannerUpdateView.as_view(), name='banners-update'),
    path('cards/', CardListView.as_view(), name='cards-list'),
    path('cards/create/', CardCreateView.as_view(), name='cards-create'),
    path('cards/<int:pk>/update/', CardUpdateView.as_view(), name='cards-update'),
    path('magic-login/<str:token>/',
         MagicLinkLoginView.as_view(), name='magic-login'),
]
