FROM python:3.10-slim
WORKDIR /app
ARG MODEL_DIR=python/models
COPY nexpapi/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY python/src /app/src
COPY python/config.yaml /app/config.yaml
COPY nexpapi/app.py nexpapi/__init__.py /app/nexpapi/
COPY ${MODEL_DIR}/modelo_clasificador_300.pkl /app/models/modelo_clasificador_300.pkl
RUN useradd --create-home nexpapi
USER nexpapi
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "nexpapi.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
