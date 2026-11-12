FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
# Configure H4_DATABASE_URL and H4_TENANTS securely at runtime.
CMD ["uvicorn", "datarights.app:app", "--host", "0.0.0.0", "--port", "8000"]
