import logging
import mimetypes
import os
from collections import OrderedDict
from pathlib import Path

from django_regex.utils import RegexList

import aurora

from . import env

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, "static/js", "serviceworker.js")

mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)

PACKAGE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PACKAGE_DIR.parent
DEV_DIR = SRC_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
FERNET_KEY = env("FERNET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")
DEBUG_PROPAGATE_EXCEPTIONS = env("DEBUG_PROPAGATE_EXCEPTIONS")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
DJANGO_ADMIN_URL = env("DJANGO_ADMIN_URL")

# Application definition
SITE_ID = env("SITE_ID")
INSTALLED_APPS = [
    "daphne",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.forms",
    # -- dev --
    "debug_toolbar",
    # ---
    "reversion",  # https://github.com/etianen/django-reversion
    "reversion_compare",  # https://github.com/jedie/django-reversion-compare
    "django_filters",
    # ---
    # "aurora.admin.apps.AuroraAdminUIConfig",
    "smart_admin.apps.SmartLogsConfig",
    "smart_admin.apps.SmartTemplateConfig",
    # "smart_admin.apps.SmartAuthConfig",
    "smart_admin.apps.SmartConfig",
    "aurora.administration.apps.AuroraAdminConfig",
    "front_door.contrib",
    "hijack",
    "rest_framework",
    "rest_framework.authtoken",
    "aurora.api",
    "admin_ordering",
    "django_sysinfo",
    "admin_extra_buttons",
    "adminfilters",
    "adminactions",
    "mptt",
    "tinymce",
    "mdeditor",
    "constance",
    "constance.backends.database",
    "flags",
    "jsoneditor",
    "captcha",
    "social_django",
    "corsheaders",
    "simplemathcaptcha",
    "dbtemplates",
    "admin_sync",
    # ---
    "aurora.apps.Config",
    "aurora.flatpages.apps.Config",
    "aurora.i18n",
    "aurora.web",
    "aurora.security.apps.Config",
    "aurora.core",
    "aurora.registration",
    "aurora.counters",
]
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
MIDDLEWARE = [
    # "django.middleware.cache.UpdateCacheMiddleware",
    "aurora.web.middlewares.thread_local.ThreadLocalMiddleware",
    "aurora.web.middlewares.sentry.SentryMiddleware",
    "front_door.middleware.FrontDoorMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "aurora.web.middlewares.maintenance.MaintenanceMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "aurora.web.middlewares.i18n.I18NMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "aurora.web.middlewares.admin.AdminSiteMiddleware",
    # "aurora.web.middlewares.http2.HTTP2Middleware",
    "aurora.web.middlewares.minify.HtmlMinMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    # "django.middleware.cache.FetchFromCacheMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "hijack.middleware.HijackUserMiddleware",
]
X_FRAME_OPTIONS = "SAMEORIGIN"

