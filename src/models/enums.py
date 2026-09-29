from enum import Enum


class EvaluationStatus(str, Enum):
    EVALUATED = "EVALUATED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ModuleRole(str, Enum):
    DOMAIN = "DOMAIN"
    APPLICATION = "APPLICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    UNKNOWN = "UNKNOWN"


class TechClass(str, Enum):
    """Valores de `type` en catalog/technology.yaml."""
    VENDOR_SDK = "VENDOR_SDK"


class PortabilityClass(str, Enum):
    """Valores de `portability_class` en catalog/technology.yaml."""
    CLOUD_SPECIFIC = "CLOUD_SPECIFIC"
    AGNOSTIC = "AGNOSTIC"
