FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY db ./db
EXPOSE 8000
CMD ["sh", "-c", "python -m db.udf_load && uvicorn app.main:app_from_env --factory --host 0.0.0.0 --port 8000"]