ROOT_URLCONF = "aurora.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            PACKAGE_DIR / "administration/templates",
            PACKAGE_DIR / "admin/ui/templates",
            PACKAGE_DIR / "api/templates",
            PACKAGE_DIR / "registration/templates",
            PACKAGE_DIR / "flatpages/templates",
            PACKAGE_DIR / "core/templates",
            PACKAGE_DIR / "web/templates",
        ],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [
                "dbtemplates.loader.Loader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # 'builtins': [
            #     'http2.templatetags',
            # ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "constance.context_processors.config",
                "aurora.i18n.context_processors.itrans",
                "aurora.web.context_processors.smart",
                "django.template.context_processors.i18n",
                # Social auth context_processors
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "aurora.config.wsgi.application"
ASGI_APPLICATION = "aurora.config.asgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

main_conn = env.db("DATABASE_URL")
main_conn["CONN_MAX_AGE"] = 60
main_conn.update({"OPTIONS": {"options": "-c statement_timeout=10000"}})

ro_conn = main_conn.copy()
ro_conn.update(
    {
        "OPTIONS": {"options": "-c default_transaction_read_only=on"},
        "TEST": {
            "READ_ONLY": True,  # Do not manage this database during tests
        },
    }
)

DATABASES = {"default": main_conn, "read_only": ro_conn}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

try:
    if REDIS_CONNSTR := env("REDIS_CONNSTR"):
        os.environ["CACHE_DEFAULT"] = f"redisraw://{REDIS_CONNSTR},client_class=django_redis.client.DefaultClient"
except Exception as e:  # pragma: no cover
    logging.exception(e)

CACHES = {
    "default": env.cache_url("CACHE_DEFAULT"),
}

if DEBUG:  # pragma: no cover
    AUTH_PASSWORD_VALIDATORS = []
else:  # pragma: no cover
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = env("LANGUAGE_CODE")
LANGUAGE_COOKIE_NAME = "smart-register-language"

# As per http://www.lingoes.net/en/translator/langcode.htm
LANGUAGES = (
    ("en-us", "English | English"),
    ("ar-ae", " | عربي" + "Arabic"),
    ("cs-cz", "čeština | Czech"),
    ("de-de", "Deutsch | German"),
    ("es-es", "Español | Spanish"),
    ("fr-fr", "Français | French"),
    ("hu-hu", "Magyar | Hungarian"),
    ("it-it", "Italiano | Italian"),
    ("pl-pl", "Polskie | Polish"),
    ("pt-pt", "Português | Portuguese"),
    ("ro-ro", "Română | Romanian"),
    ("ru-ru", "Русский | Russian"),
    ("si-si", "සිංහල | Sinhala"),
    ("ta-ta", "தமிழ் | Tamil"),
    ("uk-ua", "український | Ukrainian"),
    ("hi-hi", "हिंदी | Hindi"),  # Hindi
)
LOCALE_PATHS = (str(PACKAGE_DIR / "LOCALE"),)

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
# SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN')
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
SESSION_COOKIE_NAME = env("SESSION_COOKIE_NAME")
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# Ensure STATIC_ROOT exists.
# os.makedirs(STATIC_ROOT, exist_ok=True)

# STATIC_URL = f"/static/{os.environ.get('VERSION', '')}/"
STATIC_URL = env("STATIC_URL")
STATIC_ROOT = env("STATIC_ROOT") + STATIC_URL  # simplify nginx config
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATICFILES_STORAGE = env("STATICFILES_STORAGE")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "web/static"),
    os.path.join(BASE_DIR, "flatpages/static"),
]

# -------- Added Settings
ADMINS = env("ADMINS")
AUTHENTICATION_BACKENDS = [
    "aurora.security.backend.AuroraAuthBackend",
    # "aurora.security.backend.RegistrationAuthBackend",
    # "aurora.security.backend.OrganizationAuthBackend",
    # "django.contrib.auth.backends.ModelBackend",
    "social_core.backends.azuread_tenant.AzureADTenantOAuth2",
] + env("AUTHENTICATION_BACKENDS")

CSRF_COOKIE_NAME = env("CSRF_COOKIE_NAME")
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env("USE_X_FORWARDED_HOST")

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_DEFAULT_FROM = env("EMAIL_FROM_EMAIL")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_TIMEOUT = env("EMAIL_TIMEOUT")
EMAIL_USE_SSL = env("EMAIL_USE_SSL")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")

# FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"
# LOGIN_URL = "/login"
# USER_LOGIN_URL = "/login"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {"verbose": {"format": "%(levelname)s %(asctime)s %(module)s: %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
    "loggers": {
        "selector_events": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "flags": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "front_door": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "front_door.middleware": {
            "handlers": ["console"],
            "level": "CRITICAL",
        },
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "aurora": {
            "handlers": ["console"],
            "level": env("LOG_LEVEL"),
        },
    },
}

# ------ Custom App

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",  # '2006-10-25'
    "%Y/%m/%d",  # '2006/10/25'
    "%m/%d/%Y",  # '10/25/2006'
    "%m/%d/%y",  # '10/25/06'
    "%b %d %Y",  # 'Oct 25 2006'
    "%b %d, %Y",  # 'Oct 25, 2006'
    "%d %b %Y",  # '25 Oct 2006'
    "%d %b, %Y",  # '25 Oct, 2006'
    "%B %d %Y",  # 'October 25 2006'
    "%B %d, %Y",  # 'October 25, 2006'
    "%d %B %Y",  # '25 October 2006'
    "%d %B, %Y",  # '25 October, 2006'
]

