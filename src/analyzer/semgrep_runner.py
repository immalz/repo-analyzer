import subprocess
import json
from typing import List
from models.domain_models import Evidence

import sys
import os
def run_semgrep(repo_path: str, rules_path: str) -> List[Evidence]:
    semgrep_path = os.path.join(os.path.dirname(sys.executable), "semgrep.exe")
    command = [
        semgrep_path,
        "scan",
        "--json",
        "--config",
        rules_path,
        "--exclude", ".mvn",
        "--exclude", "src/test",
        "--exclude", "target",
        repo_path
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8')
        semgrep_data = json.loads(result.stdout)
    except Exception as e:
        print("ERROR en semgrep_runner:", e)
        return []

    evidences = []
    for finding in semgrep_data.get("results", []):
        try:
            file_path = finding.get("path", "")
            line_num = finding.get("start", {}).get("line", 0)
            
            # Leer el contenido real de la línea para evadir el bug de Semgrep ("requires login")
            matched_content = finding.get("extra", {}).get("lines", "")
            if matched_content == "requires login" and file_path and line_num > 0:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if line_num <= len(lines):
                            matched_content = lines[line_num - 1].strip()
                except Exception:
                    pass

            evidence = Evidence(
                check_id=finding.get("check_id", ""),
                file_path=file_path,
                line_number=line_num,
                matched_content=matched_content
            )
            evidences.append(evidence)
        except Exception:
            continue

    return evidences