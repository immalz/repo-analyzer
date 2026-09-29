from typing import List

from pydantic import BaseModel, Field


class TechnologyDefinition(BaseModel):
    """Una tecnologia tal como se declara en catalog/technology.yaml."""
    id: str
    type: str
    portability_class: str
    # Prefijos de paquete que identifican a la tecnologia (p.ej. "com.azure").
    patterns: List[str] = Field(default_factory=list)
