from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator

from models.discovery import Fact
from models.enums import EvaluationStatus


class RuleEvaluation(BaseModel):
    rule_id: str
    name: str
    status: EvaluationStatus
    score: Optional[int]
    # Confianza declarada en el catalogo para el criterio (se reporta junto al veredicto).
    confidence: float
    reason: str = ""
    metrics: Dict[str, Any]
    evidence: List[Fact]

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: Optional[int]) -> Optional[int]:
        if v not in (0, 3, 5, None):
            raise ValueError("Score must be 0, 3, 5, or None")
        return v


class FinalReport(BaseModel):
    repository_path: str
    commit_sha: str = "unknown"
    evaluations: List[RuleEvaluation]
