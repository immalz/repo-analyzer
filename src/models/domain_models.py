from pydantic import BaseModel;
from typing import List, Dict;

# todo lo que vaya aqui representara los hallazgos que haga semgrep en el codigo.
class Evidence(BaseModel):
    check_id: str;
    file_path: str;
    line_number: int;
    matched_content: str;

# segun las reglas que se implementen, esta zona representa el veredicto para cada una.
class RuleEvaluation(BaseModel):
    rule_id: str;
    score: int;
    metrics: Dict[str, int | float | bool];
    evidence: List[Evidence];

class FinalReport(BaseModel):
    repository_path: str;
    evaluations: List[RuleEvaluation];
    
    