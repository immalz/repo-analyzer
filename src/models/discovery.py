from typing import Dict, List

from pydantic import BaseModel, Field

from models.enums import ModuleRole


class Fact(BaseModel):
    """Hecho neutral extraido por una regla de Semgrep (rules/*.yaml)."""
    kind: str
    file_path: str
    line_number: int
    attributes: Dict[str, str] = Field(default_factory=dict)
    criteria: List[str] = Field(default_factory=list)
    rule_id: str = ""


class ComponentInfo(BaseModel):
    file_path: str
    package: str = ""
    module: str = ""
    role: ModuleRole = ModuleRole.UNKNOWN
    facts: List[Fact] = Field(default_factory=list)

    def facts_of(self, kind: str) -> List[Fact]:
        return [f for f in self.facts if f.kind == kind]

    @property
    def imports(self) -> List[str]:
        return [f.attributes.get("name", "") for f in self.facts_of("java.import")]


class ModuleInfo(BaseModel):
    name: str
    path: str
    dependencies: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)


class RepositoryInventory(BaseModel):
    """Resultado unico del descubrimiento: todo lo que las fases siguientes pueden consultar."""
    files: List[str] = Field(default_factory=list)
    scanned_files: List[str] = Field(default_factory=list)
    facts: List[Fact] = Field(default_factory=list)
    components: List[ComponentInfo] = Field(default_factory=list)
    modules: List[ModuleInfo] = Field(default_factory=list)
    scan_errors: List[str] = Field(default_factory=list)

    def facts_of(self, kind: str) -> List[Fact]:
        return [f for f in self.facts if f.kind == kind]