MAX_OBSERVED = 1
SENTRY_DSN = env("SENTRY_DSN")
SENTRY_PROJECT = env("SENTRY_PROJECT")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env("SENTRY_ENVIRONMENT"),
        integrations=[
            DjangoIntegration(transaction_style="url"),
            sentry_logging,
        ],
        release=aurora.VERSION,
        send_default_pii=True,
    )
CORS_ALLOWED_ORIGINS = [
    "https://excubo.unicef.io",
    "http://localhost:8000",
    "https://browser.sentry-cdn.com",
    "https://cdnjs.cloudflare.com",
    "https://login.microsoftonline.com",
] + env("CORS_ALLOWED_ORIGINS")

CONSTANCE_ADDITIONAL_FIELDS = {
    "html_minify_select": [
        "bitfield.forms.BitFormField",
        {"initial": 0, "required": False, "choices": (("html", "HTML"), ("line", "NEWLINE"), ("space", "SPACES"))},
    ],
}
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_CACHE_BACKEND = env("CONSTANCE_DATABASE_CACHE_BACKEND")
CONSTANCE_CONFIG = OrderedDict(
    {
        "CACHE_FORMS": (False, "", bool),
        "CACHE_VERSION": (1, "", int),
        "HOME_PAGE_REGISTRATIONS": ("", "", str),
        "SMART_ADMIN_BOOKMARKS": (
            "",
            "",
            str,
        ),
        "LOGIN_LOCAL": (True, "Enable local accounts login", bool),
        "LOGIN_SSO": (True, "Enable SSO logon", bool),
        "ADMIN_SYNC_REMOTE_SERVER": ("", "production server url", str),
        "ADMIN_SYNC_REMOTE_ADMIN_URL": ("/admin/", "", str),
        "ADMIN_SYNC_LOCAL_ADMIN_URL": ("/admin/", "", str),
        "ADMIN_SYNC_USE_REVERSION": (False, "", bool),
        "LOG_POST_ERRORS": (False, "", bool),
        "MINIFY_RESPONSE": (0, "select yes or no", "html_minify_select"),
        "MINIFY_IGNORE_PATH": (r"", "regex for ignored path", str),
        "BASE_TEMPLATE": ("base_lean.html", "Default base template", str),
        "HOME_TEMPLATE": ("home.html", "Default home.html", str),
        "QRCODE": (True, "Enable QRCode generation", bool),
        "SHOW_REGISTER_ANOTHER": (True, "Enable QRCode generation", bool),
        "MAINTENANCE_MODE": (False, "set maintenance mode On/Off", bool),
        "WAF_REGISTRATION_ALLOWED_HOSTNAMES": (".*", "public website hostname (regex)", str),
        "WAF_ADMIN_ALLOWED_HOSTNAMES": ("", "admin website hostname (regex)", str),
    }
)

SMART_ADMIN_SECTIONS = {
    "Registration": ["registration", "dbtemplates", "flatpages"],
    "Security": ["social_auth", "security"],
    "Form Builder": ["core"],
    "Organization": ["core.Organization", "core.Project"],
    "Configuration": ["constance", "flags"],
    "i18N": [
        "i18n",
    ],
    "Other": [],
    "_hidden_": [],
}
SMART_ADMIN_TITLE = "="
SMART_ADMIN_HEADER = env("DJANGO_ADMIN_TITLE")
SMART_ADMIN_BOOKMARKS = "aurora.core.utils.get_bookmarks"

SMART_ADMIN_PROFILE_LINK = True

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

RATELIMIT = {
    "PERIODS": {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 60 * 60,
        "M": 30 * 24 * 60 * 60,
        "y": 365 * 24 * 60 * 60,
    }
}

AA_PERMISSION_HANDLER = 3  # AA_PERMISSION_CREATE_USE_APPCONFIG


