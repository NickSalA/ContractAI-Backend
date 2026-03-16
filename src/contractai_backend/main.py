"""Archivo principal para la aplicación FastAPI de ContractAI-Backend."""

from fastapi import FastAPI
from uvicorn import run

app = FastAPI()

def main():
    """Función principal para ejecutar la aplicación FastAPI."""
    run("contractai_backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
