import hashlib
import io
import json
from typing import Any, Dict, List
import PyPDF2
from openai import OpenAI
import dotenv

from models.Case import Case

dotenv.load_dotenv()

class LLMExtractorService:
    """Service to build Case objects from uploaded PDF content using LLM analysis."""

    def __init__(self) -> None:
        """Initialize the service with OpenAI client and cache."""
        self.client = OpenAI()
        self.cache: Dict[str, Dict[str, Any]] = {}

    def create_case_from_pdf(self, case_id: str, pdf_content: bytes) -> Case:
        """Create a Case object from PDF bytes using LLM analysis."""
        fingerprint = hashlib.sha256(pdf_content).hexdigest()
        cached = self.cache.get(case_id)
        if cached and cached["fingerprint"] == fingerprint:
            return cached["case"]

        # Extract text from PDF
        text = self._extract_text(pdf_content)
        
        # Use LLM to analyze and extract case structure
        case_data = self._analyze_case_with_llm(text)
        
        # Create Case object
        case = Case(case_data)

        # Cache the result
        self.cache[case_id] = {
            "fingerprint": fingerprint,
            "case": case,
            "case_data": case_data,
        }
        
        return case

    def _extract_text(self, pdf_content: bytes) -> str:
        """Extract and normalize text from PDF bytes."""
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        pages: List[str] = []
        
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                pages.append(page_text)

        raw_text = "\n".join(pages)
        return self._normalize_text(raw_text)

    def _normalize_text(self, text: str) -> str:
        """Normalize PDF-derived text by fixing line endings, hyphenation, and spacing."""
        import re
        
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Join hyphenated words split by line breaks
        text = re.sub(r"-\n(?=[a-z])", "", text)
        # Collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Trim trailing spaces on each line
        text = "\n".join(line.strip() for line in text.split("\n"))
        return text.strip()

    def _analyze_case_with_llm(self, text: str) -> Dict[str, Any]:
        """Use LLM to analyze the case text and extract structured information."""
        
        system_prompt = """You are an expert case interview analyst. Your task is to analyze a business case study document and extract the key information in a structured format.

                        From the provided case study text, you need to:

                        1. **Case Description**: Extract the main case description/prompt. This is usually labeled as "PROMPT:", "Case Description:", "Scenario:", or contains phrases like "Your client is..." or "You have been hired to..."

                        2. **Interview Questions**: Identify all the interview questions that a candidate would be asked during the case. These might be:
                        - Direct questions ending with "?"
                        - Calculation tasks (e.g., "Calculate the ROI...")
                        - Analysis tasks (e.g., "Analyze the market opportunity...")
                        - Framework questions (e.g., "How would you structure your analysis?")

                        3. **Question Classification**: For each question, determine if it's primarily:
                        - "math" (requires calculations, quantitative analysis)
                        - "analysis" (requires qualitative reasoning, frameworks, strategic thinking)

                        Please return your analysis in the following JSON format:

                        ```json
                        {
                            "case_description": "The main case description/scenario text",
                            "phase_order": ["01_analysis_framework", "02_math_calculation", "03_analysis_recommendation"],
                            "phases": {
                                "01_analysis_framework": {
                                    "name": "01_analysis_framework",
                                    "question": "The actual question text",
                                    "rubric": [
                                        "Evaluation criteria 1",
                                        "Evaluation criteria 2",
                                        "Evaluation criteria 3",
                                        "Evaluation criteria 4"
                                    ]
                                },
                                "02_math_calculation": {
                                    "name": "02_math_calculation", 
                                    "question": "The calculation question text",
                                    "rubric": [
                                        "Math-specific evaluation criteria 1",
                                        "Math-specific evaluation criteria 2",
                                        "Math-specific evaluation criteria 3",
                                        "Math-specific evaluation criteria 4"
                                    ]
                                }
                            }
                        }
                        ```

                        **Important Guidelines:**
                        - Phase names should follow the pattern: "{number}_{type}_{short_description}" (e.g., "01_analysis_market_entry", "02_math_roi_calculation")
                        - Math questions should have rubrics focused on: identifying figures/assumptions, calculation setup, accuracy, business interpretation
                        - Analysis questions should have rubrics focused on: structured approach, using case facts, considering multiple angles, clear communication
                        - Extract questions in the order they appear in the document
                        - If no clear case description is found, use an empty string
                        - Ensure all questions are substantial and relevant to the case interview process

                        Be thorough but focused on extracting information that would be useful for conducting an actual case interview."""

        user_prompt = f"""Please analyze the following case study document and extract the structured information as requested:

                        ---
                        {text}
                        ---

                        Return only the JSON response with the extracted case information."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for more consistent extraction
                max_tokens=4000
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            case_data = json.loads(content)
            
            # Validate the structure
            return self._validate_and_fix_case_data(case_data)
            
        except Exception as e:
            raise ValueError(f"Failed to analyze case with LLM: {str(e)}")

    def _validate_and_fix_case_data(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix the case data structure returned by LLM."""
        
        # Ensure required top-level keys exist
        if "case_description" not in case_data:
            case_data["case_description"] = ""
        
        if "phases" not in case_data:
            raise ValueError("LLM response missing 'phases' key")
        
        if "phase_order" not in case_data:
            case_data["phase_order"] = list(case_data["phases"].keys())
        
        # Validate each phase
        for phase_name, phase_data in case_data["phases"].items():
            if "name" not in phase_data:
                phase_data["name"] = phase_name
            
            if "question" not in phase_data:
                raise ValueError(f"Phase {phase_name} missing 'question' key")
            
            if "rubric" not in phase_data:
                # Generate default rubric based on phase name
                if "math" in phase_name.lower():
                    phase_data["rubric"] = [
                        "Identifies the relevant figures, units, and assumptions from the case facts.",
                        "Sets up the calculation with a clear structure before solving.",
                        "Executes each computation accurately and shows intermediate steps.",
                        "Interprets the numerical result within the client's business context."
                    ]
                else:
                    phase_data["rubric"] = [
                        "Applies a structured, hypothesis-driven approach to the question.",
                        "Incorporates pertinent case facts and clarifying data points.",
                        "Considers multiple angles, risks, and trade-offs before concluding.",
                        "Communicates insights crisply and ties them to business impact."
                    ]
        
        return case_data

    def get_cached_case_data(self, case_id: str) -> Dict[str, Any]:
        """Get the raw case data for a cached case."""
        cached = self.cache.get(case_id)
        if cached:
            return cached.get("case_data", {})
        return {}