def masker(key, value, config, request):
    from django_sysinfo.utils import cleanse_setting

    from aurora.core.utils import is_root

    if is_root(request):
        return value
    return cleanse_setting(key, value, config, request)


SYSINFO = {
    "host": True,
    "os": True,
    "python": True,
    "modules": True,
    "masker": "aurora.config.settings.masker",
    "masked_environment": "API|TOKEN|KEY|SECRET|PASS|SIGNATURE|AUTH|_ID|SID|DATABASE_URL",
    # "project": {
    #     "mail": False,
    #     "installed_apps": False,
    #     "databases": False,
    #     "MEDIA_ROOT": False,
    #     "STATIC_ROOT": False,
    #     "CACHES": False
    # },
    # "checks": None,
}

FLAGS_STATE_LOGGING = DEBUG

FLAGS = {
    "DEVELOP_DEVELOPER": [],
    "DEVELOP_DEBUG_TOOLBAR": [],
    "SENTRY_JAVASCRIPT": [],
    "I18N_COLLECT_MESSAGES": [],
}

JSON_EDITOR_JS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/8.6.4/jsoneditor.js"
JSON_EDITOR_CSS = "https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/8.6.4/jsoneditor.css"
JSON_EDITOR_INIT_JS = "django-jsoneditor/jsoneditor-init.min.js"
JSON_EDITOR_ACE_OPTIONS_JS = "django-jsoneditor/ace_options.min.js"

# CAPTCHA_IMAGE_SIZE = 300,200
CAPTCHA_FONT_SIZE = 40
CAPTCHA_CHALLENGE_FUNCT = "captcha.helpers.random_char_challenge"
CAPTCHA_TEST_MODE = env("CAPTCHA_TEST_MODE")
CAPTCHA_GET_FROM_POOL = True


# CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'


# DEBUG TOOLBAR
def show_ddt(request):  # pragma: no-cover
    from flags.state import flag_enabled

    if request.path in RegexList(("/tpl/.*", "/api/.*", "/dal/.*")):  # pragma: no cache
        return False
    return flag_enabled("DEVELOP_DEBUG_TOOLBAR", request=request)


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_ddt,
    "JQUERY_URL": "",
    "INSERT_BEFORE": "</head>",
    "SHOW_TEMPLATE_CONTEXT": True,
}
INTERNAL_IPS = env.list("INTERNAL_IPS")
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    # "debug_toolbar.panels.versions.VersionsPanel",
    "aurora.ddt_panels.StatePanel",
    "aurora.ddt_panels.MigrationPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "flags.panels.FlagsPanel",
    "flags.panels.FlagChecksPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]

ROOT_TOKEN = env("ROOT_TOKEN")
CSRF_FAILURE_VIEW = "aurora.web.views.site.error_csrf"

# WARNING: Do NOT touch this line before it will reach out production
AUTH_USER_MODEL = "auth.User"
# AUTH_USER_MODEL = "security.AuroraUser"

# Graph API
AZURE_GRAPH_API_BASE_URL = "https://graph.microsoft.com"
AZURE_GRAPH_API_VERSION = "v1.0"
AZURE_TOKEN_URL = "https://login.microsoftonline.com/unicef.org/oauth2/token"

# Social Auth settings.
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = env.str("AZURE_CLIENT_SECRET")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = env("AZURE_TENANT_ID")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = env.str("AZURE_CLIENT_KEY")
SOCIAL_AUTH_RESOURCE = "https://graph.microsoft.com/"
# SOCIAL_AUTH_POLICY = env("AZURE_POLICY_NAME")
# SOCIAL_AUTH_AUTHORITY_HOST = env("AZURE_AUTHORITY_HOST")
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = [
    "username",
    "first_name",
    "last_name",
    "email",
]

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_PIPELINE = (
    "aurora.core.authentication.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "aurora.core.authentication.require_email",
    "social_core.pipeline.social_auth.associate_by_email",
    "aurora.core.authentication.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "aurora.core.authentication.user_details",
    "aurora.core.authentication.redir_to_form",
)
SOCIAL_AUTH_AZUREAD_B2C_OAUTH2_USER_FIELDS = [
    "email",
    "fullname",
]

