"""MOTOR 2 - Clasificacion de capas y registro de analizadores."""
import unittest

from builders import CRITERIA_FILE, TECHNOLOGIES, component
from analysis.classifier import LayerClassifier, role_of_package
from analysis.registry import build_analyzers
from config.loader import load_criteria
from models.enums import ModuleRole


def classify(path, overrides=None):
    comp = component(path, ModuleRole.UNKNOWN, "")
    LayerClassifier(overrides or {}).classify([comp])
    return comp.role


class LayerClassifierTest(unittest.TestCase):
    def test_reconoce_el_dominio_por_carpeta(self):
        self.assertEqual(classify("model/src/main/java/com/acme/model/Order.java"), ModuleRole.DOMAIN)

    def test_reconoce_la_aplicacion_por_carpeta(self):
        self.assertEqual(classify("app/src/main/java/com/acme/application/port/OrderPort.java"), ModuleRole.APPLICATION)

    def test_reconoce_la_infraestructura_por_carpeta(self):
        self.assertEqual(classify("app/src/main/java/com/acme/adapter/OrderJpa.java"), ModuleRole.INFRASTRUCTURE)

    def test_reconoce_carpetas_en_la_raiz_del_repo(self):
        self.assertEqual(classify("domain/Order.java"), ModuleRole.DOMAIN)

    def test_deja_sin_rol_una_carpeta_no_estandar(self):
        self.assertEqual(classify("src/main/java/org/acme/GreetingResource.java"), ModuleRole.UNKNOWN)

    def test_la_capa_declarada_por_el_owner_tiene_prioridad(self):
        overrides = {"domain": ["org/acme/"]}
        self.assertEqual(classify("src/main/java/org/acme/GreetingResource.java", overrides), ModuleRole.DOMAIN)


class RoleOfPackageTest(unittest.TestCase):
    def test_usa_la_capa_del_componente_dueno_del_paquete(self):
        adapter = component("adapter/OrderJpa.java", ModuleRole.INFRASTRUCTURE, "com.acme.orders")
        self.assertEqual(role_of_package("com.acme.orders.OrderJpa", [adapter]), ModuleRole.INFRASTRUCTURE)

    def test_deduce_la_capa_por_el_nombre_si_no_hay_componente(self):
        self.assertEqual(role_of_package("com.vendor.persistence.Store", []), ModuleRole.INFRASTRUCTURE)

    def test_ignora_el_nombre_de_la_clase_al_deducir_la_capa(self):
        self.assertEqual(role_of_package("jakarta.persistence.Entity", []), ModuleRole.INFRASTRUCTURE)

    def test_una_clase_llamada_service_no_convierte_el_paquete_en_aplicacion(self):
        self.assertEqual(role_of_package("org.springframework.stereotype.Service", []), ModuleRole.UNKNOWN)

    def test_no_confunde_una_palabra_contenida_en_otro_segmento(self):
        self.assertEqual(role_of_package("com.vendor.coreutils.Helper", []), ModuleRole.UNKNOWN)

    def test_reconoce_el_dominio_por_un_segmento_del_paquete(self):
        self.assertEqual(role_of_package("com.acme.model.Order", []), ModuleRole.DOMAIN)


class AnalyzerRegistryTest(unittest.TestCase):
    def test_cada_analizador_registrado_tiene_su_criterio_en_el_catalogo(self):
        registered = {analyzer.criterion_id for analyzer in build_analyzers(TECHNOLOGIES)}
        self.assertEqual(registered - set(load_criteria(CRITERIA_FILE)), set())


if __name__ == "__main__":
    unittest.main()
