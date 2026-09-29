"""Constructores de datos de prueba compartidos por todos los tests.

Importar este modulo antes que cualquier modulo de `src/`: agrega `src/` al path.
"""
import os
import sys
from typing import Iterable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from models.discovery import ComponentInfo, Fact  # noqa: E402
from models.enums import ModuleRole  # noqa: E402

RULES_DIR = os.path.join(ROOT, "rules")
CRITERIA_FILE = os.path.join(ROOT, "catalog", "criteria.yaml")
TECHNOLOGY_FILE = os.path.join(ROOT, "catalog", "technology.yaml")
SAMPLE_APP = os.path.join(ROOT, "tests", "fixtures", "sample-app")

AZURE_BLOB = "com.azure.storage.blob.BlobClient"
TECH_CATALOG = {
    "technologies": {
        "azure_sdk": {"type": "VENDOR_SDK", "portability_class": "CLOUD_SPECIFIC", "patterns": ["com.azure"]},
    }
}


def component(path: str, role: ModuleRole, package: str,
              imports: Iterable[str] = (), interfaces: Iterable[str] = ()) -> ComponentInfo:
    """Componente Java con los hechos minimos que usan las metricas."""
    facts = [Fact(kind="java.import", file_path=path, line_number=i + 3, attributes={"name": name})
             for i, name in enumerate(imports)]
    facts += [Fact(kind="java.type", file_path=path, line_number=10, attributes={"name": name, "kind": "interface"})
              for name in interfaces]
    return ComponentInfo(file_path=path, role=role, package=package, facts=facts)


def port_component() -> ComponentInfo:
    """Capa de aplicacion con una interfaz (puerto)."""
    return component("app/OrderPort.java", ModuleRole.APPLICATION, "com.acme.app", interfaces=["OrderPort"])
