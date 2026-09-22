from models.domain_models import ComponentInfo, Arq001Metrics, Arq002Metrics, TechnologyUsage, ModuleRole
from typing import List, Dict

class MetricsCalculator:
    def __init__(self, technology_catalog: Dict):
        self.tech_catalog = technology_catalog.get("technologies", {})

    def calculate_arq001(self, components: List[ComponentInfo]) -> Arq001Metrics:
        metrics = Arq001Metrics()
        
        known_roles = [c for c in components if c.role != ModuleRole.UNKNOWN]
        metrics.structure_classifiable = len(known_roles) > 0
        
        for comp in components:
            if comp.role == ModuleRole.DOMAIN:
                for imp in comp.imports:
                    target_role = self._find_role_of_package(imp, components)
                    if target_role in [ModuleRole.INFRASTRUCTURE, ModuleRole.APPLICATION]:
                        metrics.domain_violations += 1
                        metrics.layer_violations += 1
                        metrics.violation_details.append(f"DOMAIN component '{comp.file_path}' illegally imports {target_role.value} package '{imp}'")
            elif comp.role == ModuleRole.APPLICATION:
                for imp in comp.imports:
                    target_role = self._find_role_of_package(imp, components)
                    if target_role == ModuleRole.INFRASTRUCTURE:
                        metrics.application_violations += 1
                        metrics.layer_violations += 1
                        metrics.violation_details.append(f"APPLICATION component '{comp.file_path}' illegally imports INFRASTRUCTURE package '{imp}'")

            if comp.declarations and comp.role in [ModuleRole.DOMAIN, ModuleRole.APPLICATION]:
                for dec in comp.declarations:
                    if "interface" in dec:
                        metrics.ports_layer_present = True

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
            for imp in comp.imports:
                tech_id = self._identify_technology(imp)
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

    def _find_role_of_package(self, package: str, components: List[ComponentInfo]) -> ModuleRole:
        for comp in components:
            if comp.package and package.startswith(comp.package):
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
