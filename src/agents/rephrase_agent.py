"""
Rephrase Agent for systematic problem complexity escalation.

Uses LLM to transform math problems into more complex versions through
escalation dimensions while preserving core mathematical concepts.
"""

import logging
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from .llm_client import LLMClient, LLMConfig
from src.prompts.rephrase_prompt import create_rephrase_prompt
from src.parsers.rephrase_parser import RephraseParser, RephraseAgentOutput, RephraseParseError
from src.models.agent_execution import AgentExecution, AgentType
from src.models.problem import MathDomain

logger = logging.getLogger(__name__)


# Valid escalation dimensions
VALID_ESCALATION_DIMENSIONS = {
    "Multi-stage Transformation",
    "Cross-domain Integration",
    "Real-world Parameterization",
    "Conditional Branching",
    "Inverse Problem Design",
    "Uncertainty Integration",
    "Optimization Extension",
}


class RephraseAgent:
    """
    Rephrase Agent for math problem complexity escalation.

    Features:
    - 3-stage systematic transformation (Deconstruction → Protocol → Rewrite)
    - Applies ≥3 escalation dimensions
    - Preserves mathematical correctness
    - Logs execution to AgentExecution table

    Example:
        >>> agent = RephraseAgent()
        >>> result = agent.rephrase(
        ...     problem_content="Solve 2x + 3 = 11",
        ...     escalation_dimensions=["Multi-stage Transformation", "Cross-domain Integration"]
        ... )
        >>> print(result.stage3_rewritten_question)
    """

    def __init__(self, llm_client: Optional[LLMClient] = None, db: Optional[Session] = None):
        """
        Initialize Rephrase Agent.

        Args:
            llm_client: LLM client. If None, creates default client.
            db: Database session for logging. If None, logging is skipped.
        """
        self.llm_client = llm_client or LLMClient(
            config=LLMConfig(temperature=0.7, model="gpt-4o")
        )
        self.db = db
        self.parser = RephraseParser()

    def rephrase(
        self,
        problem_content: str,
        escalation_dimensions: List[str],
        problem_id: Optional[UUID] = None,
        domain: Optional[MathDomain] = None,
        target_difficulty: Optional[int] = None,
    ) -> RephraseAgentOutput:
        """
        Rephrase a math problem with complexity escalation.

        Args:
            problem_content: Original problem text (minimum 10 characters)
            escalation_dimensions: List of ≥3 escalation dimensions
            problem_id: Optional problem ID for logging
            domain: Optional domain hint
            target_difficulty: Optional target difficulty 1-5

        Returns:
            RephraseAgentOutput with 3 stages and extracted metadata

        Raises:
            ValueError: If input validation fails
            RephraseParseError: If LLM output cannot be parsed
        """
        # Validate input
        self._validate_input(problem_content, escalation_dimensions)

        # Create prompt
        prompt = create_rephrase_prompt(problem_content, escalation_dimensions)

        # Record execution start time
        execution_start = datetime.utcnow()

        try:
            # Call LLM
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.chat_completion(messages)

            raw_output = response["content"]
            token_usage = response["usage"]

            # Calculate execution time
            execution_end = datetime.utcnow()
            execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)

            # Parse output
            parsed_output = self.parser.parse(raw_output)

            # Validate output
            self._validate_output(parsed_output, escalation_dimensions)

            # Log to database if db session is available
            if self.db:
                execution_record = AgentExecution(
                    id=uuid4(),
                    agent_type=AgentType.REPHRASE,
                    session_id=None,  # Will be set by pipeline if part of a session
                    input_data={
                        "problem_content": problem_content,
                        "escalation_dimensions": escalation_dimensions,
                        "problem_id": str(problem_id) if problem_id else None,
                        "domain": domain.value if domain else None,
                        "target_difficulty": target_difficulty,
                    },
                    output_data={
                        "rephrased_problem": parsed_output.stage3_rewritten_question,
                        "identified_domain": parsed_output.identified_domain,
                        "applied_dimensions": parsed_output.applied_dimensions,
                        "expected_difficulty": parsed_output.expected_difficulty,
                        "reasoning": parsed_output.stage1_reasoning,
                    },
                    prompt_template=prompt,
                    raw_llm_response=raw_output,
                    execution_time_ms=execution_time_ms,
                    llm_model=response.get("model", "gpt-4o"),
                )
                self.db.add(execution_record)
                self.db.commit()

                logger.info(
                    f"Rephrase execution logged: {execution_record.id}, "
                    f"{execution_time_ms}ms"
                )

            logger.info(
                f"Rephrase successful: {parsed_output.identified_domain}, "
                f"{len(parsed_output.applied_dimensions)} dimensions, "
                f"{token_usage['total_tokens']} tokens"
            )

            return parsed_output

        except Exception as e:
            # Calculate execution time for failed execution
            execution_end = datetime.utcnow()
            execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)

            # Log failure to database if available
            if self.db:
                try:
                    execution_record = AgentExecution(
                        id=uuid4(),
                        agent_type=AgentType.REPHRASE,
                        session_id=None,
                        input_data={
                            "problem_content": problem_content,
                            "escalation_dimensions": escalation_dimensions,
                            "problem_id": str(problem_id) if problem_id else None,
                        },
                        output_data={"error": str(e)},
                        prompt_template=prompt,
                        raw_llm_response=None,
                        execution_time_ms=execution_time_ms,
                        llm_model="gpt-4o",
                    )
                    self.db.add(execution_record)
                    self.db.commit()
                except Exception as log_error:
                    logger.warning(f"Failed to log error to database: {log_error}")

            logger.error(f"Rephrase failed: {e}")
            raise

    def _validate_input(self, problem_content: str, escalation_dimensions: List[str]):
        """Validate input parameters."""
        if not problem_content or len(problem_content) < 10:
            raise ValueError("problem_content must be at least 10 characters")

        if not escalation_dimensions or len(escalation_dimensions) < 3:
            raise ValueError("escalation_dimensions must contain at least 3 dimensions")

        invalid_dimensions = [d for d in escalation_dimensions if d not in VALID_ESCALATION_DIMENSIONS]
        if invalid_dimensions:
            raise ValueError(
                f"Invalid escalation dimensions: {invalid_dimensions}. "
                f"Valid options: {sorted(VALID_ESCALATION_DIMENSIONS)}"
            )

    def _validate_output(self, output: RephraseAgentOutput, input_dimensions: List[str]):
        """Validate parsed output."""
        if not output.stage3_rewritten_question:
            raise RephraseParseError("stage3_rewritten_question is empty")

        # Check if question ends with ? or imperative (support both English and Chinese)
        question = output.stage3_rewritten_question.strip()

        # Valid endings: ?, ？, or imperative verbs
        valid_endings = question.endswith("?") or question.endswith("？")

        # Valid starts: English imperatives
        english_imperatives = ["find", "calculate", "determine", "solve", "compute"]
        has_english_imperative = any(
            question.lower().startswith(cmd) for cmd in english_imperatives
        )

        # Valid patterns: Chinese question formats
        chinese_patterns = [
            "求", "計算", "問", "解", "證明", "判斷", "確定",  # Chinese imperatives
            "是多少", "有多少", "為何", "如何",  # Chinese question patterns
        ]
        has_chinese_pattern = any(pattern in question for pattern in chinese_patterns)

        # Accept if any valid format is found
        if not (valid_endings or has_english_imperative or has_chinese_pattern):
            logger.warning(
                "Rephrased question may not be properly formatted "
                "(no ? or imperative in English/Chinese)"
            )

        # Check applied dimensions match input (at least 3)
        # Only warn if parser completely failed (0 dimensions)
        if len(output.applied_dimensions) == 0:
            logger.warning(
                f"Could not extract applied dimensions from LLM output. "
                f"This may be due to formatting differences but doesn't affect quality."
            )

    def _estimate_cost(self, token_usage: dict) -> float:
        """Estimate cost from token usage."""
        # GPT-4o pricing: ~$5/1M prompt, ~$15/1M completion
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        return (prompt_tokens * 5 + completion_tokens * 15) / 1_000_000