SOCIAL_AUTH_AZUREAD_B2C_OAUTH2_SCOPE = [
    "openid",
    "email",
    "profile",
]

SOCIAL_AUTH_SANITIZE_REDIRECTS = True
SOCIAL_AUTH_JWT_LEEWAY = env.int("JWT_LEEWAY", 0)

# fix admin name
LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/logged-in/"

# allow upload big file
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 2  # 2M
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE

HTTP2_PRELOAD_HEADERS = True
HTTP2_PRESEND_CACHED_HEADERS = True
HTTP2_SERVER_PUSH = False
# CSP
SOURCES = (
    "self",
    "inline",
    "unsafe-inline",
    "http://localhost:8000",
    "https://unpkg.com",
    "https://browser.sentry-cdn.com",
    "https://cdnjs.cloudflare.com",
    "data",
    "unsafe-inline",
)
# MIDDLEWARE += ["csp.middleware.CSPMiddleware", ]
CSP_DEFAULT_SRC = SOURCES
# CSP_SCRIPT_SRC = ("self",)
CSP_STYLE_SRC = (
    "self",
    "unsafe-inline",
    "https://unpkg.com",
    "http://localhost:8000",
    "https://cdnjs.cloudflare.com",
)
# CSP_OBJECT_SRC = ("self",)
# CSP_BASE_URI = ("self", "http://localhost:8000",)
# CSP_CONNECT_SRC = ("self",)
# CSP_FONT_SRC = ("self",)
# CSP_FRAME_SRC = ("self",)
# CSP_IMG_SRC = ("self", "data")
# CSP_MANIFEST_SRC = ("self",)
# CSP_MEDIA_SRC = ("self",)
# CSP_REPORT_URI = ("https://624948b721ea44ac2a6b4de4.endpoint.csper.io/?v=0;",)
# CSP_WORKER_SRC = ("self",)
"""default-src 'self';
script-src 'report-sample' 'self';
style-src 'report-sample' 'self';
object-src 'none';
base-uri 'self';
connect-src 'self';
font-src 'self';
frame-src 'self';
img-src 'self';
manifest-src 'self';
media-src 'self';
report-uri https://624948b721ea44ac2a6b4de4.endpoint.csper.io/?v=0;
worker-src 'none';
"""

# CSP_INCLUDE_NONCE_IN = env("CSP_INCLUDE_NONCE_IN")
# CSP_REPORT_ONLY = env("CSP_REPORT_ONLY")
# CSP_DEFAULT_SRC = env("CSP_DEFAULT_SRC")
# CSP_SCRIPT_SRC = env("CSP_SCRIPT_SRC")

# Add reversion models to admin interface:
ADD_REVERSION_ADMIN = True
# optional settings:
REVERSION_COMPARE_FOREIGN_OBJECTS_AS_ID = False
REVERSION_COMPARE_IGNORE_NOT_REGISTERED = False

ADMIN_SYNC_CONFIG = env("ADMIN_SYNC_CONFIG")
ADMIN_SYNC_RESPONSE_HEADER = None
# these are actually used only in local development
ADMIN_SYNC_REMOTE_SERVER = env("ADMIN_SYNC_REMOTE_SERVER", default="")
ADMIN_SYNC_REMOTE_ADMIN_URL = env("ADMIN_SYNC_REMOTE_ADMIN_URL", default="")
ADMIN_SYNC_LOCAL_ADMIN_URL = env("ADMIN_SYNC_LOCAL_ADMIN_URL", default="")
# ADMIN_SYNC_USE_REVERSION=

SILENCED_SYSTEM_CHECKS = [
    "debug_toolbar.W006",
    "urls.W005",
    "admin_extra_buttons.PERM",
    "security.W008",  # SECURE_SSL_REDIRECT
    "security.W019",  # XFrameOptionsMiddleware
]

DBTEMPLATES_USE_REVERSION = True
DBTEMPLATES_USE_CODEMIRROR = True

CONCURRENCY_ENABLED = False

STRATEGY_CLASSLOADER = "aurora.core.registry.classloader"
MIGRATION_LOCK_KEY = env("MIGRATION_LOCK_KEY")

