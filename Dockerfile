FROM python:3.11-slim
WORKDIR /app
COPY deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY deploy /app
EXPOSE 80
CMD ["uvicorn", "main_cosmosdb:app", "--host", "0.0.0.0", "--port", "80"]
