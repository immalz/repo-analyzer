import json
import os

from models.report import FinalReport


def save_results(result_dir: str, report: FinalReport, discovery_report: dict) -> None:
    """Escribe output.json (scores) y discovery.json (inventario) en `result_dir`."""
    os.makedirs(result_dir, exist_ok=True)
    _write_json(os.path.join(result_dir, "output.json"), report.model_dump(), indent=4)
    _write_json(os.path.join(result_dir, "discovery.json"), discovery_report, indent=2)


def _write_json(path: str, data, indent: int) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=indent, ensure_ascii=False)
