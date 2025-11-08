"""
Prompt template for Rephrase Agent.

This prompt guides the LLM to systematically transform math problems
into more complex versions through escalation dimensions.
"""

from typing import List


REPHRASE_PROMPT_TEMPLATE = """Act as an expert mathematics educator specializing in problem complexity escalation. Systematically transform the given problem while preserving its core concepts, using the following framework:

**Stage 1: Problem Deconstruction**
- Domain Identification: [Algebra/Geometry/Calculus/etc.]
- Core Competencies: [List specific theorems/formulas/methods]
- Baseline Difficulty: [Level 1–5 using Krathwohl's Cognitive Rigor Index]

**Stage 2: Escalation Protocol**
Select ≥3 complexity dimensions from:
1. Multi-stage Transformation: Designs a single, cohesive mathematical problem where the complete solution inherently demands multiple, sequentially dependent calculations. The output of one implicit intermediate step must serve as the essential and sole input for the next, creating a longer chain of necessary computational derivation for the solver to reach the definite final answer.
2. Cross-domain Integration: Create hybrid problems combining ≥2 mathematical disciplines
3. Real-world Parameterization: Embed contextual constraints with multivariate relationships
4. Conditional Branching: Introduce layered constraints requiring decision-tree analysis
5. Inverse Problem Design: Reverse-engineer given solutions to reconstruct premises
6. Uncertainty Integration: Incorporate measurement errors/probabilistic factors
7. Optimization Extension: Convert closed solutions into multi-objective optimization challenges

**Stage 3: Revise question**
- Must be a definitive mathematical problem: The question must require mathematical reasoning, calculation, or logical deduction.
- Must have a unique and specific mathematical answer: The problem should lead to a single, verifiable numerical or analytical solution, avoiding open-ended questions, subjective evaluations, or non-mathematical tasks.

Please reply strictly in the following format:
Stage 1 #Problem Deconstruction#:
<your analysis>

Stage 2 #Escalation Protocol#:
<your escalation strategy>

Stage 3 #Finally Rewritten question#:
<the rephrased problem>

**Required Escalation Dimensions**: {escalation_dimensions}

**Original Problem**:
{problem_content}
"""


def create_rephrase_prompt(problem_content: str, escalation_dimensions: List[str]) -> str:
    """
    Create a rephrase prompt from problem content and escalation dimensions.

    Args:
        problem_content: The original math problem text
        escalation_dimensions: List of required escalation dimensions (≥3)

    Returns:
        Formatted prompt string ready for LLM

    Example:
        >>> prompt = create_rephrase_prompt(
        ...     "What is 2x + 3 = 11?",
        ...     ["Multi-stage Transformation", "Cross-domain Integration"]
        ... )
    """
    return REPHRASE_PROMPT_TEMPLATE.format(
        problem_content=problem_content,
        escalation_dimensions=", ".join(escalation_dimensions)
    )
