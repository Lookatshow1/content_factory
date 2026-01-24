FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY scheduler /app/scheduler
COPY alembic.ini /app/alembic.ini

CMD ["python", "-m", "scheduler.scheduler"]
