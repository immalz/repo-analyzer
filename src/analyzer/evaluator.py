from typing import List, Dict
from models.domain_models import Evidence, RuleEvaluation

class Evaluator:
    """
    Motor principal de evaluación. Procesa las evidencias crudas de Semgrep
    y aplica la lógica de arquitectura para calcular un veredicto (score).
    """
    def __init__(self, project_config: Dict):
        self.config = project_config

    def evaluate_all(self, evidences: List[Evidence]) -> List[RuleEvaluation]:
        """
        Evalúa todas las evidencias agrupándolas por regla.
        """
        evidences_by_rule: Dict[str, List[Evidence]] = {}
        for evi in evidences:
            evidences_by_rule.setdefault(evi.check_id, []).append(evi)
            
        evaluations = []
        for raw_rule_id, rule_evidences in evidences_by_rule.items():
            rule_id = raw_rule_id.replace("rules.", "")
            if rule_id == "arq-001-detect-internal-import":
                evaluations.append(self._evaluate_internal_import(rule_id, rule_evidences))
            elif rule_id == "arq-002-detect-vendor-sdk":
                evaluations.append(self._evaluate_vendor_sdk(rule_id, rule_evidences))
            else:
                evaluations.append(self._generic_evaluation(rule_id, rule_evidences))
                
        return evaluations

    def _evaluate_internal_import(self, rule_id: str, evidences: List[Evidence]) -> RuleEvaluation:
        """
        Criterios para Arquitectura Hexagonal:
        - Domain: NO debe importar 'application', 'infrastructure', 'adapter', 'controller'.
        - Application: NO debe importar 'infrastructure', 'adapter', 'controller'.
        """
        violations = []
        for evi in evidences:
            content = evi.matched_content.lower()
            is_violation = False
            
            if evi.layer == "domain":
                # En CRUD, 'repository' equivale a infra/DB. 'persistence' o 'spring' ensucian el dominio.
                if any(kw in content for kw in ["application", "infrastructure", "adapter", "controller", "repository", "persistence", "spring", "service"]):
                    is_violation = True
            elif evi.layer == "application":
                if any(kw in content for kw in ["infrastructure", "adapter", "controller", "repository"]):
                    is_violation = True
                    
            if is_violation:
                violations.append(evi)
                
        # Penalidad: -10 puntos por cada violación. Parte de un puntaje ideal de 100.
        score = 100 - (len(violations) * 10)
        score = max(0, score)
        
        return RuleEvaluation(
            rule_id=rule_id,
            score=score,
            metrics={"total_hallazgos": len(evidences), "violaciones_arquitectonicas": len(violations)},
            evidence=violations # Filtramos para que el reporte solo muestre violaciones reales
        )

    def _evaluate_vendor_sdk(self, rule_id: str, evidences: List[Evidence]) -> RuleEvaluation:
        """
        Criterios de Portabilidad/Vendor Lock-in:
        - SDKs de proveedores Cloud (AWS, GCP, Azure) no deberían contaminar el Dominio.
        - Se penalizan fuertemente si están en 'domain' o 'application'.
        """
        violations = []
        for evi in evidences:
            # Sólo permitimos SDKs explícitamente en la capa de infrastructure
            if evi.layer in ["domain", "application", "unknown"]:
                violations.append(evi)
                
        score = 100 - (len(violations) * 20) # Penalidad más fuerte (-20)
        score = max(0, score)
        
        return RuleEvaluation(
            rule_id=rule_id,
            score=score,
            metrics={"total_hallazgos": len(evidences), "violaciones_arquitectonicas": len(violations)},
            evidence=violations
        )

    def _generic_evaluation(self, rule_id: str, evidences: List[Evidence]) -> RuleEvaluation:
        """Evaluación por defecto para reglas desconocidas."""
        return RuleEvaluation(
            rule_id=rule_id,
            score=0,
            metrics={"total_hallazgos": len(evidences)},
            evidence=evidences
        )
