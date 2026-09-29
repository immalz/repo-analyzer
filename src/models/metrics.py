from typing import Any, Dict, List

from pydantic import BaseModel, Field

from models.discovery import Fact
from models.enums import PortabilityClass, TechClass


class CriterionMetrics(BaseModel):
    """Base de las metricas de un criterio.

    - Los campos publicos son las metricas que se reportan.
    - `evidence` son los hechos que sustentan el veredicto (se reportan aparte).
    - `scoring_inputs()` son los valores contra los que se evaluan las condiciones del catalogo.
    """
    evidence: List[Fact] = Field(default_factory=list, exclude=True)

    def scoring_inputs(self) -> Dict[str, Any]:
        return self.model_dump()


class TechnologyUsage(BaseModel):
    technology: str
    tech_class: str
    portability_class: str
    references: int = 0
    domain_leak: int = 0
    encapsulation_ratio: float = 0.0
    spread: int = 0


class Arq001Metrics(CriterionMetrics):
    layer_violations: int = 0
    domain_violations: int = 0
    application_violations: int = 0
    ports_layer_present: bool = False
    structure_classifiable: bool = False
    violation_details: List[str] = Field(default_factory=list)


class Arq002Metrics(CriterionMetrics):
    integrations: List[TechnologyUsage] = Field(default_factory=list)

    def scoring_inputs(self) -> Dict[str, Any]:
        cloud_specific = any(i.portability_class == PortabilityClass.CLOUD_SPECIFIC for i in self.integrations)
        return {
            "vendor_sdk_integrations": sum(1 for i in self.integrations if i.tech_class == TechClass.VENDOR_SDK),
            "domain_leak": sum(i.domain_leak for i in self.integrations),
            "encapsulation_ratio": min((i.encapsulation_ratio for i in self.integrations), default=1.0),
            "portability_class": (PortabilityClass.CLOUD_SPECIFIC if cloud_specific else PortabilityClass.AGNOSTIC).value,
        }
