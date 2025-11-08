"""
Prompt template for Review Agent.

This prompt guides the LLM to evaluate math problems on three quality dimensions:
1. Clarity & Grammar
2. Logical Coherence & Completeness
3. Mathematical Validity & Solvability
"""


REVIEW_PROMPT_TEMPLATE = """As a mathematics quality checker, your task is to rigorously assess whether a given mathematical question is high-quality and provide rewrite suggestions:

1. Clarity & Grammar (1–5): The question must be grammatically correct, precisely phrased, and easy to understand. It should avoid ambiguity in wording or phrasing.

2. Logical Coherence & Completeness (1–5): All elements of the problem (e.g., given information, constraints, relationships, objectives) must be logically interconnected and sufficient. The problem should present a clear, sequential path for reasoning, without missing information required for the specified solution approach.

3. Mathematical Validity & Solvability (1–5): The problem must be fundamentally a mathematics problem, with all its premises and conditions being *mutually consistent* and *mathematically sound*. It must lead to a *unique, solvable numerical or analytical answer* that adheres to all mathematical rules and specified ranges (e.g., probabilities summing to 1, valid geometric properties, real number solutions). If any condition leads to a mathematical contradiction or an impossible/undefined solution (e.g., total probability > 1 after adjustments, an equation with no valid solution within given constraints), this criterion rates very low, and the exact mathematical inconsistency must be pinpointed. Avoid open-ended or non-mathematical questions.

** Scoring Guidelines **:
- Please rate the sample on a scale from 1 to 5 for each criterion, and return an overall rating on a scale from 1 to 5, where a higher score indicates higher level of quality.

Rephrased question: {rephrased_question}

**Output Requirements**
Respond in the following plain-text format **only** (do not include JSON or any additional commentary):

###thought###
<Analytical reasoning addressing each criterion sequentially, especially for rephrased_question>

###rating_score###
["<Clarity & Grammar score>", "<Logical Consistency score>", "<Mathematical Relevance & Solvability score>"]

###suggestions###
###Specific improvement 1###
<Specific improvement 1>
###Specific improvement 2###
<Specific improvement 2>
...more improvements if needed...

Notice:
- "rating_score" represents evaluate score of Rephrased question.
- when generate "suggestions", please give more details and reasons for each improvement.
"""


def create_review_prompt(rephrased_question: str) -> str:
    """
    Create a review prompt from rephrased question.

    Args:
        rephrased_question: The problem to evaluate

    Returns:
        Formatted prompt string ready for LLM

    Example:
        >>> prompt = create_review_prompt(
        ...     "A rectangular garden has a length that is 3 meters..."
        ... )
    """
    return REVIEW_PROMPT_TEMPLATE.format(rephrased_question=rephrased_question)
