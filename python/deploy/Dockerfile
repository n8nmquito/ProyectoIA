FROM python:3.10-slim
WORKDIR /app
COPY deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src /app/src
COPY models/modelo_clasificador_300.pkl /app/models/modelo_clasificador_300.pkl
RUN useradd --create-home classifier
USER classifier
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