# for offline forms
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 10
SESSION_COOKIE_HTTPONLY = False

HIJACK_PERMISSION_CHECK = "aurora.administration.hijack.can_impersonate"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("CHANNEL_LAYER")],
        },
    },
}

MDEDITOR_CONFIGS = {
    "default": {
        "width": "100% ",  # Custom edit box width
        "height": 200,  # Custom edit box height
        "toolbar": [
            "undo",
            "redo",
            "|",
            "bold",
            "del",
            "italic",
            "quote",
            "ucwords",
            "uppercase",
            "lowercase",
            "|",
            "h1",
            "h2",
            "h3",
            "h5",
            "h6",
            "|",
            "list-ul",
            "list-ol",
            "hr",
            "|",
            "link",
            "reference-link",
            "image",
            "code",
            "preformatted-text",
            "code-block",
            "table",
            "datetime",
            "emoji",
            "html-entities",
            "pagebreak",
            "goto-line",
            "|",
            "help",
            "info",
            "||",
            "preview",
            "watch",
            "fullscreen",
        ],  # custom edit box toolbar
        # image upload format type
        # 'upload_image_formats': ["jpg", "jpeg", "gif", "png", "bmp", "webp", "svg"],
        # 'image_folder': 'editor',  # image save the folder name
        "theme": "default",  # edit box theme, dark / default
        "preview_theme": "default",  # Preview area theme, dark / default
        "editor_theme": "default",  # edit area theme, pastel-on-dark / default
        "toolbar_autofixed": False,  # Whether the toolbar capitals
        "search_replace": True,  # Whether to open the search for replacement
        "emoji": True,  # whether to open the expression function
        "tex": True,  # whether to open the tex chart function
        "flow_chart": True,  # whether to open the flow chart function
        "sequence": True,  # Whether to open the sequence diagram function
        "watch": True,  # Live preview
        "lineWrapping": True,  # lineWrapping
        "lineNumbers": True,  # lineNumbers
        "language": "en",  # zh / en / es
    }
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework_datatables.renderers.DatatablesRenderer",
    ),
    "PAGE_SIZE": 30,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissions",
    ],
}

FRONT_DOOR_CONFIG = "front_door.conf.DjangoConstance"
FRONT_DOOR_ENABLED = env("FRONT_DOOR_ENABLED")
FRONT_DOOR_ALLOWED_PATHS = env("FRONT_DOOR_ALLOWED_PATHS")
FRONT_DOOR_TOKEN = env("FRONT_DOOR_TOKEN")
FRONT_DOOR_HEADER = "x-aurora"
FRONT_DOOR_COOKIE_NAME = "x-aurora"
FRONT_DOOR_COOKIE_PATTERN = ".*"
# FRONT_DOOR_ERROR_CODE = 404
# FRONT_DOOR_REDIR_URL = "https://www.sosbob.com/"
FRONT_DOOR_LOG_LEVEL = env("FRONT_DOOR_LOG_LEVEL")  # LOG_RULE_FAIL
FRONT_DOOR_RULES = [
    # "front_door.rules.internal_ip",  # grant access to settings.INTERNAL_IPS
    # "front_door.rules.forbidden_path",  # DENY access to FORBIDDEN_PATHS
    "front_door.rules.allowed_path",  # grant access to ALLOWED_PATHS
    "front_door.rules.allowed_ip",  # grant access to ALLOWED_IPS
    "front_door.rules.special_header",  # grant access if request has Header[HEADER] == TOKEN
    # "front_door.rules.has_header",  # grant access if request has HEADER
    "front_door.rules.cookie_value",  # grant access if request.COOKIES[COOKIE_NAME]
    # "front_door.rules.cookie_exists",  # grant access ir COOKIE_NAME in request.COOKIES
]

TRANSLATOR_SERVICE = env("TRANSLATOR_SERVICE")
AZURE_TRANSLATOR_KEY = env("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_LOCATION = env("AZURE_TRANSLATOR_LOCATION")

AZURE_CLIENT_ID = env("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = env("AZURE_CLIENT_SECRET")
