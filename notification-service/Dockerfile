FROM python:3.12-slim AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
COPY requirements.txt requirements.lock.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.lock.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=3006
WORKDIR /app
COPY --from=dependencies /install /usr/local
RUN useradd --create-home --uid 10001 appuser
COPY manage.py pytest.ini ./
COPY config ./config
COPY common ./common
COPY email_delivery ./email_delivery
COPY tests ./tests
USER appuser
EXPOSE 3006
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 30 --error-logfile -"]
