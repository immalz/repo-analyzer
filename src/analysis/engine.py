from typing import Dict, List

from analysis.classifier import LayerClassifier
from analysis.registry import build_analyzers
from models.catalog import CriterionDefinition
from models.discovery import RepositoryInventory
from models.metrics import CriterionMetrics
from models.technology import TechnologyDefinition


class AnalysisEngine:
    """MOTOR 2 - Analisis.

    Interpreta los hallazgos del inventario:
      1. clasifica cada componente en su capa (dominio, aplicacion, infraestructura);
      2. ejecuta el analizador de cada criterio registrado y obtiene sus metricas.
    No asigna scores: eso es del motor de evaluacion.
    """

    def __init__(self, criteria: Dict[str, CriterionDefinition], technologies: List[TechnologyDefinition],
                 layer_overrides: Dict[str, List[str]]):
        self.criteria = criteria
        self.classifier = LayerClassifier(layer_overrides)
        self.analyzers = build_analyzers(technologies)

    def run(self, inventory: RepositoryInventory) -> Dict[str, CriterionMetrics]:
        self.classifier.classify(inventory.components)
        return {
            analyzer.criterion_id: analyzer.analyze(inventory, self.criteria[analyzer.criterion_id])
            for analyzer in self.analyzers
        }
