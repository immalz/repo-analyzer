from typing import List

from analysis.analyzers.base import CriterionAnalyzer
from analysis.classifier import role_of_package
from models.catalog import CriterionDefinition
from models.discovery import ComponentInfo, Fact, RepositoryInventory
from models.enums import ModuleRole
from models.metrics import Arq001Metrics
from shared.java_packages import belongs_to


class ArchitectureStyleAnalyzer(CriterionAnalyzer):
    """ARQ.001 - Estilo Arquitectonico.

    Mide si las dependencias van hacia el nucleo del negocio:
      - el dominio no debe importar la capa de aplicacion, la infraestructura ni
        frameworks o SDK externos (salvo los de `domain_allowed_packages`);
      - la capa de aplicacion no debe importar la infraestructura;
      - debe existir una capa de puertos (interfaces en dominio o aplicacion).
    """

    criterion_id = "ARQ.001"

    def analyze(self, inventory: RepositoryInventory, criterion: CriterionDefinition) -> Arq001Metrics:
        components = inventory.components
        allowed_packages: List[str] = criterion.parameters.get("domain_allowed_packages", [])
        project_packages = {c.package for c in components if c.package}

        metrics = Arq001Metrics()
        metrics.structure_classifiable = any(c.role != ModuleRole.UNKNOWN for c in components)

        for comp in components:
            for import_fact in comp.facts_of("java.import"):
                imported = import_fact.attributes.get("name", "")
                if comp.role == ModuleRole.DOMAIN:
                    self._check_domain_import(metrics, comp, import_fact, imported, components, project_packages, allowed_packages)
                elif comp.role == ModuleRole.APPLICATION:
                    self._check_application_import(metrics, comp, import_fact, imported, components)

            if comp.role in [ModuleRole.DOMAIN, ModuleRole.APPLICATION]:
                for type_fact in comp.facts_of("java.type"):
                    if type_fact.attributes.get("kind") == "interface":
                        metrics.ports_layer_present = True
                        metrics.evidence.append(type_fact)

        if not metrics.ports_layer_present:
            metrics.violation_details.append(
                "Falta Capa de Puertos: No se detectaron interfaces en las capas de Dominio o Aplicación. "
                "Para alcanzar Score 5, inyecta dependencias usando interfaces (Dependency Inversion)."
            )
        return metrics

    def _check_domain_import(self, metrics: Arq001Metrics, comp: ComponentInfo, import_fact: Fact, imported: str,
                             components: List[ComponentInfo], project_packages: set, allowed_packages: List[str]) -> None:
        if belongs_to(imported, project_packages):
            target_role = role_of_package(imported, components)
            if target_role in [ModuleRole.INFRASTRUCTURE, ModuleRole.APPLICATION]:
                self._add_violation(metrics, import_fact, ModuleRole.DOMAIN,
                                    f"DOMAIN component '{comp.file_path}' illegally imports {target_role.value} package '{imported}'")
        elif not belongs_to(imported, allowed_packages):
            # El catalogo cuenta tambien las dependencias del dominio hacia frameworks o SDK externos.
            self._add_violation(metrics, import_fact, ModuleRole.DOMAIN,
                                f"DOMAIN component '{comp.file_path}' depends on external framework/SDK '{imported}'")

    def _check_application_import(self, metrics: Arq001Metrics, comp: ComponentInfo, import_fact: Fact, imported: str,
                                  components: List[ComponentInfo]) -> None:
        if role_of_package(imported, components) == ModuleRole.INFRASTRUCTURE:
            self._add_violation(metrics, import_fact, ModuleRole.APPLICATION,
                                f"APPLICATION component '{comp.file_path}' illegally imports INFRASTRUCTURE package '{imported}'")

    @staticmethod
    def _add_violation(metrics: Arq001Metrics, import_fact: Fact, source_role: ModuleRole, detail: str) -> None:
        metrics.layer_violations += 1
        if source_role == ModuleRole.DOMAIN:
            metrics.domain_violations += 1
        else:
            metrics.application_violations += 1
        metrics.violation_details.append(detail)
        metrics.evidence.append(import_fact)
