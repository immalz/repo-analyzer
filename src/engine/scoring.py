from typing import Any, Dict, List, Optional, Tuple

from engine.conditions import evaluate_condition
from models.catalog import CriterionDefinition
from models.enums import EvaluationStatus
from models.metrics import CriterionMetrics
from models.report import RuleEvaluation

CRITICAL_LEVEL = 0
# Sin evidencia de acoplamiento el criterio se considera apto para migrar. El status sigue siendo
# NOT_APPLICABLE para que una agregacion posterior pueda excluirlo del denominador si el comite lo decide.
NOT_APPLICABLE_SCORE = 5


class ScoringEngine:
    """Asigna el score de un criterio evaluando sus metricas contra catalog/criteria.yaml.

    Orden de evaluacion:
      1. applies_when: si alguna condicion no se cumple -> NOT_APPLICABLE con NOT_APPLICABLE_SCORE.
      2. Nivel 0 (`any`): basta una condicion para el fallo critico.
      3. Niveles positivos de mayor a menor (`all`): el primero que se cumpla completo.
      4. Ninguno -> UNKNOWN.
    """

    def __init__(self, criteria: Dict[str, CriterionDefinition]):
        self.criteria = criteria

    def evaluate(self, criterion_id: str, metrics: CriterionMetrics) -> RuleEvaluation:
        definition = self.criteria[criterion_id]
        score, status, reason = self._score(definition, metrics.scoring_inputs())
        return RuleEvaluation(
            rule_id=definition.id,
            name=definition.name,
            status=status,
            score=score,
            confidence=definition.confidence,
            reason=reason,
            metrics=metrics.model_dump(),
            evidence=metrics.evidence if status == EvaluationStatus.EVALUATED else [],
        )

    def _score(self, definition: CriterionDefinition, values: Dict[str, Any]) -> Tuple[Optional[int], EvaluationStatus, str]:
        unmet = self._unmet(definition.applies_when, values)
        if unmet:
            return (NOT_APPLICABLE_SCORE, EvaluationStatus.NOT_APPLICABLE,
                    f"No aplica (no se cumple '{unmet[0]}'): sin evidencia de acoplamiento, se considera apto para migrar.")

        critical = definition.scores.get(CRITICAL_LEVEL)
        if critical:
            triggered = [c for c in critical.any if evaluate_condition(c, values)]
            if triggered:
                return CRITICAL_LEVEL, EvaluationStatus.EVALUATED, f"Fallo crítico detectado: {triggered[0]}"

        levels = sorted((level for level in definition.scores if level != CRITICAL_LEVEL), reverse=True)
        for level in levels:
            rule = definition.scores[level]
            if rule.all and not self._unmet(rule.all, values):
                return level, EvaluationStatus.EVALUATED, self._reason(definition, level, levels[0], values)

        return None, EvaluationStatus.UNKNOWN, "No cumple con las reglas de evaluación configuradas."

    def _reason(self, definition: CriterionDefinition, level: int, best_level: int, values: Dict[str, Any]) -> str:
        if level == best_level:
            return "Cumple todos los requisitos para nivel óptimo."
        missing = self._unmet(definition.scores[best_level].all, values)
        return f"Cumple nivel {level}. No alcanza nivel óptimo por fallar en: {', '.join(missing)}"

    @staticmethod
    def _unmet(conditions: List[str], values: Dict[str, Any]) -> List[str]:
        return [c for c in conditions if not evaluate_condition(c, values)]
