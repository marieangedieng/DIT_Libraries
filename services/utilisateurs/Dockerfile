FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app

COPY services/utilisateurs/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=app:app services/utilisateurs /app

USER app
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn config_utilisateurs.wsgi:application --bind 0.0.0.0:8000"]
