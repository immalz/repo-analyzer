from typing import Dict

import yaml

from models.catalog import CriterionDefinition


def load_config(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_criteria(file_path: str) -> Dict[str, CriterionDefinition]:
    """Lee catalog/criteria.yaml y devuelve cada criterio validado, indexado por su id."""
    raw = load_config(file_path).get("criteria", {})
    return {criterion_id: CriterionDefinition(id=criterion_id, **body) for criterion_id, body in raw.items()}
