import uuid
from urllib.parse import urlencode, urlparse

from environ import Env

from aurora.core.flags import parse_bool


def parse_bookmarks(value):
    return "".join(value.split(r"\n"))


def parse_emails(value):
    admins = value.split(",")
    v = [(a.split("@")[0].strip(), a.strip()) for a in admins]
    return v


MANDATORY = {
    "CACHE_DEFAULT": (str, "locmemcache://"),
    "CHANNEL_LAYER": (str, "locmemcache://"),
    "DATABASE_URL": (str, "psql://postgres:@postgres:5432/aurora"),
    "DJANGO_ADMIN_URL": (str, f"{uuid.uuid4().hex}/"),
    "EMAIL_FROM_EMAIL": (str, ""),
    "EMAIL_HOST": (str, ""),
    "EMAIL_HOST_PASSWORD": (str, ""),
    "EMAIL_HOST_USER": (str, ""),
    "EMAIL_SUBJECT_PREFIX": (str, "[Aurora]"),
    "FERNET_KEY": (str, uuid.uuid4().hex),
    "MEDIA_ROOT": (str, "/tmp/media/"),
    "STATIC_ROOT": (str, "/tmp/static/"),
}

OPTIONS = {
    "ADMINS": (parse_emails, ""),
    "ADMIN_SYNC_CONFIG": (str, "admin_sync.conf.DjangoConstance"),
    "ALLOWED_HOSTS": (list, ["*"]),
    "AUTHENTICATION_BACKENDS": (list, []),
    "AZURE_AUTHORITY_HOST": (str, ""),
    "AZURE_CLIENT_ID": (str, ""),
    "AZURE_CLIENT_KEY": (str, ""),
    "AZURE_CLIENT_SECRET": (str, ""),
    "AZURE_POLICY_NAME": (str, ""),
    "AZURE_TENANT_ID": (str, ""),
    "AZURE_TENANT_KEY": (str, ""),
    "CAPTCHA_TEST_MODE": (bool, "false"),
    "TRANSLATOR_SERVICE": (str, ""),
    "AZURE_TRANSLATOR_KEY": (str, ""),
    "AZURE_TRANSLATOR_LOCATION": (str, ""),
    "CONSTANCE_DATABASE_CACHE_BACKEND": (str, ""),
    "CORS_ALLOWED_ORIGINS": (list, []),
    "CSP_REPORT_ONLY": (bool, True),
    "CSRF_COOKIE_NAME": (str, "aurora"),
    "CSRF_COOKIE_SECURE": (bool, True),
    "DEBUG": (bool, False),
    "DEBUG_PROPAGATE_EXCEPTIONS": (bool, False),
    "DJANGO_ADMIN_TITLE": (str, "Aurora"),
    "EMAIL_BACKEND": (str, "django.core.mail.backends.smtp.EmailBackend"),
    # "EMAIL_FROM_EMAIL": (str, ""),
    # "EMAIL_HOST": (str, ""),
    # "EMAIL_HOST_PASSWORD": (str, ""),
    # "EMAIL_HOST_USER": (str, ""),
    "EMAIL_PORT": (int, 587),
    # "EMAIL_SUBJECT_PREFIX": (str, "[Aurora]"),
    "EMAIL_TIMEOUT": (int, 30),
    "EMAIL_USE_LOCALTIME": (bool, False),
    "EMAIL_USE_SSL": (bool, False),
    "EMAIL_USE_TLS": (bool, True),
    "FRONT_DOOR_ENABLED": (bool, False),
    "FRONT_DOOR_ALLOWED_PATHS": (str, ".*"),
    "FRONT_DOOR_TOKEN": (str, uuid.uuid4()),
    "FRONT_DOOR_LOG_LEVEL": (str, "ERROR"),
    # "FERNET_KEY": (str, "2jQklRvSAZUdsVOKH-521Wbf_p5t2nTDA0LgD9sgim4="),
    "INTERNAL_IPS": (list, ["127.0.0.1", "localhost"]),
    "LANGUAGE_CODE": (str, "en-us"),
    "LOG_LEVEL": (str, "ERROR"),
    "MIGRATION_LOCK_KEY": (str, "django-migrations"),
    "PRODUCTION_SERVER": (str, ""),
    "PRODUCTION_TOKEN": (str, ""),
    "REDIS_CONNSTR": (str, ""),
    "ROOT_TOKEN": (str, uuid.uuid4().hex),
    "SECRET_KEY": (str, ""),
    "SECURE_HSTS_SECONDS": (int, 0),
    "SENTRY_DSN": (str, ""),
    "SENTRY_ENVIRONMENT": (str, "production"),
    "SENTRY_PROJECT": (str, ""),
    "SENTRY_SECURITY_TOKEN": (str, ""),
    "SENTRY_SECURITY_TOKEN_HEADER": (str, "X-Sentry-Token"),
    "SESSION_COOKIE_DOMAIN": (str, "localhost"),
    "SESSION_COOKIE_NAME": (str, "aurora_id"),
    "SESSION_COOKIE_SECURE": (bool, True),
    "SESSION_COOKIE_HTTPONLY": (bool, True),
    "SMART_ADMIN_BOOKMARKS": (parse_bookmarks, ""),
    "STATICFILES_STORAGE": (str, "aurora.web.storage.ForgivingManifestStaticFilesStorage"),
    "USE_HTTPS": (bool, False),
    "USE_X_FORWARDED_HOST": (bool, True),
    "SITE_ID": (int, 1),
    # "CSP_DEFAULT_SRC": (list, ),
    # "CSP_SCRIPT_SRC": (str, None),
    # "FERNET_KEY": (str, "Nl_puP2z0-OKVNKMtPXx4jEI-ox7sKLM7CgnGT-yAug="),
    # "STATICFILES_STORAGE": (str, "django.contrib.staticfiles.storage.StaticFilesStorage"),
    # "STATIC_ROOT": (str, "/tmp/static/"),
    # Sentry - see CONTRIBUTING.md
}


class SmartEnv(Env):
    def cache_url(self, var=Env.DEFAULT_CACHE_ENV, default=Env.NOTSET, backend=None):
        v = self.str(var, default)
        if v.startswith("redisraw://"):
            scheme, string = v.split("redisraw://")
            host, *options = string.split(",")
            config = dict([v.split("=", 1) for v in options])
            if parse_bool(config.get("ssl", "false")):
                scheme = "rediss"
            else:
                scheme = "redis"
            auth = ""
            credentials = [config.pop("user", ""), config.pop("password", "")]
            if credentials[0] or credentials[1]:
                auth = f"{':'.join(credentials)}@"
            new_url = f"{scheme}://{auth}{host}/?{urlencode(config)}"
            return self.cache_url_config(urlparse(new_url), backend=backend)
        return super().cache_url(var, default, backend)


env = SmartEnv(**MANDATORY, **OPTIONS)
