from typing import Dict, Iterable, List

from models.discovery import ComponentInfo, Fact
from models.enums import ModuleRole
from models.metrics import Arq001Metrics, Arq002Metrics, TechnologyUsage


class MetricsCalculator:
    def __init__(self, technology_catalog: Dict, domain_allowed_packages: List[str]):
        self.tech_catalog = technology_catalog.get("technologies", {})
        # Paquetes externos que el dominio puede importar sin que cuente como violacion (p.ej. java, lombok).
        self.domain_allowed_packages = domain_allowed_packages

    def calculate_arq001(self, components: List[ComponentInfo]) -> Arq001Metrics:
        metrics = Arq001Metrics()
        metrics.structure_classifiable = any(c.role != ModuleRole.UNKNOWN for c in components)
        project_packages = {c.package for c in components if c.package}

        for comp in components:
            for imp_fact in comp.facts_of("java.import"):
                imp = imp_fact.attributes.get("name", "")
                if comp.role == ModuleRole.DOMAIN:
                    if _belongs_to(imp, project_packages):
                        target_role = self._find_role_of_package(imp, components)
                        if target_role in [ModuleRole.INFRASTRUCTURE, ModuleRole.APPLICATION]:
                            self._add_violation(metrics, imp_fact, ModuleRole.DOMAIN,
                                                f"DOMAIN component '{comp.file_path}' illegally imports {target_role.value} package '{imp}'")
                    elif not _belongs_to(imp, self.domain_allowed_packages):
                        # El catalogo cuenta tambien las dependencias del dominio hacia frameworks o SDK externos.
                        self._add_violation(metrics, imp_fact, ModuleRole.DOMAIN,
                                            f"DOMAIN component '{comp.file_path}' depends on external framework/SDK '{imp}'")
                elif comp.role == ModuleRole.APPLICATION:
                    target_role = self._find_role_of_package(imp, components)
                    if target_role == ModuleRole.INFRASTRUCTURE:
                        self._add_violation(metrics, imp_fact, ModuleRole.APPLICATION,
                                            f"APPLICATION component '{comp.file_path}' illegally imports INFRASTRUCTURE package '{imp}'")

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

    def calculate_arq002(self, components: List[ComponentInfo]) -> Arq002Metrics:
        metrics = Arq002Metrics()
        tech_usages: Dict[str, TechnologyUsage] = {}

        for comp in components:
            for imp_fact in comp.facts_of("java.import"):
                tech_id = self._identify_technology(imp_fact.attributes.get("name", ""))
                if tech_id:
                    if tech_id not in tech_usages:
                        tech_info = self.tech_catalog[tech_id]
                        tech_usages[tech_id] = TechnologyUsage(
                            technology=tech_id,
                            tech_class=tech_info.get("type", "UNKNOWN"),
                            portability_class=tech_info.get("portability_class", "UNKNOWN")
                        )

                    usage = tech_usages[tech_id]
                    usage.references += 1
                    usage.spread += 1
                    metrics.evidence.append(imp_fact)

                    if comp.role == ModuleRole.DOMAIN:
                        usage.domain_leak += 1

        for usage in tech_usages.values():
            infra_refs = 0
            for comp in components:
                for imp in comp.imports:
                    if self._identify_technology(imp) == usage.technology:
                        if comp.role == ModuleRole.INFRASTRUCTURE:
                            infra_refs += 1
            if usage.references > 0:
                usage.encapsulation_ratio = infra_refs / usage.references

            metrics.integrations.append(usage)

        return metrics

    @staticmethod
    def _add_violation(metrics: Arq001Metrics, imp_fact: Fact, source_role: ModuleRole, detail: str) -> None:
        metrics.layer_violations += 1
        if source_role == ModuleRole.DOMAIN:
            metrics.domain_violations += 1
        else:
            metrics.application_violations += 1
        metrics.violation_details.append(detail)
        metrics.evidence.append(imp_fact)

    def _find_role_of_package(self, package: str, components: List[ComponentInfo]) -> ModuleRole:
        for comp in components:
            if comp.package and _belongs_to(package, [comp.package]):
                return comp.role

        # FALLBACK (solo si no se encontró un componente explícito)
        lower_pkg = package.lower()
        if any(kw in lower_pkg for kw in ["domain", "model", "entity", "core"]):
            return ModuleRole.DOMAIN
        if any(kw in lower_pkg for kw in ["application", "service", "usecase", "port"]):
            return ModuleRole.APPLICATION
        if any(kw in lower_pkg for kw in ["repository", "infrastructure", "adapter", "persistence", "config"]):
            return ModuleRole.INFRASTRUCTURE

        return ModuleRole.UNKNOWN

    def _identify_technology(self, imp: str) -> str:
        for tech_id, tech_info in self.tech_catalog.items():
            for pattern in tech_info.get("patterns", []):
                if imp.startswith(pattern):
                    return tech_id
        return ""


def _belongs_to(name: str, packages: Iterable[str]) -> bool:
    """True si `name` es uno de los paquetes o esta dentro de ellos ("java" cubre "java.util.List", pero no "javax")."""
    return any(name == p or name.startswith(p + ".") for p in packages)
