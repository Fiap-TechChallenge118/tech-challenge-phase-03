"""Schemas Pydantic para a API de Triagem Médica."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    """Payload de entrada para o endpoint /predict."""

    texto: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Texto do laudo médico a ser classificado (máx. 5.000 caracteres).",
        examples=[
            "Paciente apresenta dor torácica intensa com irradiação para o braço esquerdo."  # noqa: E501
        ],
    )

    @field_validator("texto")
    @classmethod
    def texto_nao_pode_ser_branco(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "O campo 'texto' não pode ser vazio ou conter apenas espaços."
            )
        return v


class PredictResponse(BaseModel):
    """Payload de saída do endpoint /predict."""

    classe: Literal["normal", "atenção", "urgente"] = Field(
        ...,
        description="Classe de urgência predita pelo modelo.",
        examples=["urgente"],
    )
    confianca: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probabilidade associada à classe predita (0.0 – 1.0).",
        examples=[0.92],
    )
    tempo_ms: float = Field(
        ...,
        ge=0.0,
        description="Tempo total de inferência em milissegundos.",
        examples=[3.7],
    )
