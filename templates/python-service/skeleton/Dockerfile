FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /srv
RUN useradd --uid 10001 --no-create-home app
COPY app/ app/
USER 10001
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request,sys; sys.exit(urllib.request.urlopen('http://127.0.0.1:8080/healthz').status != 200)"
ENTRYPOINT ["python", "-m", "app.main"]
