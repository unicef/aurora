# envs to set before use this script
.ONESHELL:

DEVELOP?=0
DOCKER_PASS?=
DOCKER_USER?=
VERSION?=0.1.0
BASE?=$(shell echo "${VERSION}" | sed "s/\([0-9]*\)\.\([0-9]*\)\.\(.*\)/\1.\2/g" )
PUSH_BASE?=0
DEVELOP?=1
BUILD_DATE:="$(shell date +"%Y-%m-%d %H:%M")"
# below vars are used internally
POETRY_VERSION=1.2.2
BUILD_OPTIONS?=--squash
CMD?=run
WORKER?='??'
CONTAINER_NAME?=flex-form-cnt
LAZO?=$(shell which lazo)

DOCKER_REGISTRY=ghcr.io
DOCKER_IMAGE_NAME=saxix/aurora
DOCKER_IMAGE=${DOCKER_IMAGE_NAME}:${VERSION}
DOCKER_TARGET=${DOCKER_REGISTRY}/${DOCKER_IMAGE}
DOCKERFILE?=Dockerfile

RUN_OPTIONS?=
PIPENV_ARGS?=

ISDIRTY=$(shell git status --porcelain)
IMAGE_EXISTS=$(shell docker ps -a | grep "${DOCKER_REGISTRY}/${DOCKER_IMAGE}")

.PHONY: help runlocal
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

check:
	@[ -z "`git status --porcelain`" ] || ( git status ; echo "Uncommited changes"; exit 1 )
	export IMAGE_EXISTS=`curl --silent --header "PRIVATE-TOKEN: ${GITLAB_API_TOKEN}" https://gitlab.com/api/v4/projects/22122245/registry/repositories/1473455/tags/${VERSION} | jq '.location'`
	@[ "${IMAGE_EXISTS}" != null ] || ( echo "Docker image '${DOCKER_TARGET}' already exists"; exit 1 )
	@[ -n "`git tag -l ${VERSION}`" ] || git tag -m "v${VERSION}"  ${VERSION}

.build:
	cd .. && docker build \
			--build-arg VERSION=${VERSION} \
			--build-arg BUILD_DATE=${BUILD_DATE} \
			-t ${DOCKER_REGISTRY}/${DOCKER_IMAGE} \
			-f docker/${DOCKERFILE} .
	docker tag ${DOCKER_REGISTRY}/${DOCKER_IMAGE} ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:latest
	docker images | grep "${DOCKER_IMAGE_NAME}" | grep ${VERSION}

build: check .build

dev:
	cd .. && docker build -t flex-dev -f docker/Dockerfile.dev .
	DOCKER_IMAGE=flex-dev \
	CMD='/bin/bash' \
	RUN_OPTIONS="-it -v ${PWD}/conf/:/conf/ -v ${PWD}/../:/code/" \
	$(MAKE) .run

.push:
	git push

.run:
	mkdir -p ../${VOLUME}
	cd .. && docker run \
	 		--rm \
	 		--name=${CONTAINER_NAME} \
			-p 8000:80 \
			-e AUTHENTICATION_BACKENDS=\
			-e ADMIN_EMAIL="${ADMIN_EMAIL}" \
			-e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
			-e DJANGO_ADMIN_URL=admin/ \
			-e ADMINS="" \
			-e MAINTENANCE_MODE="off" \
			-e LANGUAGE_CODE="uk-ua" \
			-e ALLOWED_HOSTS="*" \
			-e DATABASE_URL="${DATABASE_URL}" \
			-e DEBUG="0" \
			-e DJANGO_SETTINGS_MODULE="aurora.config.settings" \
			-e SENTRY_DSN="${SENTRY_DSN}" \
			-e REDIS_CONNSTR="192.168.66.66" \
			-e VERSION="${VERSION}" \
			-v ${PWD}/conf/:/conf/ \
			-v ${PWD}/bin/entrypoint.sh:/usr/local/bin/entrypoint.sh \
			-v ${PWD}/conf/nginx:/var/nginx/ \
			${RUN_OPTIONS} \
			${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:latest \
			${CMD}

# 			-e STATICFILES_STORAGE="django.contrib.staticfiles.storage.ManifestStaticFilesStorage"\
#docker push registry.gitlab.com/bitcaster/bitcaster

release: .docker-login ## release version $VERSION
	docker tag ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${VERSION} ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:latest
	docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:latest
	docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${VERSION}

run:  ## run image locally
	CMD="" $(MAKE) .run

check:  ## test docker image
	CMD='sh -c "whoami && django-admin collectstatic --no-input -v 3 && django-admin check --deploy"' \
	$(MAKE) .run

shell:  ## run docker and spawn a shell
	DOCKER_IMAGE=${DOCKER_IMAGE_NAME}:latest RUN_OPTIONS=-it CMD='/bin/bash' $(MAKE) .run
