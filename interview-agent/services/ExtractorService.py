import hashlib
import io
import re
from typing import Any, Dict, List, Tuple

import PyPDF2

from models.Case import Case


class ExtractorService:
    """Service to build Case objects from uploaded PDF content."""

    _QUESTION_LEADS = (
        "question",
        "prompt",
        "case prompt",
        "case question",
        "analysis",
        "phase",
        "stage",
        "step",
        "section",
        "task",
        "calculation",
        "market sizing",
        "framework",
    )
    _MATH_KEYWORDS = (
        "calculate",
        "calculation",
        "compute",
        "estimate",
        "project",
        "determin",
        "how much",
        "how many",
        "roi",
        "margin",
        "breakeven",
        "%",
        "percent",
        "percentage",
        "growth rate",
        "npv",
        "volume",
        "units",
        "revenue",
        "cost",
    )
    _ANALYSIS_KEYWORDS = (
        "explain",
        "describe",
        "outline",
        "structure",
        "recommend",
        "assess",
        "evaluate",
        "analyze",
        "diagnose",
        "framework",
        "approach",
        "strategy",
        "prioritize",
        "consider",
        "discuss",
    )

    def __init__(self) -> None:
        """Initialize the service with an in-memory cache of parsed cases."""
        self.cache: Dict[str, Dict[str, Any]] = {}

    def create_case_from_pdf(self, case_id: str, pdf_content: bytes) -> Case:
        """Create a Case object from PDF bytes."""
        fingerprint = hashlib.sha256(pdf_content).hexdigest()
        cached = self.cache.get(case_id)
        if cached and cached["fingerprint"] == fingerprint:
            return cached["case"]

        text = self._extract_text(pdf_content)
        description, questions = self._separate_description_and_questions(text)

        if not questions:
            raise ValueError(
                "No interview questions found in the supplied PDF. "
                "Ensure the document contains clear question prompts."
            )

        phases: Dict[str, Dict[str, List[str]]] = {}
        used_keys: set[str] = set()
        for idx, question in enumerate(questions, start=1):
            phase_key = self._generate_phase_name(question, idx, used_keys)
            used_keys.add(phase_key)
            phases[phase_key] = {
                "Q": question,
                "R": self._build_rubric(question),
            }

        case = Case(phases)
        case.case_description = description

        self.cache[case_id] = {
            "fingerprint": fingerprint,
            "case": case,
            "questions": questions,
            "description": description,
        }
        return case

    def _extract_text(self, pdf_content: bytes) -> str:
        """Return normalized text content extracted from the supplied PDF bytes."""
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
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Join hyphenated words split by line breaks (common in PDFs).
        text = re.sub(r"-\n(?=[a-z])", "", text)
        # Collapse excessive blank lines.
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Trim trailing spaces on each line.
        text = "\n".join(line.strip() for line in text.split("\n"))
        return text.strip()

    def _separate_description_and_questions(self, text: str) -> Tuple[str, List[str]]:
        """Split case text into a narrative description and a list of questions."""
        blocks = [
            block.strip()
            for block in re.split(r"\n\s*\n", text)
            if block and block.strip()
        ]

        description_parts: List[str] = []
        questions: List[str] = []

        for block in blocks:
            if self._block_is_question(block):
                extracted = self._extract_questions_from_block(block)
                if extracted:
                    questions.extend(extracted)
                elif questions:
                    questions[-1] = f"{questions[-1]} {block}".strip()
                else:
                    description_parts.append(block)
            else:
                if questions:
                    questions[-1] = f"{questions[-1]} {block}".strip()
                else:
                    description_parts.append(block)

        if not questions:
            # Fallback: attempt to split entire text into questions via '?'.
            fallback = [
                segment.strip()
                for segment in re.findall(r"[^?]+\?", text)
                if segment and len(segment.split()) >= 5
            ]
            questions.extend(fallback)

        description = " ".join(description_parts).strip()
        return description, questions

    def _block_is_question(self, block: str) -> bool:
        """Return True when a text block likely represents a question prompt."""
        if "?" in block:
            return True

        lowered = block.lower()
        if any(lowered.startswith(prefix) for prefix in self._QUESTION_LEADS):
            return True

        if any(keyword in lowered for keyword in self._MATH_KEYWORDS):
            return True

        if any(keyword in lowered for keyword in self._ANALYSIS_KEYWORDS):
            return True

        return False

    def _extract_questions_from_block(self, block: str) -> List[str]:
        """Break a text block into individual, cleaned question strings."""
        questions: List[str] = []
        parts = block.split("?")

        for idx, part in enumerate(parts):
            chunk = part.strip()
            if not chunk:
                continue

            if idx < len(parts) - 1:
                candidate = f"{chunk}?"
                if self._is_viable_question(candidate):
                    questions.append(self._collapse_whitespace(candidate))
            else:
                if (
                    self._looks_like_question(chunk)
                    and self._is_viable_question(chunk)
                ):
                    questions.append(self._collapse_whitespace(chunk))

        return questions

    def _collapse_whitespace(self, text: str) -> str:
        """Collapse repeated whitespace characters into single spaces."""
        return re.sub(r"\s+", " ", text).strip()

    def _is_viable_question(self, question: str) -> bool:
        """Check whether a candidate question falls within the accepted word range."""
        word_count = len(question.split())
        return 6 <= word_count <= 120

    def _looks_like_question(self, text: str) -> bool:
        """Heuristically determine if text resembles a case interview question."""
        lowered = text.lower()
        if any(lowered.startswith(prefix) for prefix in self._QUESTION_LEADS):
            return True
        if any(keyword in lowered for keyword in self._MATH_KEYWORDS):
            return True
        if any(keyword in lowered for keyword in self._ANALYSIS_KEYWORDS):
            return True
        return False

    def _generate_phase_name(
        self, question: str, index: int, existing: set[str]
    ) -> str:
        """Create a unique phase identifier keyed off the question content and type."""
        q_type = self._classify_question(question)
        prefix = "math" if q_type == "math" else "analysis"

        slug = re.sub(r"[^a-z0-9]+", "_", question.lower()).strip("_")
        slug = slug[:30] or prefix
        candidate = f"{index:02d}_{prefix}_{slug}"

        while candidate in existing:
            candidate = f"{candidate}_{len(existing)}"
        return candidate

    def _build_rubric(self, question: str) -> List[str]:
        """Return rubric bullet points tailored to the question classification."""
        q_type = self._classify_question(question)
        if q_type == "math":
            return [
                "Identifies the relevant figures, units, and assumptions from the case facts.",
                "Sets up the calculation with a clear structure before solving.",
                "Executes each computation accurately and shows intermediate steps.",
                "Interprets the numerical result within the client’s business context.",
            ]
        return [
            "Applies a structured, hypothesis-driven approach to the question.",
            "Incorporates pertinent case facts and clarifying data points.",
            "Considers multiple angles, risks, and trade-offs before concluding.",
            "Communicates insights crisply and ties them to business impact.",
        ]

    def _classify_question(self, question: str) -> str:
        """Classify a question as 'math' or 'analysis' using keyword heuristics."""
        text = question.lower()
        if any(keyword in text for keyword in self._MATH_KEYWORDS):
            return "math"
        if re.search(r"\d", question):
            return "math"
        return "analysis"
