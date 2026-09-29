import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, NamedTuple, Optional, Set

import yaml

from models.discovery import Fact

# Rutas que no forman parte del artefacto productivo.
EXCLUDED_PATHS = ["src/test", "target", "build", ".mvn", ".gradle", ".git", ".idea", "node_modules"]

# Claves cuyo valor literal nunca se persiste (condicion N3: nombres y referencias, nunca valores).
SENSITIVE_KEY = re.compile(r"(?i)(passw|pwd|secret|token|api[_-]?key|credential|private[_-]?key|access[_-]?key|"
                           r"account[_-]?key|client[_-]?secret|connection[_-]?string|sas)")
PLACEHOLDER = re.compile(r"^\s*(\$\{.*\}|#\{.*\}|\$\(.*\)|\{\{.*\}\})\s*$")
INLINE_CREDENTIAL = re.compile(r"(?i)\b(password|pwd|accountkey|sharedaccesskey|sharedaccesssignature|secret|token)=([^;&\s\"']+)")
URL_USERINFO = re.compile(r"(://[^/:@\s]+):([^@/\s]+)@")
UNBOUND_METAVARIABLE = re.compile(r"^\$[A-Z_][A-Z0-9_]*$")


class SemgrepScan(NamedTuple):
    facts: List[Fact]
    scanned_files: List[str]
    errors: List[str]


def run_semgrep(repo_path: str, rules_dir: str) -> SemgrepScan:
    command = [
        _semgrep_executable(), "scan",
        "--json", "--metrics=off", "--disable-version-check",
        # Fuerza modo sin VCS: ignora .gitignore y calcula los ignores relativos al repo analizado.
        "--project-root", ".",
        "--config", os.path.abspath(rules_dir),
    ]
    for path in EXCLUDED_PATHS:
        command += ["--exclude", path]
    command.append(".")

    result = subprocess.run(command, cwd=repo_path, capture_output=True, text=True, encoding="utf-8", check=False)
    try:
        semgrep_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Semgrep no devolvio JSON (exit {result.returncode}): {result.stderr.strip()[-1000:]}")

    fatal = [e for e in semgrep_data.get("errors", []) if e.get("level") == "error"]
    if fatal:
        raise RuntimeError("Semgrep reporto errores de configuracion: " + "; ".join(e.get("message", "")[:300] for e in fatal))

    facts: List[Fact] = []
    seen: Set[tuple] = set()
    for finding in semgrep_data.get("results", []):
        fact = _to_fact(finding)
        if fact is None:
            continue
        key = (fact.rule_id, fact.file_path, fact.line_number, tuple(sorted(fact.attributes.items())))
        if key not in seen:
            seen.add(key)
            facts.append(fact)

    scanned = sorted(_normalize_path(p) for p in semgrep_data.get("paths", {}).get("scanned", []))
    warnings = [f"{e.get('type', '')}: {e.get('message', '')[:300]}" for e in semgrep_data.get("errors", [])]
    return SemgrepScan(facts=facts, scanned_files=scanned, errors=warnings)


def load_rule_criteria(rules_dir: str) -> Set[str]:
    """Criterios del catalogo que al menos una regla declara alimentar."""
    criteria: Set[str] = set()
    for name in os.listdir(rules_dir):
        if name.endswith((".yaml", ".yml")):
            with open(os.path.join(rules_dir, name), encoding="utf-8") as f:
                for rule in (yaml.safe_load(f) or {}).get("rules", []):
                    criteria.update(rule.get("metadata", {}).get("criteria", []))
    return criteria


def _semgrep_executable() -> str:
    for candidate in ("semgrep.exe", "semgrep"):
        local = os.path.join(os.path.dirname(sys.executable), candidate)
        if os.path.isfile(local):
            return local
    found = shutil.which("semgrep")
    if not found:
        raise RuntimeError("No se encontro el ejecutable de semgrep (pip install -r requirements.txt).")
    return found


def _to_fact(finding: Dict) -> Optional[Fact]:
    extra = finding.get("extra", {})
    metadata = extra.get("metadata", {})
    kind = metadata.get("fact")
    if not kind:
        return None

    # Sin sesion iniciada Semgrep oculta `lines` y `metavars`; los valores capturados
    # llegan interpolados en `message`, en el orden declarado en metadata.fields.
    fields: List[str] = metadata.get("fields", [])
    values = extra.get("message", "").split("|", max(len(fields) - 1, 0)) if fields else []
    attributes: Dict[str, str] = {}
    for field, value in zip(fields, values):
        value = _unquote(value.strip())
        if value and not UNBOUND_METAVARIABLE.match(value):
            attributes[field] = value
    for key, value in metadata.items():
        if key not in ("fact", "fields", "criteria") and isinstance(value, (str, int, float, bool)):
            attributes.setdefault(key, str(value))

    return Fact(
        kind=kind,
        file_path=_normalize_path(finding.get("path", "")),
        line_number=finding.get("start", {}).get("line", 0),
        attributes=_redact(kind, attributes),
        criteria=list(metadata.get("criteria", [])),
        rule_id=finding.get("check_id", "").rsplit(".", 1)[-1],
    )


def _redact(kind: str, attributes: Dict[str, str]) -> Dict[str, str]:
    key = attributes.get("key") or attributes.get("name") or ""
    value = attributes.get("value")
    if kind in ("config.property", "manifest.env") and value is not None and SENSITIVE_KEY.search(key):
        attributes["value"] = _hash_literal(value)
    if kind == "container.instruction" and attributes.get("instruction", "").upper() in ("ENV", "ARG"):
        attributes["args"] = re.sub(
            r"([\w.\-]+)=(\"[^\"]*\"|'[^']*'|\S+)",
            lambda m: f"{m.group(1)}={_hash_literal(m.group(2)) if SENSITIVE_KEY.search(m.group(1)) else m.group(2)}",
            attributes.get("args", ""),
        )
    for field, text in attributes.items():
        text = INLINE_CREDENTIAL.sub(lambda m: f"{m.group(1)}={_hash_literal(m.group(2))}", text)
        attributes[field] = URL_USERINFO.sub(lambda m: f"{m.group(1)}:{_hash_literal(m.group(2))}@", text)
    return attributes


def _hash_literal(value: str) -> str:
    if PLACEHOLDER.match(value) or value.startswith("sha256:") or not value.strip():
        return value
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _normalize_path(path: str) -> str:
    path = path.replace("\\", "/")
    return path[2:] if path.startswith("./") else path
