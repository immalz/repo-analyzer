"""MOTOR 3 - Motor de evaluacion (scoring contra el catalogo)."""
import unittest

import builders  # noqa: F401  (configura el path de src/)

from evaluation.engine import NOT_APPLICABLE_SCORE, EvaluationEngine
from models.catalog import CriterionDefinition, ScoreRule
from models.enums import EvaluationStatus
from models.metrics import CriterionMetrics


class SampleMetrics(CriterionMetrics):
    """Metricas minimas para probar el motor sin depender de un criterio real."""
    active: bool = True
    violations: int = 0


def build_engine() -> EvaluationEngine:
    definition = CriterionDefinition(
        id="TST.001",
        name="Criterio de prueba",
        confidence=0.8,
        applies_when=["active == true"],
        scores={
            5: ScoreRule(all=["violations == 0"]),
            3: ScoreRule(all=["violations <= 2"]),
            0: ScoreRule(any=["violations > 4"]),
        },
    )
    return EvaluationEngine({"TST.001": definition})


class ScoringNotApplicableTest(unittest.TestCase):
    def setUp(self):
        self.result = build_engine().evaluate("TST.001", SampleMetrics(active=False, violations=9))

    def test_marca_el_status_como_no_aplica(self):
        self.assertEqual(self.result.status, EvaluationStatus.NOT_APPLICABLE)

    def test_asigna_el_score_de_no_aplica(self):
        self.assertEqual(self.result.score, NOT_APPLICABLE_SCORE)

    def test_no_evalua_los_niveles_aunque_haya_violaciones(self):
        self.assertNotEqual(self.result.score, 0)


class ScoringLevelsTest(unittest.TestCase):
    def setUp(self):
        self.engine = build_engine()

    def test_asigna_nivel_optimo_sin_violaciones(self):
        self.assertEqual(self.engine.evaluate("TST.001", SampleMetrics(violations=0)).score, 5)

    def test_asigna_nivel_intermedio_dentro_del_umbral(self):
        self.assertEqual(self.engine.evaluate("TST.001", SampleMetrics(violations=2)).score, 3)

    def test_asigna_fallo_critico_sobre_el_umbral(self):
        self.assertEqual(self.engine.evaluate("TST.001", SampleMetrics(violations=5)).score, 0)

    def test_queda_unknown_si_ningun_nivel_se_cumple(self):
        self.assertEqual(self.engine.evaluate("TST.001", SampleMetrics(violations=3)).status, EvaluationStatus.UNKNOWN)

    def test_explica_por_que_no_alcanza_el_nivel_optimo(self):
        self.assertIn("violations == 0", self.engine.evaluate("TST.001", SampleMetrics(violations=1)).reason)


class ScoringReportTest(unittest.TestCase):
    def setUp(self):
        self.result = build_engine().evaluate("TST.001", SampleMetrics())

    def test_reporta_la_confianza_del_catalogo(self):
        self.assertEqual(self.result.confidence, 0.8)

    def test_reporta_el_nombre_del_criterio(self):
        self.assertEqual(self.result.name, "Criterio de prueba")

    def test_no_expone_la_evidencia_dentro_de_las_metricas(self):
        self.assertNotIn("evidence", self.result.metrics)


if __name__ == "__main__":
    unittest.main()
