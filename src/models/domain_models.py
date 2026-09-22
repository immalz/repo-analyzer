from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
from enum import Enum

class EvaluationStatus(str, Enum):
    EVALUATED = "EVALUATED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class ModuleRole(str, Enum):
    DOMAIN = "DOMAIN"
    APPLICATION = "APPLICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    UNKNOWN = "UNKNOWN"

class Evidence(BaseModel):
    file_path: str
    line_number: int
    matched_content: str
    tags: List[str] = Field(default_factory=list)

class ComponentInfo(BaseModel):
    file_path: str
    package: str = ""
    imports: List[str] = Field(default_factory=list)
    declarations: List[str] = Field(default_factory=list)
    module: str = ""
    role: ModuleRole = ModuleRole.UNKNOWN

class ModuleInfo(BaseModel):
    name: str
    path: str
    dependencies: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)

class TechnologyUsage(BaseModel):
    technology: str
    tech_class: str
    portability_class: str
    references: int = 0
    domain_leak: int = 0
    encapsulation_ratio: float = 0.0
    spread: int = 0

class Arq001Metrics(BaseModel):
    layer_violations: int = 0
    domain_violations: int = 0
    application_violations: int = 0
    ports_layer_present: bool = False
    structure_classifiable: bool = False
    violation_details: List[str] = Field(default_factory=list)

class Arq002Metrics(BaseModel):
    integrations: List[TechnologyUsage] = Field(default_factory=list)

class RuleEvaluation(BaseModel):
    rule_id: str
    status: EvaluationStatus
    score: Optional[int]
    reason: str = ""
    metrics: Dict[str, Any]
    evidence: List[Evidence]

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: Optional[int]) -> Optional[int]:
        if v not in (0, 3, 5, None):
            raise ValueError("Score must be 0, 3, 5, or None")
        return v

class FinalReport(BaseModel):
    repository_path: str
    commit_sha: str = "unknown"
    evaluations: List[RuleEvaluation]