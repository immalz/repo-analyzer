import subprocess
import json
from typing import List, Dict
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

    evidences_map: Dict[str, Evidence] = {}
    
    for finding in semgrep_data.get("results", []):
        try:
            file_path = finding.get("path", "")
            line_num = finding.get("start", {}).get("line", 0)
            matched_content = finding.get("extra", {}).get("lines", "")
            
            if matched_content == "requires login" and file_path and line_num > 0:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if line_num <= len(lines):
                            matched_content = lines[line_num - 1].strip()
                except Exception:
                    pass
            
            check_id = finding.get("check_id", "")
            
            # Deduplicacion: usar file + line + content como ID unico
            key = f"{file_path}::{line_num}::{matched_content}"
            if key in evidences_map:
                if check_id not in evidences_map[key].tags:
                    evidences_map[key].tags.append(check_id)
            else:
                evidences_map[key] = Evidence(
                    file_path=file_path,
                    line_number=line_num,
                    matched_content=matched_content,
                    tags=[check_id]
                )
        except Exception:
            continue

    return list(evidences_map.values())
