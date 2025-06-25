FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY chunkserver.py ./

# No need for entrypoint.sh — we run directly
CMD ["python", "chunkserver.py"]
