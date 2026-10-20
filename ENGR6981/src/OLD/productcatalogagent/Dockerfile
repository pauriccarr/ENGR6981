FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv:/srv/app

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY test_fault_injection.py ./

ENV FAULT_MODE=NONE
EXPOSE 8080 3550

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]


