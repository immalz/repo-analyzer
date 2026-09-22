import sys
import os
import shutil
import subprocess
import stat
import json

from config.loader import load_config
from engine.semgrep_runner import run_semgrep
from engine.discoverer import Discoverer
from engine.classifier import Classifier
from engine.metrics import MetricsCalculator
from engine.scoring import ScoringEngine
from models.domain_models import FinalReport

def main():
    project_config = load_config("src/portability.config.yaml")
    criteria_catalog = load_config("catalog/criteria.yaml")
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
            subprocess.run(["git", "clone", "--branch", branch, "--depth", "1", repo_url, target_path], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] No se pudo clonar el repositorio.")
        print(f"Causa posible: La rama '{branch}' no existe o el repositorio es privado/inexistente.")
        print(f"Detalle técnico: {e.stderr.decode('utf-8').strip() if e.stderr else 'Git clone failed'}")
        sys.exit(1)
    
    # Obtener el commit SHA determinista
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target_path, capture_output=True, text=True, check=True)
    commit_sha = res.stdout.strip()
    
    print("Ejecutando semgrep...")
    evidences = run_semgrep(target_path, "rules/semgrep.yaml")
    print(f"¡Semgrep terminó! Se encontraron {len(evidences)} evidencias unicas.")
    
    print("Discovery...")
    discoverer = Discoverer(target_path)
    components, modules = discoverer.discover(evidences)
    print(f"Componentes encontrados: {len(components)}, Modulos lógicos: {len(modules)}")
    
    print("Classification...")
    classifier = Classifier(project_config.get("overrides", {}).get("module_roles", {}))
    classifier.classify(components)
            
    print("Calculando métricas...")
    metrics_calc = MetricsCalculator(tech_catalog)
    arq001_metrics = metrics_calc.calculate_arq001(components)
    arq002_metrics = metrics_calc.calculate_arq002(components)
    
    print("Evaluando Scores...")
    scoring = ScoringEngine(criteria_catalog)
    eval_001 = scoring.evaluate_arq001(arq001_metrics, evidences)
    eval_002 = scoring.evaluate_arq002(arq002_metrics, evidences)
    
    report = FinalReport(
        repository_path=repo_url,
        commit_sha=commit_sha,
        evaluations=[eval_001, eval_002]
    )
    
    with open("result/output.json", "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=4, ensure_ascii=False)
        
    print("Analisis finalizado exitosamente. (result/output.json)")
    
if __name__ == "__main__":
    main()