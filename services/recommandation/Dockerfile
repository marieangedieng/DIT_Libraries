FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/workspace/scripts"
ENV WORKSPACE_DIR="/workspace"

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY services/recommandation/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app services/recommandation /app
COPY --chown=app:app scripts /workspace/scripts
COPY --chown=app:app data /workspace/data
COPY --chown=app:app models /workspace/models
COPY --chown=app:app metrics /workspace/metrics

USER app
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
