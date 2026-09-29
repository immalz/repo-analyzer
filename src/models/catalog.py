from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ScoreRule(BaseModel):
    """Condiciones de un nivel de score: `all` deben cumplirse todas, `any` basta con una."""
    all: List[str] = Field(default_factory=list)
    any: List[str] = Field(default_factory=list)


class CriterionDefinition(BaseModel):
    """Un criterio tal como se declara en catalog/criteria.yaml."""
    id: str
    name: str
    confidence: float
    metrics: List[str] = Field(default_factory=list)
    # Condiciones que deben cumplirse para que el criterio aplique; vacio = aplica siempre.
    applies_when: List[str] = Field(default_factory=list)
    # Parametros propios del criterio (umbrales, listas permitidas...) que usa el calculo de metricas.
    parameters: Dict[str, Any] = Field(default_factory=dict)
    scores: Dict[int, ScoreRule] = Field(default_factory=dict)
