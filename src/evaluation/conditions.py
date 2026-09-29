"""Evaluador de las condiciones declaradas en catalog/criteria.yaml.

Formato: `<metrica> <operador> <valor>`, por ejemplo:
    layer_violations <= 5
    ports_layer_present == true
    portability_class != "CLOUD_SPECIFIC"
"""
import operator
import re
from typing import Any, Dict

OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
}

# Los operadores de dos caracteres van primero para que "<=" no se lea como "<".
CONDITION = re.compile(r"^\s*(?P<metric>\w+)\s*(?P<op>==|!=|<=|>=|<|>)\s*(?P<value>.+?)\s*$")


def evaluate_condition(condition: str, values: Dict[str, Any]) -> bool:
    """True si la condicion se cumple. Una metrica ausente nunca cumple la condicion."""
    match = CONDITION.match(condition)
    if not match:
        raise ValueError(f"Condicion invalida en el catalogo: '{condition}'")

    actual = values.get(match["metric"])
    if actual is None:
        return False
    return OPERATORS[match["op"]](actual, _parse_value(match["value"]))


def _parse_value(text: str) -> Any:
    if text in ("true", "false"):
        return text == "true"
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text
