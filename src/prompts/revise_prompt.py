"""
Prompt template for Revise Agent.

This prompt guides the LLM to improve math problems based on specific suggestions
from the Review Agent, while preserving mathematical intent.
"""

from typing import List


REVISE_PROMPT_TEMPLATE = """As an expert in mathematical question improvement, please optimize the question according to the following suggestions:

{suggestions}

Optimization requirements:

1. Clarity & Grammar (1–5): The question must be grammatically correct, precisely phrased, and easy to understand. It should avoid ambiguity in wording or phrasing.

2. Logical Coherence & Completeness (1–5): All elements of the problem (e.g., given information, constraints, relationships, objectives) must be logically interconnected and sufficient. The problem should present a clear, sequential path for reasoning, without missing information required for the specified solution approach.

3. Mathematical Validity & Solvability (1–5): The problem must be fundamentally a mathematics problem, with all its premises and conditions being *mutually consistent* and *mathematically sound*. It must lead to a *unique, solvable numerical or analytical answer* that adheres to all mathematical rules and specified ranges (e.g., probabilities summing to 1, valid geometric properties, real number solutions). If any condition leads to a mathematical contradiction or an impossible/undefined solution (e.g., total probability exceeds 1 after adjustments, an equation with no valid solution within given constraints), this criterion rates very low, and the exact mathematical inconsistency must be pinpointed. Avoid open-ended or non-mathematical questions.

original question: {rephrased_question}

** Output Requirements **
Respond in the following plain-text format **only** (do not include JSON or any additional commentary):

###revised_question###
<improved full question>

###revision_notes###
<Specific revision note>
"""


def create_revise_prompt(rephrased_question: str, suggestions: List[str]) -> str:
    """
    Create a revise prompt from rephrased question and suggestions.

    Args:
        rephrased_question: The problem to improve
        suggestions: List of specific improvements from Review Agent

    Returns:
        Formatted prompt string ready for LLM

    Example:
        >>> prompt = create_revise_prompt(
        ...     rephrased_question="A rectangular garden has a length...",
        ...     suggestions=[
        ...         "Explicitly state answer format",
        ...         "Add units clarification"
        ...     ]
        ... )
    """
    # Format suggestions as bullet list
    suggestions_text = "\n".join(f"- {s}" for s in suggestions)

    return REVISE_PROMPT_TEMPLATE.format(
        rephrased_question=rephrased_question,
        suggestions=suggestions_text
    )
