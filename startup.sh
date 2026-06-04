#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn --bind=0.0.0.0:8000 --workers=2 config.wsgi
