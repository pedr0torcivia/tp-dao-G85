FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system django && adduser --system --ingroup django django

COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .
RUN chown -R django:django /app

USER django

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
