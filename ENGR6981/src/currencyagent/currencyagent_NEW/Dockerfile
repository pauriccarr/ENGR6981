FROM python:3.12-slim

# No protoc step: the stubs are already in app/clients/ and are imported as app.clients.demo_pb2.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY test_fault_injection.py ./

ENV FAULT_MODE=NONE \
    RESULTS_DIR=/results \
    AGENT_NAME=currency
EXPOSE 8080 7000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
