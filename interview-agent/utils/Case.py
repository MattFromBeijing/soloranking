from typing import Dict, Any
from utils.Phase import Phase

class Case:
    
    """
        {
            "description": "Case description here",
            "introduction": {
                "Q": "n/a",
                "R": ["Rubric item 1", "Rubric item 2"]
            },
            "phase1": {
                "Q": "Question for phase 1",
                "R": ["Rubric item 1", "Rubric item 2"]
            }
        }
    """
    
    def __init__(self, phases_data: Dict[str, Any]):
        self.phases = {}
        self.phase_order = list(phases_data.keys())
        self.case_description = phases_data.get("description", "")

        for phase_name, config in phases_data.items():
            self.phases[phase_name] = Phase(
                name=phase_name,
                question=config["Q"],
                rubric=config["R"]
            )
    
    def get_phase(self, phase_name: str) -> Phase:
        return self.phases.get(phase_name)
    
    def get_next_phase(self, current_phase: str) -> str:
        try:
            current_index = self.phase_order.index(current_phase)
            if current_index < len(self.phase_order) - 1:
                return self.phase_order[current_index + 1]
            return None  # No next phase
        except ValueError:
            return None

    def get_case_description(self) -> str:
        return self.case_description