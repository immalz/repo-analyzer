"""MOTOR 1 - Descubrimiento con Semgrep contra tests/fixtures/sample-app (un proyecto con todas las tecnologias)."""
import json
import unittest
from functools import lru_cache

from builders import RULES_DIR, SAMPLE_APP
from discovery.engine import DiscoveryEngine

PLAIN_SECRETS = ["s3cr3t!", "tok_live_123", "Hunter2", "plainTextKafkaPwd", "supersecret", "MIIEowIBAAKCAQEA"]


@lru_cache(maxsize=1)
def scan_sample_app():
    """Semgrep se ejecuta una sola vez para todas las clases de este archivo."""
    return DiscoveryEngine(RULES_DIR).run(SAMPLE_APP)


class DiscoveryTestCase(unittest.TestCase):
    """Base comun (beforeAll): comparte el inventario del fixture entre los tests."""

    @classmethod
    def setUpClass(cls):
        cls.inventory = scan_sample_app()

    def values(self, kind, field):
        return {f.attributes.get(field) for f in self.inventory.facts_of(kind)}

    def component(self, suffix):
        return next(c for c in self.inventory.components if c.file_path.endswith(suffix))


class ScanTest(DiscoveryTestCase):
    def test_no_reporta_errores_de_semgrep(self):
        self.assertEqual(self.inventory.scan_errors, [])

    def test_el_inventario_incluye_archivos_binarios(self):
        self.assertIn("src/main/resources/keystore.p12", self.inventory.files)

    def test_cada_criterio_de_las_reglas_recibe_hechos(self):
        covered = {c for f in self.inventory.facts for c in f.criteria}
        self.assertEqual(DiscoveryEngine(RULES_DIR).rule_criteria() - covered, set())


class JavaStructureTest(DiscoveryTestCase):
    def test_captura_imports(self):
        self.assertIn("com.azure.storage.blob.BlobClient", self.values("java.import", "name"))

    def test_ignora_imports_comentados(self):
        self.assertNotIn("com.amazonaws.services.s3.AmazonS3", self.values("java.import", "name"))

    def test_toma_el_paquete_de_la_declaracion(self):
        self.assertEqual(self.component("domain/Order.java").package, "com.acme.shop.domain")

    def test_cuenta_cada_import_una_sola_vez(self):
        self.assertEqual(len(self.component("domain/Order.java").imports), 2)

    def test_no_confunde_modificadores_con_anotaciones(self):
        self.assertNotIn("native", self.values("java.annotation", "name"))


class JavaTypesTest(DiscoveryTestCase):
    def types(self):
        return {(f.attributes["name"], f.attributes["kind"]) for f in self.inventory.facts_of("java.type")}

    def test_reconoce_interfaces(self):
        self.assertIn(("OrderRepository", "interface"), self.types())

    def test_una_anotacion_no_es_un_puerto(self):
        self.assertIn(("Audited", "annotation"), self.types())

    def test_reconoce_enums(self):
        self.assertIn(("Status", "enum"), self.types())

    def test_reconoce_records(self):
        self.assertIn(("Money", "record"), self.types())

    def test_un_enum_no_se_registra_como_clase(self):
        self.assertNotIn(("Status", "class"), self.types())


class JavaCodePatternsTest(DiscoveryTestCase):
    def calls(self):
        return {(f.attributes["method"], f.attributes.get("arg")) for f in self.inventory.facts_of("java.call")}

    def test_captura_lectura_de_variables_de_entorno(self):
        self.assertIn(("getenv", "DB_HOST"), self.calls())

    def test_captura_algoritmos_criptograficos(self):
        self.assertIn(("getInstance", "MD5"), self.calls())

    def test_captura_librerias_nativas(self):
        self.assertIn(("loadLibrary", "legacycrypto"), self.calls())

    def test_captura_headers_de_gateway(self):
        self.assertIn(("getHeader", "Ocp-Apim-Subscription-Key"), self.calls())

    def test_captura_chequeos_de_rol(self):
        self.assertIn(("isUserInRole", "OPERATOR"), self.calls())

    def test_captura_shutdown_hooks(self):
        self.assertIn(("addShutdownHook", None), self.calls())

    def test_captura_codigos_de_salida(self):
        self.assertIn(("exit", None), self.calls())

    def test_captura_constructores_de_credenciales(self):
        self.assertIn("DefaultAzureCredentialBuilder", self.values("java.new", "class"))

    def test_captura_argumentos_de_anotaciones(self):
        args = {(f.attributes["name"], f.attributes["key"], f.attributes["value"]) for f in self.inventory.facts_of("java.annotation-arg")}
        self.assertIn(("Query", "nativeQuery", "true"), args)

    def test_captura_el_metodo_main(self):
        self.assertEqual(len(self.inventory.facts_of("java.entrypoint")), 1)

    def test_captura_metodos_nativos(self):
        self.assertEqual(len(self.inventory.facts_of("java.native-method")), 1)


class NonJavaSourcesTest(DiscoveryTestCase):
    def test_captura_dependencias_maven(self):
        self.assertIn("mssql-jdbc", self.values("build.dependency", "artifact"))

    def test_captura_dependencias_gradle(self):
        self.assertIn("postgresql", self.values("build.dependency", "artifact"))

    def test_captura_plugins_de_build(self):
        self.assertIn("jib-maven-plugin", self.values("build.plugin", "artifact"))

    def test_captura_instrucciones_de_dockerfile(self):
        self.assertIn("USER", self.values("container.instruction", "instruction"))

    def test_captura_objetos_de_kubernetes(self):
        self.assertIn("Deployment", self.values("manifest.object", "kind"))

    def test_captura_claves_de_kubernetes(self):
        self.assertIn("sessionAffinity", self.values("manifest.key", "key"))

    def test_captura_versiones_de_contratos(self):
        self.assertEqual(self.values("contract.spec", "spec"), {"openapi", "asyncapi"})

    def test_captura_paths_de_openapi(self):
        self.assertIn("/api/v1/orders/{id}", self.values("contract.path", "path"))

    def test_captura_objetos_sql(self):
        self.assertIn("PROCEDURE", {v.upper() for v in self.values("sql.ddl", "object")})

    def test_captura_recursos_de_terraform(self):
        self.assertIn("azurerm_storage_account", self.values("iac.resource", "type"))

    def test_captura_appenders_de_logging(self):
        self.assertIn("ch.qos.logback.core.rolling.RollingFileAppender", self.values("logging.component", "class"))

    def test_captura_pasos_de_pipeline(self):
        self.assertIn("azure/webapps-deploy@v2", self.values("pipeline.step", "action"))

    def test_captura_propiedades_yaml(self):
        self.assertIn("issuer-uri", self.values("config.property", "key"))

    def test_solo_captura_hojas_escalares_del_yaml(self):
        self.assertNotIn("jwt", self.values("config.property", "key"))


class SecretRedactionTest(DiscoveryTestCase):
    def test_ningun_secreto_se_persiste_en_texto_plano(self):
        dump = json.dumps([f.model_dump() for f in self.inventory.facts])
        self.assertEqual([s for s in PLAIN_SECRETS if s in dump], [])

    def test_registra_el_nombre_del_secreto_embebido(self):
        self.assertIn("DB_PASSWORD", self.values("secret.hardcoded", "name"))

    def test_conserva_los_placeholders(self):
        self.assertIn("${DB_USER}", self.values("config.property", "value"))


if __name__ == "__main__":
    unittest.main()
