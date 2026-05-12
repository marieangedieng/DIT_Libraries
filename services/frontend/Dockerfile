FROM python:3.12-slim

RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY --chown=app:app services/frontend /app

USER app
EXPOSE 8000
CMD ["python", "-m", "http.server", "8000"]
