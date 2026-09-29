"""Escenarios de punta a punta con el catalogo real (catalog/criteria.yaml)."""
import unittest

from builders import AZURE_BLOB, CRITERIA_FILE, TECH_CATALOG, component, port_component
from config.loader import load_criteria
from engine.metrics import MetricsCalculator
from engine.scoring import ScoringEngine
from models.enums import EvaluationStatus, ModuleRole


class CatalogScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.criteria = load_criteria(CRITERIA_FILE)
        cls.engine = ScoringEngine(cls.criteria)
        cls.calculator = MetricsCalculator(TECH_CATALOG, cls.criteria["ARQ.001"].parameters["domain_allowed_packages"])

    def evaluate_arq001(self, *components):
        return self.engine.evaluate("ARQ.001", self.calculator.calculate_arq001(list(components)))

    def evaluate_arq002(self, *components):
        return self.engine.evaluate("ARQ.002", self.calculator.calculate_arq002(list(components)))


class Arq001CatalogTest(CatalogScenarioTest):
    def test_dominio_limpio_con_puertos_obtiene_5(self):
        domain = component("model/Order.java", ModuleRole.DOMAIN, "com.acme.model", imports=["lombok.Getter"])
        self.assertEqual(self.evaluate_arq001(domain, port_component()).score, 5)

    def test_dominio_con_framework_externo_obtiene_0(self):
        domain = component("model/Order.java", ModuleRole.DOMAIN, "com.acme.model", imports=["jakarta.persistence.Entity"])
        self.assertEqual(self.evaluate_arq001(domain, port_component()).score, 0)

    def test_sin_capas_reconocibles_obtiene_0(self):
        unknown = component("Main.java", ModuleRole.UNKNOWN, "com.acme")
        self.assertEqual(self.evaluate_arq001(unknown).score, 0)

    def test_reporta_la_confianza_declarada(self):
        self.assertEqual(self.evaluate_arq001(port_component()).confidence, 0.6)


class Arq002CatalogTest(CatalogScenarioTest):
    def test_sin_sdk_no_aplica(self):
        adapter = component("adapter/Repo.java", ModuleRole.INFRASTRUCTURE, "com.acme.adapter")
        self.assertEqual(self.evaluate_arq002(adapter).status, EvaluationStatus.NOT_APPLICABLE)

    def test_sin_sdk_se_considera_apto(self):
        adapter = component("adapter/Repo.java", ModuleRole.INFRASTRUCTURE, "com.acme.adapter")
        self.assertEqual(self.evaluate_arq002(adapter).score, 5)

    def test_sdk_de_nube_encapsulado_obtiene_3(self):
        adapter = component("adapter/Blob.java", ModuleRole.INFRASTRUCTURE, "com.acme.adapter", imports=[AZURE_BLOB])
        self.assertEqual(self.evaluate_arq002(adapter).score, 3)

    def test_sdk_filtrado_al_dominio_obtiene_0(self):
        domain = component("model/Doc.java", ModuleRole.DOMAIN, "com.acme.model", imports=[AZURE_BLOB])
        self.assertEqual(self.evaluate_arq002(domain).score, 0)


if __name__ == "__main__":
    unittest.main()
