from typing import List, Dict, Tuple
from models.domain_models import Evidence, ComponentInfo, ModuleInfo
import re

class Discoverer:
    def __init__(self, target_path: str):
        self.target_path = target_path.replace("\\", "/")

    def discover(self, evidences: List[Evidence]) -> Tuple[List[ComponentInfo], List[ModuleInfo]]:
        components_map: Dict[str, ComponentInfo] = {}
        
        import os
        # 1. Escanear todo el directorio en busca de archivos .java (incluso los que no tienen imports)
        for root, dirs, files in os.walk(self.target_path):
            for file in files:
                if file.endswith(".java"):
                    full_path = os.path.join(root, file).replace("\\", "/")
                    
                    package = ""
                    package_match = re.search(r'src/main/java/(.*)/[^/]+\.java$', full_path)
                    if package_match:
                        package = package_match.group(1).replace("/", ".")
                    
                    declarations = []
                    imports = []
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if re.search(r'\binterface\s+\w+', content):
                                declarations.append("interface")
                            
                            # Extraer todos los imports nativamente
                            for match in re.finditer(r'import\s+(?:static\s+)?([a-zA-Z0-9_.*]+)\s*;', content):
                                imports.append(match.group(1))
                    except Exception:
                        pass
                    
                    components_map[full_path] = ComponentInfo(
                        file_path=full_path,
                        package=package,
                        imports=imports,
                        declarations=declarations,
                        module=""
                    )

        # 2. Enriquecer con los imports detectados por Semgrep
        for ev in evidences:
            normalized_path = ev.file_path.replace("\\", "/")
            if normalized_path in components_map:
                comp = components_map[normalized_path]
                if "java-import" in ev.tags or "cloud-vendor-sdk-import" in ev.tags:
                    import_match = re.search(r'import\s+(?:static\s+)?([a-zA-Z0-9_.*]+)\s*;', ev.matched_content)
                    if import_match:
                        comp.imports.append(import_match.group(1))

        # 3. Agrupar componentes en ModuleInfo
        modules_map: Dict[str, ModuleInfo] = {}
        
        for comp in components_map.values():
            parts = comp.file_path.split("/")
            module_name = "root"
            if "src" in parts:
                src_idx = parts.index("src")
                # parts[0] es usualmente temp_repo_clonado o similar.
                # parts[src_idx-1] seria el modulo maven si src_idx >= 2
                if src_idx >= 2 and parts[src_idx-1] != self.target_path.split("/")[-1]:
                    module_name = parts[src_idx - 1]
            
            if module_name not in modules_map:
                modules_map[module_name] = ModuleInfo(
                    name=module_name,
                    path=module_name,
                    components=[],
                    dependencies=[]
                )
            
            comp.module = module_name
            modules_map[module_name].components.append(comp.file_path)

        # 3. Determinar dependencias entre modulos
        for module in modules_map.values():
            module_deps = set()
            for comp_path in module.components:
                comp = components_map[comp_path]
                for imp in comp.imports:
                    for other_module in modules_map.values():
                        if other_module.name != module.name:
                            for other_comp_path in other_module.components:
                                other_comp = components_map[other_comp_path]
                                if other_comp.package and other_comp.package in imp:
                                    module_deps.add(other_module.name)
            module.dependencies = list(module_deps)

        return list(components_map.values()), list(modules_map.values())
