from typing import Dict, List, Set

from models.discovery import ComponentInfo
from models.enums import ModuleRole
from shared.java_packages import belongs_to

# Palabras en la ruta que delatan la capa, de la mas interna a la mas externa.
DOMAIN_PATH_HINTS = ["/domain/", "/model/", "/entity/", "/core/"]
APPLICATION_PATH_HINTS = ["/application/", "/service/", "/usecase/", "/port/"]
INFRASTRUCTURE_PATH_HINTS = ["/infrastructure/", "/adapter/", "/repository/", "/controller/", "/config/"]

# Mismas pistas aplicadas a los segmentos de un paquete que no pertenece a ningun componente escaneado
# (se compara segmento completo: "core" coincide con "com.acme.core", no con "com.acme.coreutils").
DOMAIN_PACKAGE_HINTS = ["domain", "model", "entity", "core"]
APPLICATION_PACKAGE_HINTS = ["application", "service", "usecase", "port"]
INFRASTRUCTURE_PACKAGE_HINTS = ["repository", "infrastructure", "adapter", "persistence", "config"]


class LayerClassifier:
    """Asigna a cada componente su capa: dominio, aplicacion o infraestructura.

    Primero usa las capas declaradas por el owner (overrides.module_roles en
    portability.config.yaml); si no hay, las deduce de los nombres de carpeta.
    """

    def __init__(self, overrides: Dict[str, List[str]]):
        self.overrides = overrides or {}

    def classify(self, components: List[ComponentInfo]) -> None:
        for comp in components:
            comp.role = self._determine_role(comp)

    def _determine_role(self, comp: ComponentInfo) -> ModuleRole:
        # Las rutas son relativas al repo; el "/" inicial permite que "/domain/" coincida en la raiz.
        normalized_path = "/" + comp.file_path.replace("\\", "/")

        # 1. Capas declaradas por el owner
        for role_name, patterns in self.overrides.items():
            for pattern in patterns:
                simple_pattern = pattern.replace("**", "").replace("*", "").replace("\\", "/")
                if simple_pattern and simple_pattern in normalized_path:
                    try:
                        return ModuleRole(role_name.upper())
                    except ValueError:
                        pass

        # 2. Deduccion por nombres de carpeta (del nucleo hacia afuera)
        lower_path = normalized_path.lower()
        if any(hint in lower_path for hint in DOMAIN_PATH_HINTS):
            return ModuleRole.DOMAIN
        if any(hint in lower_path for hint in APPLICATION_PATH_HINTS):
            return ModuleRole.APPLICATION
        if any(hint in lower_path for hint in INFRASTRUCTURE_PATH_HINTS):
            return ModuleRole.INFRASTRUCTURE
        return ModuleRole.UNKNOWN


def role_of_package(package: str, components: List[ComponentInfo]) -> ModuleRole:
    """Capa a la que pertenece un paquete importado."""
    for comp in components:
        if comp.package and belongs_to(package, [comp.package]):
            return comp.role

    # El paquete no es de ningun componente escaneado: se deduce por los nombres de sus segmentos.
    segments = _package_segments(package)
    if segments & set(DOMAIN_PACKAGE_HINTS):
        return ModuleRole.DOMAIN
    if segments & set(APPLICATION_PACKAGE_HINTS):
        return ModuleRole.APPLICATION
    if segments & set(INFRASTRUCTURE_PACKAGE_HINTS):
        return ModuleRole.INFRASTRUCTURE
    return ModuleRole.UNKNOWN


def _package_segments(name: str) -> Set[str]:
    """Segmentos de paquete de un nombre calificado, sin el nombre de la clase.

    "jakarta.persistence.Entity" -> {"jakarta", "persistence"}: en Java los paquetes
    van en minuscula y las clases empiezan con mayuscula, asi que "Entity" no cuenta.
    """
    return {segment.lower() for segment in name.split(".") if segment[:1].islower()}
