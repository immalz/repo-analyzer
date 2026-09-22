from models.domain_models import ComponentInfo, ModuleRole
from typing import List, Dict

class Classifier:
    def __init__(self, overrides: Dict[str, List[str]]):
        self.overrides = overrides or {}

    def classify(self, components: List[ComponentInfo]) -> None:
        for comp in components:
            comp.role = self._determine_role(comp)

    def _determine_role(self, comp: ComponentInfo) -> ModuleRole:
        # 1. Overrides manuales
        normalized_path = comp.file_path.replace("\\", "/")
        for role_name, patterns in self.overrides.items():
            for pattern in patterns:
                simple_pattern = pattern.replace("**", "").replace("*", "").replace("\\", "/")
                if simple_pattern and simple_pattern in normalized_path:
                    try:
                        return ModuleRole(role_name.upper())
                    except ValueError:
                        pass
        
        # 2. Heuristica por rutas (fallback)
        lower_path = normalized_path.lower()
        
        # Primero DOMINIO (el núcleo más profundo)
        if any(kw in lower_path for kw in ["/domain/", "/model/", "/entity/", "/core/"]):
            return ModuleRole.DOMAIN

        # Luego APLICACION (envuelve al dominio, incluye los puertos)
        if any(kw in lower_path for kw in ["/application/", "/service/", "/usecase/", "/port/"]):
            return ModuleRole.APPLICATION
            
        # Finalmente INFRAESTRUCTURA (lo más externo, adaptadores, controladores)
        if any(kw in lower_path for kw in ["/infrastructure/", "/adapter/", "/repository/", "/controller/", "/config/"]):
            return ModuleRole.INFRASTRUCTURE
            
        return ModuleRole.UNKNOWN
