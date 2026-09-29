from abc import ABC, abstractmethod

from models.catalog import CriterionDefinition
from models.discovery import RepositoryInventory
from models.metrics import CriterionMetrics


class CriterionAnalyzer(ABC):
    """Contrato comun de todos los analizadores: uno por criterio (o familia de criterios).

    Recibe el inventario ya clasificado por capas y devuelve las metricas del
    criterio junto con su evidencia. No asigna scores: eso es del motor de evaluacion.
    """

    # Id del criterio en catalog/criteria.yaml que este analizador calcula.
    criterion_id: str

    @abstractmethod
    def analyze(self, inventory: RepositoryInventory, criterion: CriterionDefinition) -> CriterionMetrics:
        ...
