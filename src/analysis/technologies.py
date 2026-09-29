from typing import List, Optional

from models.technology import TechnologyDefinition


class TechnologyMatcher:
    """Identifica a que tecnologia del catalogo pertenece un import."""

    def __init__(self, technologies: List[TechnologyDefinition]):
        self.technologies = technologies

    def identify(self, import_name: str) -> Optional[TechnologyDefinition]:
        for technology in self.technologies:
            if any(import_name.startswith(pattern) for pattern in technology.patterns):
                return technology
        return None
