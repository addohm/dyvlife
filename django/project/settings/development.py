from pathlib import Path
import mimetypes
from os import sys
from decouple import config

print("Development environment settings loaded.")

mimetypes.add_type("text/css", ".css", True)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

PROJECT_NAME = config("PROJECT_NAME")

SECRET_KEY = config("SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = ['*']
INTERNAL_IPS = ['127.0.0.1', '0.0.0.0']
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=lambda v: [
                              s.strip() for s in v.split(',')])
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mainapp'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# EMAIL CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("EMAIL_HOST_USER")

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LOGIN\OUT REDIRECTION
LOGIN_URL = 'login'  # Where to redirect if the user is not authenticated
# Where to redirect after login, use 'protected' if you want to redirect to the break out the login view, see urls.py
LOGIN_REDIRECT_URL = 'protected'
LOGOUT_REDIRECT_URL = 'index'  # Where to redirect after logout

# STATICFILES_DIRS: This lists additional directories that Django's collectstatic tool
# should search for static files.
STATICFILES_DIRS = [
    f"{BASE_DIR}/_static",
]

# STATIC_ROOT: This is the absolute path to a directory where Django's collectstatic tool
# will gather any static files referenced in our templates. Once collected, these can then be uploaded as a group to wherever the files are to be hosted.
STATIC_ROOT = "./django/staticfiles"

# STATIC_URL: This is the base URL location from which static files will be served,
# for example on a CDN.
STATIC_URL = "static/"

# Restrict upload file size
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# MEDIA_ROOT: This is the absolute path to a directory where Django will gather any user uploaded images and files
# ex: /var/www/files/media
MEDIA_ROOT = "./django/mediafiles"

# MEDIA_URL: This is the base URL location from which media files will be served,
# for example on a CDN.
MEDIA_URL = "media/"

ENABLE_DEBUG_TOOLBAR = DEBUG and "test" not in sys.argv
if ENABLE_DEBUG_TOOLBAR:
    SECURE_CROSS_ORIGIN_OPENER_POLICY = None
    mimetypes.add_type("application/javascript", ".js", True)
    INSTALLED_APPS += [
        "debug_toolbar",
    ]
    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "ROOT_TAG_EXTRA_ATTRS": "data-turbo-permanent hx-preserve"}

# https://django-jazzmin.readthedocs.io/
JAZZMIN_SETTINGS = {
    "site_title": "your site Admin",
    "site_header": "your site",
    "site_brand": "your site",
    "site_logo": "/images/logos/divemonkey_dark_sm.png",
    "login_logo": '/images/logos/divemonkey_dark_sm.png',
    "login_logo_dark": '/images/logos/divemonkey_dark.png',
    "site_logo_classes": "",
    "site_icon": '/images/favicons/favicon-32x32.png',
    "welcome_sign": "Welcome to the site Admin",
    "copyright": "your site",
    "user_avatar": None,

    ############
    # Top Menu #
    ############

    "topmenu_links": [
        {"name": "View Site",  "url": "index"},
        {"name": "Support", "url": "", "new_window": True},
    ],

    #############
    # User Menu #
    #############

    "usermenu_links": [
        {"name": "Support", "url": "", "new_window": True},
    ],

    #############
    # Side Menu #
    #############

    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["mainapp", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #################
    # Related Modal #
    #################
    "related_modal_active": False,

    #############
    # UI Tweaks #
    #############
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": True,

    ###############
    # Change view #
    ###############
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": True,
    "footer_small_text": True,
    "body_small_text": True,
    "brand_small_text": True,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-navy",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "cerulean",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
