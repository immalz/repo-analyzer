from models.domain_models import Arq001Metrics, Arq002Metrics, EvaluationStatus, RuleEvaluation, Evidence
from typing import Dict, List, Tuple, Any

class ScoringEngine:
    def __init__(self, criteria_catalog: Dict):
        self.criteria = criteria_catalog.get("criteria", {})

    def evaluate_arq001(self, metrics: Arq001Metrics, evidences: List[Evidence]) -> RuleEvaluation:
        score_5_rules = self.criteria.get("ARQ.001", {}).get("scores", {}).get(5, {}).get("all", [])
        score_3_rules = self.criteria.get("ARQ.001", {}).get("scores", {}).get(3, {}).get("all", [])
        score_0_rules = self.criteria.get("ARQ.001", {}).get("scores", {}).get(0, {}).get("any", [])
        
        score, status, reason = self._evaluate_generic(metrics.model_dump(), score_5_rules, score_3_rules, score_0_rules)
        
        relevant_evidences = []
        if metrics.layer_violations > 0:
            relevant_evidences.extend([e for e in evidences if "java-import" in e.tags])
        if metrics.ports_layer_present:
            relevant_evidences.extend([e for e in evidences if "java-interface-declaration" in e.tags or "java-class-implements" in e.tags])
            
        return RuleEvaluation(
            rule_id="ARQ.001",
            status=status,
            score=score,
            reason=reason,
            metrics=metrics.model_dump(),
            evidence=relevant_evidences
        )

    def evaluate_arq002(self, metrics: Arq002Metrics, evidences: List[Evidence]) -> RuleEvaluation:
        relevant_evidences = [e for e in evidences if "cloud-vendor-sdk-import" in e.tags]
            
        score_5_rules = self.criteria.get("ARQ.002", {}).get("scores", {}).get(5, {}).get("all", [])
        score_3_rules = self.criteria.get("ARQ.002", {}).get("scores", {}).get(3, {}).get("all", [])
        score_0_rules = self.criteria.get("ARQ.002", {}).get("scores", {}).get(0, {}).get("any", [])
        
        domain_leak = sum(integ.domain_leak for integ in metrics.integrations)
        encapsulation_ratio = min((integ.encapsulation_ratio for integ in metrics.integrations), default=1.0)
        
        flat_metrics = {
            "domain_leak": domain_leak,
            "encapsulation_ratio": encapsulation_ratio
        }
        cloud_specific = False
        for integ in metrics.integrations:
            if integ.portability_class == "CLOUD_SPECIFIC":
                cloud_specific = True
        flat_metrics["portability_class"] = "CLOUD_SPECIFIC" if cloud_specific else "AGNOSTIC"

        score, status, reason = self._evaluate_generic(flat_metrics, score_5_rules, score_3_rules, score_0_rules)
        
        if not metrics.integrations:
            reason = "No aplicable o cumple idealmente al ser 100% agnóstico (sin SDKs)."
            
        return RuleEvaluation(
            rule_id="ARQ.002",
            status=status,
            score=score,
            reason=reason,
            metrics=metrics.model_dump(),
            evidence=relevant_evidences
        )

    def _evaluate_generic(self, metrics_dict: Dict[str, Any], score_5_all: List[str], score_3_all: List[str], score_0_any: List[str]) -> Tuple[Any, EvaluationStatus, str]:
        def eval_condition(cond: str) -> bool:
            parts = cond.split(" ")
            if len(parts) == 3:
                var, op, val_str = parts[0], parts[1], parts[2]
                val = float(val_str) if "." in val_str else int(val_str) if val_str.isdigit() else val_str
                if val == "true": val = True
                if val == "false": val = False
                if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                    
                var_val = metrics_dict.get(var)
                if var_val is None:
                    return False
                    
                if op == "==": return var_val == val
                if op == "<": return var_val < val
                if op == "<=": return var_val <= val
                if op == ">": return var_val > val
                if op == ">=": return var_val >= val
                if op == "!=": return var_val != val
            return False

        failed_0 = [c for c in score_0_any if eval_condition(c)]
        if score_0_any and failed_0:
            return 0, EvaluationStatus.EVALUATED, f"Fallo crítico detectado: {failed_0[0]}"
            
        if score_5_all and all(eval_condition(c) for c in score_5_all):
            return 5, EvaluationStatus.EVALUATED, "Cumple todos los requisitos para nivel óptimo."
            
        if score_3_all and all(eval_condition(c) for c in score_3_all):
            failed_5 = [c for c in score_5_all if not eval_condition(c)]
            reason = f"Cumple nivel básico. No alcanza nivel óptimo por fallar en: {', '.join(failed_5)}" if failed_5 else "Cumple nivel básico."
            return 3, EvaluationStatus.EVALUATED, reason
            
        return None, EvaluationStatus.UNKNOWN, "No cumple con las reglas de evaluación configuradas."
