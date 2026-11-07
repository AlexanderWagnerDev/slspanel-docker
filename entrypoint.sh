#!/bin/sh
set -eu

if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
    DJANGO_SECRET_KEY="$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
    export DJANGO_SECRET_KEY
fi

python3 manage.py migrate --noinput
python3 manage.py create_user
python3 manage.py initconfig
exec gunicorn --bind 0.0.0.0:8000 slspanel.wsgi:application
