FROM python:3.11-slim-bullseye as base
ARG BUILD_DATE
ARG VERSION

WORKDIR /code/

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                build-essential \
                locales \
                nginx \
                locales-all \
                gettext \
                libjpeg-dev \
                zlib1g-dev \
                git-core \
                postgresql-client \
                libpq-dev \
                python3-psycopg2 \
                python3-gdal \
                redis-server \
                gdal-bin \
                curl \
    && locale-gen --no-purge uk_UA.UTF-8 \
    && apt-get clean

ENV PATH="${PATH}:/root/.local/bin:/code/__pypackages__/3.11/bin" \
    ADMINS="" \
    BUILD_DATE=${BUILD_DATE} \
    CACHE_DEFAULT="redis://127.0.0.1/0" \
    CONSTANCE_DATABASE_CACHE_BACKEND="" \
    DATABASE_URL="" \
    DEFAULT_ORGANIZATION="UNICEF"\
    DJANGO_SETTINGS_MODULE="aurora.config.settings" \
    IPSTACK_KEY="" \
    LOG_LEVEL="ERROR" \
    MAINTENANCE_MODE="off" \
    NGINX_CACHE_DIR="/data/nginx/cache" \
    NGINX_MAX_BODY_SIZE=30M \
    REDIS_LOGLEVEL="warning" \
    REDIS_MAXMEMORY="100Mb" \
    REDIS_MAXMEMORY_POLICY="volatile-ttl" \
    PYTHONPATH="/code/src/:/code/__pypackages__/3.11/lib" \
    PYTHONUNBUFFERED=1 \
    SECRET_KEY="secret-key-just-for-build" \
    SENTRY_DSN="" \
    STATIC_ROOT="/var/static" \
    STATIC_URL="/static/" \
    UWSGI_PROCESSES=4 \
    VERSION=${VERSION} \
    POETRY_VERSION=${POETRY_VERSION}

RUN pip install pdm==2.15.1
ADD pyproject.toml pdm.toml pdm.lock ./
RUN sed -i 's/use_venv = true/use_venv = false/' pdm.toml
RUN pdm sync --prod --no-editable --no-self

RUN mkdir -p /var/nginx/system

ADD . ./
ADD ./docker/conf/nginx/* /var/nginx/
ADD ./docker/conf/* /conf/
ADD ./docker/bin/* /usr/local/bin/

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

FROM base as dev
RUN pdm sync --dev

FROM base as dist
