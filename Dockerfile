FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . .

# Environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# FIXED CMD: Point to the correct unified path
CMD ["python", "-u", "core/orchestrator/main.py"]
