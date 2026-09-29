import os
import subprocess
from collections import defaultdict
from typing import Dict, List

from engine.semgrep_runner import SemgrepScan, EXCLUDED_PATHS
from models.discovery import ComponentInfo, ModuleInfo, RepositoryInventory


class Discoverer:
    """Construye el inventario del repositorio a partir de los hechos de Semgrep.

    No lee ni interpreta el contenido de los archivos: esa es la unica
    responsabilidad de las reglas. Aqui solo se agrupan hechos por archivo,
    componente Java y modulo.
    """

    def __init__(self, target_path: str):
        self.target_path = target_path

    def discover(self, scan: SemgrepScan) -> RepositoryInventory:
        facts_by_file = defaultdict(list)
        for fact in scan.facts:
            facts_by_file[fact.file_path].append(fact)

        components: List[ComponentInfo] = []
        for path in scan.scanned_files:
            if not path.endswith(".java"):
                continue
            file_facts = facts_by_file.get(path, [])
            package = next((f.attributes.get("name", "") for f in file_facts if f.kind == "java.package"), "")
            components.append(ComponentInfo(
                file_path=path,
                package=package,
                module=self._module_of(path),
                facts=file_facts,
            ))

        return RepositoryInventory(
            files=self._list_files(),
            scanned_files=scan.scanned_files,
            facts=scan.facts,
            components=components,
            modules=self._build_modules(components),
            scan_errors=scan.errors,
        )

    def _list_files(self) -> List[str]:
        """Inventario de archivos (incluye binarios como .jks o .so que Semgrep no lee)."""
        if os.path.isdir(os.path.join(self.target_path, ".git")):
            res = subprocess.run(["git", "ls-files"], cwd=self.target_path, capture_output=True, text=True, check=True)
            files = res.stdout.splitlines()
        else:
            files = []
            for root, dirs, names in os.walk(self.target_path):
                dirs[:] = [d for d in dirs if d != ".git"]
                rel_root = os.path.relpath(root, self.target_path)
                files += [os.path.normpath(os.path.join(rel_root, n)).replace("\\", "/") for n in names]
        return sorted(f for f in files if not any(f == p or f.startswith(p + "/") or f"/{p}/" in f for p in EXCLUDED_PATHS))

    @staticmethod
    def _module_of(path: str) -> str:
        # Modulo Maven/Gradle = carpeta que contiene src/ (p.ej. "adapter/src/main/java/...").
        parts = path.split("/")
        if "src" in parts and parts.index("src") >= 1:
            return parts[parts.index("src") - 1]
        return "root"

    @staticmethod
    def _build_modules(components: List[ComponentInfo]) -> List[ModuleInfo]:
        modules: Dict[str, ModuleInfo] = {}
        for comp in components:
            modules.setdefault(comp.module, ModuleInfo(name=comp.module, path=comp.module)).components.append(comp.file_path)

        packages_by_module = {name: {c.package for c in components if c.module == name and c.package} for name in modules}
        for module in modules.values():
            deps = set()
            for comp in components:
                if comp.module != module.name:
                    continue
                for imp in comp.imports:
                    for other, packages in packages_by_module.items():
                        if other != module.name and any(imp == p or imp.startswith(p + ".") for p in packages):
                            deps.add(other)
            module.dependencies = sorted(deps)
        return list(modules.values())
