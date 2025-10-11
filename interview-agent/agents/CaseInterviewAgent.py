import logging
from typing import Dict, Any, Optional
from livekit.agents.llm import function_tool, RunContext
from livekit.agents import Agent
from services.RAGService import RAGService
from utils.phases import Case, PhaseConfig
import json
import openai

logger = logging.getLogger("case-interview-agent")

class CaseInterviewAgent(Agent):
    def __init__(self, case_id: str, vs_dir: str, phases_data: Dict[str, Dict[str, Any]]):
        self.case_id = case_id
        self.rag_service = RAGService(vs_dir)
        self.case = Case(phases_data)
        self.openai_client = openai.OpenAI()
        
        # State tracking
        self.current_phase = self.case.phase_order[0]  # Start with first phase
        self.evaluation_history = {}
        self.conversation_context = []
        
        super().__init__(
            instructions=self._get_current_instructions()
        )

    def _get_current_instructions(self) -> str:
        """Generate instructions based on current phase"""
        phase_config = self.case.get_phase_config(self.current_phase)
        if not phase_config:
            return "Conduct the interview professionally."
            
        # make sure the bot knows to draws from the RAG service for case facts
        return (f"""You are conducting a case interview. Current phase: {self.current_phase}

                    QUESTION TO ADDRESS: {phase_config.question}

                    Your role: Based on the case facts, guide the candidate through this question. After they respond, you will:
                    1. Evaluate their response against the rubric
                    2. Either advance to next phase OR provide coaching to improve their answer
                    3. Generate an appropriate prompt based on the evaluation
                    4. Use the RAG service to retrieve relevant case facts as needed to inform your evaluation and coaching. Do not reveal case facts to the candidate unless the case fact is allowed to be revealed and only when the candidate asks for it.

                    Be conversational and supportive while maintaining professional standards."""
                )

    # STEP 1: EVALUATION
    @function_tool
    async def evaluate_response(self, context: RunContext, user_response: str) -> str:
        """Evaluate user's response against current phase rubric using case facts"""
        try:
            phase_config = self.case.get_phase_config(self.current_phase)
            if not phase_config:
                return "No evaluation criteria available."

            # Get relevant case facts
            case_facts = await self._get_relevant_case_facts(user_response)
            
            # Build structured evaluation prompt
            evaluation_prompt = (f"""You are an expert case interview evaluator. Evaluate this candidate's response objectively.

            PHASE: {self.current_phase}
            QUESTION: {phase_config.question}

            CANDIDATE RESPONSE:
            {user_response}

            EVALUATION CRITERIA:
            {chr(10).join(f"{i+1}. {criterion}" for i, criterion in enumerate(phase_config.rubric))}

            RELEVANT CASE FACTS:
            {case_facts}

            INSTRUCTIONS:
            - Evaluate against EACH criterion (1-10 scale)
            - Overall score = average of criterion scores
            - Threshold to advance = 8.0 or higher
            - Be objective but constructive

            REQUIRED JSON OUTPUT:
            {{
                "criterion_scores": {{"criterion_1": score, "criterion_2": score, ...}},
                "overall_score": average_score,
                "should_advance": boolean,
                "strengths": ["strength1", "strength2"],
                "improvement_areas": ["area1", "area2"],
                "specific_feedback": "Detailed feedback for the candidate"
            }}""")

            # Call LLM for evaluation
            eval_response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are an expert case interview evaluator. Provide detailed, objective evaluations in the specified JSON format."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )
            
            # Parse JSON response
            try:
                evaluation_data = json.loads(eval_response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                evaluation_data = {
                    "criterion_scores": {},
                    "overall_score": 5.0,
                    "should_advance": False,
                    "strengths": ["Attempted to answer the question"],
                    "improvement_areas": ["Response needs more development"],
                    "specific_feedback": "Unable to parse detailed evaluation."
                }
            
            # Store detailed evaluation
            evaluation = {
                "response": user_response,
                "phase": self.current_phase,
                "criterion_scores": evaluation_data.get("criterion_scores", {}),
                "overall_score": evaluation_data.get("overall_score", 5.0),
                "should_advance": evaluation_data.get("should_advance", False),
                "strengths": evaluation_data.get("strengths", []),
                "improvement_areas": evaluation_data.get("improvement_areas", []),
                "specific_feedback": evaluation_data.get("specific_feedback", ""),
                "case_facts_used": case_facts,
                "timestamp": context.current_time if hasattr(context, 'current_time') else "now"
            }
            
            self.evaluation_history[self.current_phase] = evaluation
            
            logger.info(f"Evaluation complete for {self.current_phase}: Score {evaluation['overall_score']}/10")
            
            return f"Evaluation complete. Overall score: {evaluation['overall_score']:.1f}/10. {'Advancing' if evaluation['should_advance'] else 'Coaching needed'}."
            
        except Exception as e:
            logger.error(f"Error in evaluation: {e}")
            return "Unable to evaluate response."

    # STEP 2: DECISION LOGIC  
    @function_tool
    async def decide_next_action(self, context: RunContext) -> str:
        """Decide whether to advance phase or stay and coach"""
        try:
            evaluation = self.evaluation_history.get(self.current_phase)
            if not evaluation:
                return "No evaluation available for decision."
            
            if evaluation["should_advance"]:
                # Move to next phase
                next_phase = self.case.get_next_phase(self.current_phase)
                if next_phase:
                    self.current_phase = next_phase
                    return f"ADVANCE: Moving to {self.current_phase}"
                else:
                    return "COMPLETE: Interview finished"
            else:
                # Stay in current phase and coach
                return f"COACH: Stay in {self.current_phase} and provide guidance"
                
        except Exception as e:
            logger.error(f"Error in decision making: {e}")
            return "Unable to make decision."

    # STEP 3: PROMPT GENERATION
    @function_tool
    async def generate_response_prompt(self, context: RunContext, action: str) -> str:
        """Generate appropriate prompt based on decision"""
        try:
            evaluation = self.evaluation_history.get(self.current_phase)
            
            if action.startswith("ADVANCE"):
                # Generate next phase introduction
                phase_config = self.case.get_phase_config(self.current_phase)
                return (f"""Great work on that section! Let's move to the next part.

                        {phase_config.question}

                        Take your time to think through this.""")

            elif action.startswith("COACH"):
                # Generate coaching prompt based on gaps
                improvement_areas = evaluation.get("improvement_areas", [])
                specific_feedback = evaluation.get("specific_feedback", "")
                
                coaching_areas = "\n".join(f"- {area}" for area in improvement_areas)
                
                return (f"""That's a good start! {specific_feedback}

                        To strengthen your response, consider:
                        {coaching_areas}

                        Would you like to refine your approach to this question?""")

            elif action.startswith("COMPLETE"):
                return "Excellent work! You've completed the case interview. Let me provide some feedback on your performance."
                
            return "Let's continue with the interview."
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            return "Let's continue with the next part of the interview."

    async def _get_relevant_case_facts(self, query: str) -> str:
        """Helper to retrieve case facts relevant to the query"""
        try:
            chunks = self.rag_service.search(self.case_id, query, k=3)
            if chunks:
                return "\n".join([getattr(chunk, 'text', str(chunk)) for chunk in chunks])
            else:
                return "No relevant case facts found."
        except Exception as e:
            logger.error(f"Error retrieving case facts: {e}")
            return "Case facts unavailable."