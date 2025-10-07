FROM python:3.11

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY services.py .
COPY ContextVariable_pb2.py .
COPY Event_pb2.py .

CMD ["opentelemetry-instrument", "uvicorn", "services:app", "--host", "0.0.0.0", "--port", "8000"]