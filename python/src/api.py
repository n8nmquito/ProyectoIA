"""Authenticated HTTP adapter for the existing 300-email classifier."""

import hmac
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.model import load_model, predict_ticket

ROOT = Path(__file__).resolve().parents[1]


class Ticket(BaseModel):
    """Accept only the two fields required for classification."""

    model_config = ConfigDict(extra="forbid", strict=True)
    titulo: str = Field(min_length=1, max_length=20000)
    cuerpo: str = Field(min_length=1, max_length=20000)


def create_app(model_path=None, api_key=None):
    """Build an application that loads the trusted model once at startup."""
    path = Path(model_path or ROOT / "models/modelo_clasificador_300.pkl")

    @asynccontextmanager
    async def lifespan(app):
        """Require authentication configuration and exactly 300 samples."""
        key = (
            api_key
            if api_key is not None
            else os.environ.get("CLASSIFIER_API_KEY", "")
        )
        if len(key) < 32:
            raise RuntimeError(
                "CLASSIFIER_API_KEY debe tener al menos 32 caracteres."
            )
        pipeline = load_model(path)
        if getattr(pipeline, "training_sample_count_", None) != 300:
            raise RuntimeError(
                "Se requiere el modelo entrenado con 300 correos."
            )
        app.state.pipeline = pipeline
        app.state.api_key = key
        yield

    app = FastAPI(title="Clasificador de soporte TI", lifespan=lifespan)

    def authenticate(x_api_key: str = Header(default="")):
        """Compare credentials without including them in error messages."""
        if not hmac.compare_digest(
            x_api_key.encode(), app.state.api_key.encode()
        ):
            raise HTTPException(
                status_code=401, detail="Clave de API inválida."
            )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        """Avoid echoing email contents in validation responses."""
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Envía solo titulo y cuerpo como textos no vacíos."
            },
        )

    @app.get("/health")
    def health():
        """Report readiness without exposing the model or its training data."""
        return {"status": "ok", "muestras_entrenamiento": 300}

    @app.post("/predict", dependencies=[Depends(authenticate)])
    def predict(ticket: Ticket):
        """Run the original preprocessing and pipeline without retraining."""
        try:
            result = predict_ticket(
                app.state.pipeline, ticket.titulo, ticket.cuerpo
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="Clasificador no disponible."
            ) from exc
        return {
            **result,
            "probabilidad": result["confianza"],
            "confianza_pct": round(result["confianza"] * 100, 2),
            "estado": "clasificado",
            "modelo_version": "modelo_clasificador_300",
            "muestras_entrenamiento": 300,
            "datos_entrenamiento": "correos_300.json",
            "modo": "categoria_final_ticket",
        }

    return app


app = create_app()
