FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app

COPY services/statistiques/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=app:app services/statistiques /app

USER app
EXPOSE 8000

CMD ["gunicorn", "config_statistiques.wsgi:application", "--bind", "0.0.0.0:8000"]
