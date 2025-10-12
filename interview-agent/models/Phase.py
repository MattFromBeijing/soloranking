from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Phase:
    name: str
    question: str
    rubric: List[str]