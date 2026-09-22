import subprocess
import json
import os
import shutil
import stat
from analyzer.semgrep_runner import run_semgrep
from config.loader import load_config
from analyzer.architecture_matcher import ArchitectureMatcher
from analyzer.evaluator import Evaluator
from models.domain_models import FinalReport

def main():
    # lectura de archivo de configuracion
    project_config = load_config("src/portability.config.yaml")
    repo_url = project_config["repository"]["url"]
    print(f"Iniciando el analisis en: {repo_url}")

    repo_url_clean = repo_url.lstrip("/")
    
    # dependiendo si la ruta que se configuro es una carpeta local o una url de algun repositorio
    if os.path.isdir(repo_url_clean) or repo_url_clean == "temp_repo_clonado":
        target_path = repo_url
        print("El config apunta a un directorio local. Saltando clonación...")
    else:
        target_path = "./temp_repo_clonado"
        print(f"Clonando repositorio desde {repo_url}...")
        
        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
            
        if os.path.exists(target_path):
            shutil.rmtree(target_path, onerror=remove_readonly)
            
        subprocess.run(["git", "clone", repo_url, target_path], check=True)

    print(f"Iniciando el analisis en: {target_path}")
    print("Ejecutando semgrep...")

    evidences = run_semgrep(target_path, "rules/semgrep.yaml")
    
    print(f"¡Semgrep terminó! Se encontraron {len(evidences)} evidencias.")
    
    matcher = ArchitectureMatcher(project_config.get("architecture", {}))
    for evi in evidences:
        evi.layer = matcher.identify_layer(evi.file_path)

    
    evaluator = Evaluator(project_config)
    evaluations = evaluator.evaluate_all(evidences)
        
    report = FinalReport(
        repository_path=target_path,
        evaluations=evaluations
    )
    
    os.makedirs("result", exist_ok=True)
    with open("result/output.json", "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=4))
        
    print("Reporte final guardado exitosamente en result/output.json")

if __name__ == '__main__':
    main()