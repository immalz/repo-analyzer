import unittest

from builders import AZURE_BLOB, TECH_CATALOG, component, port_component
from engine.metrics import MetricsCalculator
from models.enums import ModuleRole

DOMAIN_IMPORTS = [
    "lombok.Getter",
    "java.util.List",
    "javax.persistence.Entity",
    "org.springframework.stereotype.Component",
]


def violating_imports(metrics):
    return [f.attributes["name"] for f in metrics.evidence if f.kind == "java.import"]


class Arq001DomainWithAllowListTest(unittest.TestCase):
    def setUp(self):
        domain = component("model/Order.java", ModuleRole.DOMAIN, "com.acme.model", imports=DOMAIN_IMPORTS)
        self.metrics = MetricsCalculator(TECH_CATALOG, ["java", "lombok"]).calculate_arq001([domain, port_component()])

    def test_cuenta_solo_los_frameworks_no_permitidos(self):
        self.assertEqual(self.metrics.domain_violations, 2)

    def test_no_cuenta_lombok_si_esta_permitido(self):
        self.assertNotIn("lombok.Getter", violating_imports(self.metrics))

    def test_java_permitido_no_cubre_javax(self):
        self.assertIn("javax.persistence.Entity", violating_imports(self.metrics))

    def test_cuenta_spring_en_el_dominio(self):
        self.assertIn("org.springframework.stereotype.Component", violating_imports(self.metrics))

    def test_detecta_la_capa_de_puertos(self):
        self.assertTrue(self.metrics.ports_layer_present)


class Arq001DomainWithoutAllowListTest(unittest.TestCase):
    def setUp(self):
        domain = component("model/Order.java", ModuleRole.DOMAIN, "com.acme.model", imports=DOMAIN_IMPORTS)
        self.metrics = MetricsCalculator(TECH_CATALOG, []).calculate_arq001([domain, port_component()])

    def test_cuenta_todos_los_imports_externos(self):
        self.assertEqual(self.metrics.domain_violations, 4)


class Arq001InternalImportsTest(unittest.TestCase):
    def setUp(self):
        domain = component("model/Order.java", ModuleRole.DOMAIN, "com.acme.model",
                           imports=["com.acme.adapter.OrderJpa", "com.acme.model.Money"])
        adapter = component("adapter/OrderJpa.java", ModuleRole.INFRASTRUCTURE, "com.acme.adapter")
        self.metrics = MetricsCalculator(TECH_CATALOG, ["java"]).calculate_arq001([domain, adapter, port_component()])

    def test_cuenta_el_import_del_dominio_hacia_infraestructura(self):
        self.assertEqual(violating_imports(self.metrics), ["com.acme.adapter.OrderJpa"])


class Arq001PackagePrefixTest(unittest.TestCase):
    def setUp(self):
        cart = component("model/Cart.java", ModuleRole.DOMAIN, "com.acme.cart", imports=["com.acme.cartitem.Line"])
        cart_item = component("adapter/Line.java", ModuleRole.INFRASTRUCTURE, "com.acme.cartitem")
        self.metrics = MetricsCalculator(TECH_CATALOG, []).calculate_arq001([cart, cart_item])

    def test_no_confunde_un_paquete_con_otro_que_empieza_igual(self):
        self.assertEqual(self.metrics.domain_violations, 1)


class Arq002EncapsulatedSdkTest(unittest.TestCase):
    def setUp(self):
        adapter = component("adapter/Blob.java", ModuleRole.INFRASTRUCTURE, "com.acme.adapter", imports=[AZURE_BLOB])
        self.inputs = MetricsCalculator(TECH_CATALOG, []).calculate_arq002([adapter]).scoring_inputs()

    def test_cuenta_la_integracion_con_sdk_de_proveedor(self):
        self.assertEqual(self.inputs["vendor_sdk_integrations"], 1)

    def test_no_hay_fuga_al_dominio(self):
        self.assertEqual(self.inputs["domain_leak"], 0)

    def test_el_encapsulamiento_es_total(self):
        self.assertEqual(self.inputs["encapsulation_ratio"], 1.0)


class Arq002LeakedSdkTest(unittest.TestCase):
    def setUp(self):
        adapter = component("adapter/Blob.java", ModuleRole.INFRASTRUCTURE, "com.acme.adapter", imports=[AZURE_BLOB])
        domain = component("model/Doc.java", ModuleRole.DOMAIN, "com.acme.model", imports=[AZURE_BLOB])
        self.inputs = MetricsCalculator(TECH_CATALOG, []).calculate_arq002([adapter, domain]).scoring_inputs()

    def test_detecta_la_fuga_al_dominio(self):
        self.assertEqual(self.inputs["domain_leak"], 1)


class Arq002WithoutSdkTest(unittest.TestCase):
    def setUp(self):
        adapter = component("adapter/Repo.java", ModuleRole.INFRASTRUCTURE, "com.acme.adapter", imports=["java.util.List"])
        self.inputs = MetricsCalculator(TECH_CATALOG, []).calculate_arq002([adapter]).scoring_inputs()

    def test_no_registra_integraciones(self):
        self.assertEqual(self.inputs["vendor_sdk_integrations"], 0)


if __name__ == "__main__":
    unittest.main()
