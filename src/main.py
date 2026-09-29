"""Punto de entrada: revisa el repositorio configurado en src/portability.config.yaml.

Flujo:  clonar -> MOTOR 1 Hallazgos -> MOTOR 2 Analisis -> MOTOR 3 Evaluacion -> resultados
"""
import sys

from analysis.engine import AnalysisEngine
from config.loader import load_config, load_criteria, load_technologies
from discovery.engine import DiscoveryEngine
from evaluation.engine import EvaluationEngine
from models.report import FinalReport
from reporting.discovery_report import build_discovery_report
from reporting.writer import save_results
from repository.git_repository import RepositoryCloneError, clone_repository

CONFIG_FILE = "src/portability.config.yaml"
CRITERIA_FILE = "catalog/criteria.yaml"
TECHNOLOGY_FILE = "catalog/technology.yaml"
RULES_DIR = "rules"
CLONE_DIR = "./temp_repo_clonado"
RESULT_DIR = "result"


def main():
    config = load_config(CONFIG_FILE)
    criteria = load_criteria(CRITERIA_FILE)
    technologies = load_technologies(TECHNOLOGY_FILE)
    repo_url = config["repository"]["url"]
    branch = config["repository"].get("branch", "main")

    print(f"Iniciando el analisis en: {repo_url} (rama: {branch})")
    print("Clonando repositorio...")
    try:
        commit_sha = clone_repository(repo_url, branch, CLONE_DIR)
    except RepositoryCloneError as error:
        print("\n[ERROR] No se pudo clonar el repositorio.")
        print(f"Causa posible: la rama '{branch}' no existe o el repositorio es privado/inexistente.")
        print(f"Detalle tecnico: {error}")
        sys.exit(1)

    print("Motor 1 - Hallazgos (Semgrep)...")
    discovery = DiscoveryEngine(RULES_DIR)
    inventory = discovery.run(CLONE_DIR)
    print(f"  Hechos: {len(inventory.facts)} | Archivos: {len(inventory.files)} (analizados: {len(inventory.scanned_files)}) "
          f"| Componentes Java: {len(inventory.components)} | Modulos: {len(inventory.modules)}")
    for warning in inventory.scan_errors:
        print(f"  [WARN] {warning}")

    print("Motor 2 - Analisis...")
    layer_overrides = config.get("overrides", {}).get("module_roles", {})
    metrics_by_criterion = AnalysisEngine(criteria, technologies, layer_overrides).run(inventory)

    print("Motor 3 - Evaluacion...")
    evaluations = EvaluationEngine(criteria).run(metrics_by_criterion)

    report = FinalReport(repository_path=repo_url, commit_sha=commit_sha, evaluations=evaluations)
    discovery_report = build_discovery_report(inventory, repo_url, commit_sha, discovery.rule_criteria())
    save_results(RESULT_DIR, report, discovery_report)
    print(f"Analisis finalizado. Resultados en {RESULT_DIR}/output.json y {RESULT_DIR}/discovery.json")


if __name__ == "__main__":
    main()
