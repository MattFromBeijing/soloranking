from typing import Dict, Any
from .Phase import Phase

class Case:
    
    """
    Case class for interview case studies.
    
    Expected format:
    {
        "case_description": "Case description text",
        "phase_order": ["phase1", "phase2"],
        "phases": {
            "phase1": {
                "name": "phase1",
                "question": "What should the company do?",
                "rubric": ["Point 1", "Point 2"]
            },
            "phase2": {
                "name": "phase2", 
                "question": "Calculate the ROI",
                "rubric": ["Shows calculation", "Gets right answer"]
            }
        }
    }
    """
    
    def __init__(self, phases_data: Dict[str, Any]):
        """
        Initialize Case with standardized format:
        {
            "case_description": "Case description text",
            "phase_order": ["phase1", "phase2"],
            "phases": {
                "phase1": {
                    "name": "phase1",
                    "question": "What should the company do?",
                    "rubric": ["Point 1", "Point 2"]
                }
            }
        }
        """
        self.phases = {}
        
        # Expect standardized format
        self.case_description = phases_data.get("case_description", "")
        self.phase_order = phases_data.get("phase_order", [])
        phases_dict = phases_data.get("phases", {})

        # Process phases (expecting "question" and "rubric" keys)
        for phase_name, config in phases_dict.items():
            self.phases[phase_name] = Phase(
                name=phase_name,
                question=config["question"],
                rubric=config["rubric"]
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Case object to dictionary for JSON serialization"""
        return {
            "case_description": self.case_description,
            "phase_order": self.phase_order,
            "phases": {
                phase_name: {
                    "name": phase.name,
                    "question": phase.question,
                    "rubric": phase.rubric
                }
                for phase_name, phase in self.phases.items()
            }
        }