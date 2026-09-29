from typing import Dict

from analysis.analyzers.base import CriterionAnalyzer
from analysis.technologies import TechnologyMatcher
from models.catalog import CriterionDefinition
from models.discovery import RepositoryInventory
from models.enums import ModuleRole
from models.metrics import Arq002Metrics, TechnologyUsage


class SdkIsolationAnalyzer(CriterionAnalyzer):
    """ARQ.002 - Aislamiento de Dependencias / SDK Especificos.

    Por cada SDK del catalogo de tecnologias que aparezca en los imports, mide:
      - references: cuantas veces se usa;
      - domain_leak: cuantas de esas veces estan en el dominio;
      - encapsulation_ratio: que fraccion del uso esta en la infraestructura (adaptadores).
    """

    criterion_id = "ARQ.002"

    def __init__(self, technology_matcher: TechnologyMatcher):
        self.technology_matcher = technology_matcher

    def analyze(self, inventory: RepositoryInventory, criterion: CriterionDefinition) -> Arq002Metrics:
        metrics = Arq002Metrics()
        usages: Dict[str, TechnologyUsage] = {}
        infrastructure_references: Dict[str, int] = {}

        for comp in inventory.components:
            for import_fact in comp.facts_of("java.import"):
                technology = self.technology_matcher.identify(import_fact.attributes.get("name", ""))
                if technology is None:
                    continue

                usage = usages.setdefault(technology.id, TechnologyUsage(
                    technology=technology.id,
                    tech_class=technology.type,
                    portability_class=technology.portability_class,
                ))
                usage.references += 1
                usage.spread += 1
                metrics.evidence.append(import_fact)

                if comp.role == ModuleRole.DOMAIN:
                    usage.domain_leak += 1
                if comp.role == ModuleRole.INFRASTRUCTURE:
                    infrastructure_references[technology.id] = infrastructure_references.get(technology.id, 0) + 1

        for usage in usages.values():
            usage.encapsulation_ratio = infrastructure_references.get(usage.technology, 0) / usage.references
            metrics.integrations.append(usage)
        return metrics
