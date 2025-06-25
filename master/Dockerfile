FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY master.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["/bin/sh", "/app/entrypoint.sh"]
