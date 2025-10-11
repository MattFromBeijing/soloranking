from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class PhaseConfig:
    question: str
    rubric: List[str]

class Case:
    def __init__(self, phases_data: Dict[str, Dict[str, Any]]):
        self.phases = {}
        self.phase_order = list(phases_data.keys())
        
        for phase_name, config in phases_data.items():
            self.phases[phase_name] = PhaseConfig(
                question=config["Q"],
                rubric=config["R"]
            )
    
    def get_phase_config(self, phase_name: str) -> PhaseConfig:
        return self.phases.get(phase_name)
    
    def get_next_phase(self, current_phase: str) -> str:
        try:
            current_index = self.phase_order.index(current_phase)
            if current_index < len(self.phase_order) - 1:
                return self.phase_order[current_index + 1]
            return None  # No next phase
        except ValueError:
            return None