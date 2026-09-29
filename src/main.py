import sys
import os
import shutil
import subprocess
import stat
import json

from config.loader import load_config, load_criteria
from engine.semgrep_runner import run_semgrep, load_rule_criteria
from engine.discoverer import Discoverer
from engine.classifier import Classifier
from engine.metrics import MetricsCalculator
from engine.scoring import ScoringEngine
from engine.reporting import build_discovery_report
from models.report import FinalReport

def main():
    project_config = load_config("src/portability.config.yaml")
    criteria = load_criteria("catalog/criteria.yaml")
    tech_catalog = load_config("catalog/technology.yaml")

    repo_url = project_config["repository"]["url"]
    branch = project_config["repository"].get("branch", "main")
    
    print(f"Iniciando el analisis en: {repo_url} (branch: {branch})")
    
    target_path = "./temp_repo_clonado"
    
    if os.path.exists(target_path):
        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(target_path, onerror=remove_readonly)
        
    print(f"Clonando repositorio...")
    try:
        if repo_url.startswith("http"):
            # core.longpaths evita checkouts incompletos en Windows (rutas > 260 caracteres).
            subprocess.run(["git", "-c", "core.longpaths=true", "clone", "--branch", branch, "--depth", "1", repo_url, target_path], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] No se pudo clonar el repositorio.")
        print(f"Causa posible: La rama '{branch}' no existe o el repositorio es privado/inexistente.")
        print(f"Detalle técnico: {e.stderr.decode('utf-8').strip() if e.stderr else 'Git clone failed'}")
        sys.exit(1)
    
    # Obtener el commit SHA determinista
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target_path, capture_output=True, text=True, check=True)
    commit_sha = res.stdout.strip()
    
    print("Discovery (semgrep)...")
    scan = run_semgrep(target_path, "rules")
    inventory = Discoverer(target_path).discover(scan)
    print(f"Hechos: {len(inventory.facts)} | Archivos: {len(inventory.files)} (analizados: {len(inventory.scanned_files)}) "
          f"| Componentes Java: {len(inventory.components)} | Modulos: {len(inventory.modules)}")
    for warning in inventory.scan_errors:
        print(f"  [WARN] {warning}")
    
    print("Classification...")
    classifier = Classifier(project_config.get("overrides", {}).get("module_roles", {}))
    classifier.classify(inventory.components)
            
    print("Calculando métricas...")
    metrics_calc = MetricsCalculator(
        tech_catalog,
        domain_allowed_packages=criteria["ARQ.001"].parameters.get("domain_allowed_packages", []),
    )
    metrics_by_criterion = {
        "ARQ.001": metrics_calc.calculate_arq001(inventory.components),
        "ARQ.002": metrics_calc.calculate_arq002(inventory.components),
    }
    
    print("Evaluando Scores...")
    scoring = ScoringEngine(criteria)
    report = FinalReport(
        repository_path=repo_url,
        commit_sha=commit_sha,
        evaluations=[scoring.evaluate(cid, metrics) for cid, metrics in metrics_by_criterion.items()],
    )
    
    os.makedirs("result", exist_ok=True)
    with open("result/output.json", "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=4, ensure_ascii=False)
    with open("result/discovery.json", "w", encoding="utf-8") as f:
        json.dump(build_discovery_report(inventory, repo_url, commit_sha, load_rule_criteria("rules")), f, indent=2, ensure_ascii=False)
        
    print("Analisis finalizado exitosamente. (result/output.json, result/discovery.json)")


if __name__ == "__main__":
    main()
