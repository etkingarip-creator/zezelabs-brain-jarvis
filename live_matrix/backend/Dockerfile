FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY telemetry_server.py .
CMD ["python", "-u", "telemetry_server.py"]
