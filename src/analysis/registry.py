"""Registro de analizadores: el UNICO lugar donde se da de alta un criterio nuevo.

Para agregar un criterio:
  1. Declararlo en catalog/criteria.yaml.
  2. Crear su analizador en analysis/analyzers/ (heredando de CriterionAnalyzer).
  3. Agregarlo a la lista de build_analyzers().
"""
from typing import List

from analysis.analyzers.arq001_architecture_style import ArchitectureStyleAnalyzer
from analysis.analyzers.arq002_sdk_isolation import SdkIsolationAnalyzer
from analysis.analyzers.base import CriterionAnalyzer
from analysis.technologies import TechnologyMatcher
from models.technology import TechnologyDefinition


def build_analyzers(technologies: List[TechnologyDefinition]) -> List[CriterionAnalyzer]:
    technology_matcher = TechnologyMatcher(technologies)
    return [
        ArchitectureStyleAnalyzer(),
        SdkIsolationAnalyzer(technology_matcher),
    ]
