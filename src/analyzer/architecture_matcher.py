import re
from typing import Dict, List

class ArchitectureMatcher:

    def __init__(self, architecture_config: Dict[str, List[str]]):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        if not architecture_config:
            return
            
        for layer, patterns in architecture_config.items():
            self._compiled_patterns[layer] = [self._compile_glob(p) for p in patterns]

    def _compile_glob(self, pattern: str) -> re.Pattern:
        pattern = pattern.replace('\\', '/')
        regex = pattern.replace('.', r'\.')
        regex = regex.replace('**', '___STAR_STAR___')
        regex = regex.replace('*', r'[^/]*')
        regex = regex.replace('___STAR_STAR___', '.*')
        return re.compile(f"{regex}$")

    def identify_layer(self, file_path: str) -> str:
        normalized_path = file_path.replace('\\', '/')
        
        for layer, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(normalized_path):
                    return layer
        return "unknown"
