from typing import Set

from discovery.inventory_builder import InventoryBuilder
from discovery.semgrep_runner import load_rule_criteria, run_semgrep
from models.discovery import RepositoryInventory


class DiscoveryEngine:
    """MOTOR 1 - Hallazgos.

    Recorre el repositorio UNA sola vez con las reglas de Semgrep y devuelve todo
    lo encontrado como hechos neutrales. No interpreta ni puntua nada.
    """

    def __init__(self, rules_dir: str):
        self.rules_dir = rules_dir

    def run(self, repo_path: str) -> RepositoryInventory:
        scan = run_semgrep(repo_path, self.rules_dir)
        return InventoryBuilder(repo_path).build(scan)

    def rule_criteria(self) -> Set[str]:
        """Criterios del catalogo que las reglas declaran alimentar."""
        return load_rule_criteria(self.rules_dir)
