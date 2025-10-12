import logging
from typing import Dict, Any
from livekit.agents.llm import function_tool
from livekit.agents import Agent
from services.RAGService import RAGService
from models.Case import Case
import json
import openai
from datetime import datetime

logger = logging.getLogger("case-agent")

class CaseAgent(Agent):
    def __init__(self, case_id: str, vs_dir: str, case_data: Dict[str, Dict[str, Any]]):
        self.case_id = case_id
        self.rag_service = RAGService(vs_dir)
        self.case = Case(case_data)
        self.openai_client = openai.OpenAI()
        
        # State tracking
        self.current_phase = self.case.phase_order[0]  # Start with first phase
        self.evaluation_history = {}
        self.conversation_context = []
        
        super().__init__(
            instructions=self._get_initial_instructions()
        )
        
########## Context Tool Functions ##########

    @function_tool
    async def evaluate_response(self, user_response: str) -> str:
        """Evaluate user's response against current phase rubric using case facts"""
        try:
            phase = self.case.get_phase(self.current_phase)
            if not phase:
                return "No evaluation criteria available."

            # Get relevant case facts
            case_facts = await self.get_relevant_case_facts(user_response)
            
            # Build structured evaluation prompt
            evaluation_prompt = (f"""You are an expert case interview evaluator. Evaluate this candidate's response objectively.

            PHASE: {self.current_phase}
            QUESTION: {phase.question}

            CANDIDATE RESPONSE:
            {user_response}

            EVALUATION CRITERIA:
            {chr(10).join(f"{i+1}. {criterion}" for i, criterion in enumerate(phase.rubric))}

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
                "timestamp": datetime.now().isoformat()
            }
            
            self.evaluation_history[self.current_phase] = evaluation
            
            logger.info(f"Evaluation complete for {self.current_phase}: Score {evaluation['overall_score']}/10")
            
            return f"Evaluation complete. Overall score: {evaluation['overall_score']:.1f}/10. {'Advancing' if evaluation['should_advance'] else 'Coaching needed'}."
            
        except Exception as e:
            return self._handle_error(f"Error in evaluation: {e}")
        
    @function_tool
    async def get_relevant_case_facts(self, query: str) -> str:
        """Helper to retrieve case facts relevant to the query"""
        try:
            chunks = self.rag_service.search(self.case_id, query, k=3)
            if chunks:
                return "\n".join([getattr(chunk, 'text', str(chunk)) for chunk in chunks])
            else:
                return "No relevant case facts found."
        except Exception as e:
            return self._handle_error(f"Error retrieving case facts: {e}")

    @function_tool
    async def provide_coaching(self) -> str:
        """Provide coaching feedback without advancing phase"""
        try:
            evaluation = self.evaluation_history.get(self.current_phase)
            if not evaluation:
                return "No evaluation available for coaching."
            
            # Get relevant case facts to understand the optimal direction
            user_response = evaluation.get("response", "")
            case_facts = evaluation.get("case_facts_used", "")
            phase = self.case.get_phase(self.current_phase)
            
            # Build coaching prompt to identify gaps and redirect without revealing answers
            coaching_prompt = (f"""You are an expert case interview coach. The candidate's response needs improvement.

            CURRENT PHASE: {self.current_phase}
            QUESTION: {phase.question}

            CANDIDATE'S RESPONSE:
            {user_response}
            
            RELEVANT CASE FACTS (DO NOT REVEAL TO CANDIDATE):
            {case_facts}
            
            EVALUATION RESULTS:
            - Strengths: {evaluation.get('strengths', [])}
            - Areas for improvement: {evaluation.get('improvement_areas', [])}
            - Specific feedback: {evaluation.get('specific_feedback', '')}
            
            COACHING INSTRUCTIONS:
            - Guide the candidate toward the correct analytical direction
            - Ask leading questions that help them discover the right approach
            - Suggest frameworks or thinking methods (not specific answers)
            - Encourage them to consider aspects they might have missed
            - DO NOT reveal case facts or give direct answers
            - BE encouraging but redirect their thinking
            
            REQUIRED JSON OUTPUT:
            {{
                "coaching_message": "Encouraging message with strategic redirection",
                "leading_questions": ["question1", "question2"],
                "areas_to_explore": ["area1", "area2"],
                "encouragement": "Positive reinforcement message"
            }}""")

            # Get coaching guidance from LLM
            coaching_response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are an expert case interview coach. Provide strategic guidance that redirects thinking without revealing answers."},
                    {"role": "user", "content": coaching_prompt}
                ]
            )
            
            try:
                coaching_data = json.loads(coaching_response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback coaching
                coaching_data = {
                    "coaching_message": "That's a good start! Let's refine your approach.",
                    "leading_questions": ["What other factors might be important to consider?"],
                    "areas_to_explore": ["Market dynamics", "Financial implications"],
                    "encouragement": "You're on the right track - keep building on your analysis!"
                }
            
            # Format the coaching response for the candidate
            leading_questions = "\n".join(f"- {q}" for q in coaching_data.get("leading_questions", []))
            areas = "\n".join(f"- {area}" for area in coaching_data.get("areas_to_explore", []))
            coaching_message = coaching_data.get("coaching_message", "That's a good start!")
            encouragement = coaching_data.get("encouragement", "Keep thinking through this!")

            return (f"""coaching_message: {coaching_message}
                        leading_questions: {leading_questions}
                        areas_to_explore: {areas}
                        encouragement: {encouragement}""")

        except Exception as e:
            return self._handle_error(f"Error providing coaching: {e}")
        
########## State Transition Tool Functions ##########

    @function_tool
    async def decide_next_action(self) -> None:
        """Decide whether to advance phase or stay and coach, then execute the action"""
        try:
            evaluation = self.evaluation_history.get(self.current_phase)
            if not evaluation:
                return "No evaluation available for decision."
            
            if evaluation["should_advance"]:
                # Check if there's a next phase
                next_phase = self.case.get_next_phase(self.current_phase)
                if next_phase:
                    await self.advance_to_next_phase()
                else:
                    await self.end_interview()

        except Exception as e:
            self._handle_error(f"Error in decision making: {e}")

    @function_tool
    async def advance_to_next_phase(self) -> None:
        """Advance to next phase and update agent instructions"""
        try:
            evaluation = self.evaluation_history.get(self.current_phase)
            if not evaluation or not evaluation.get("should_advance", False):
                self._handle_error(f"Error advancing phase: {'past evaluation does not support advancement'}")
            
            # Move to next phase
            next_phase = self.case.get_next_phase(self.current_phase)
            if next_phase:
                self.current_phase = next_phase
                # Update agent instructions for new phase
                new_instructions = self._get_phase_instructions()
                self.instructions = new_instructions
            else:
                self._handle_error(f"Error advancing phase: {'no next phase available'}")
                
        except Exception as e:
            self._handle_error(f"Error advancing phase: {e}")
        
    @function_tool
    async def end_interview(self) -> None:
        """End the interview session"""
        try:
            self.current_phase = None
            self.instructions = "The interview has concluded. Thank the user for their participation and end the session."
        except Exception as e:
            self._handle_error(f"Error ending interview: {e}")

########## Helper Methods ##########

    def _get_initial_instructions(self) -> str:
        """Initial instructions for the agent"""
        return (f"""You are conducting a case interview. Current phase: INTRODUCTION.

                Begin by reading the case description: {self.case.get_case_description()}.

                After reading the case description, you will:
                1. Answer claraifying questions the candidate may have about the case facts that can be answered directly by case facts that are allowed to be revealed by searching for case facts using the get_relevant_case_facts tool.

                Once the candidate is ready, you will proceed to the first phase: {self.current_phase} by using the advance_to_next_phase tool.

                Be conversational and supportive while maintaining professional standards.""")
        
    def _get_phase_instructions(self) -> str:
        """Generate instructions based on current phase"""
        phase = self.case.get_phase(self.current_phase)
        if not phase:
            return "Conduct the interview professionally."
            
        # make sure the bot knows to draws from the RAG service for case facts
        return (f"""You are conducting a case interview. Current phase: {self.current_phase}

                    QUESTION TO ADDRESS: {phase.question}
                    
                    You will begin by:
                    1. Prompt the candidate with the question to address.
                    
                    Before they give a full response, you will:
                    1. Answer questions that the candidate asks that can be answered directly by case facts that are allowed to be revealed by searching for case facts using the get_relevant_case_facts tool.
                    
                    After they respond, you will:
                    1. Use the evaluate_response tool to evaluate the user's response.
                    2. Use the decide_next_steps tool to either advance to next phase OR remain in the current phase and provide guidance using provide_coaching such that their answers align with the rubric without directly giving them answers or revealing case facts that are not allowed to be revealed.
                    3. Use the get_relevant_case_facts tool to retrieve relevant case facts as needed to inform your evaluation and coaching.

                    Be conversational and supportive while maintaining professional standards."""
                )

    def _handle_error(self, error_message: str) -> str:
        """Handle unexpected errors gracefully"""
        logger.error(f"Agent encountered an error: {error_message}")
        self.current_phase = None
        self.instructions = "The interview has concluded due to an error. Please inform the user and end the session."