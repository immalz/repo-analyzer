from collections import Counter
from typing import Dict, Set

from models.discovery import RepositoryInventory


def build_discovery_report(inventory: RepositoryInventory, repo_url: str, commit_sha: str,
                           rule_criteria: Set[str]) -> dict:
    """Contenido de result/discovery.json: el inventario completo y que criterios tienen insumos."""
    inputs: Dict[str, Dict] = {}
    for fact in inventory.facts:
        for criterion in fact.criteria:
            entry = inputs.setdefault(criterion, {"facts": 0, "kinds": set()})
            entry["facts"] += 1
            entry["kinds"].add(fact.kind)

    return {
        "repository_path": repo_url,
        "commit_sha": commit_sha,
        "summary": {
            "files": len(inventory.files),
            "scanned_files": len(inventory.scanned_files),
            "facts": len(inventory.facts),
            "facts_by_kind": dict(sorted(Counter(f.kind for f in inventory.facts).items())),
        },
        "inputs_by_criterion": {c: {"facts": v["facts"], "kinds": sorted(v["kinds"])} for c, v in sorted(inputs.items())},
        "criteria_without_signal": sorted(rule_criteria - set(inputs)),
        "scan_errors": inventory.scan_errors,
        "modules": [m.model_dump() for m in inventory.modules],
        "components": [c.model_dump(exclude={"facts"}) for c in inventory.components],
        "files": inventory.files,
        "facts": [f.model_dump() for f in inventory.facts],
    }
