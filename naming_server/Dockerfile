FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY naming_server/naming_server.py ./
CMD ["python", "naming_server.py"]
