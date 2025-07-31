#!/bin/sh

# Fix permissions on mounted volumes
chown -R django:django /project/staticfiles
chown -R django:django /project/mediafiles
chmod -R 775 /project/staticfiles /project/mediafiles

# Run Django commands
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py createcachetable
python manage.py collectstatic --noinput

if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
    python manage.py createsuperuser --noinput
fi

exec python -m gunicorn ${PROJECT_NAME}.wsgi:application --workers 3 --bind 0.0.0.0:${APP_PORT}
