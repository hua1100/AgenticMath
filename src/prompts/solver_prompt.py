"""
Solver Agent Prompt Template.

Creates prompts for generating detailed Chain-of-Thought (CoT) solutions
to mathematical problems.
"""

from typing import Optional


SOLVER_PROMPT_TEMPLATE = """As a mathematics problem solving expert, analyze and answer the following question.

Workflow:
1. Analyze and Deconstruct:
   - First, systematically break down the problem into its core components.
   - Explicitly list all given data, variables, constraints, and the final objective of the problem.

2. Clarify Ambiguities:
   - Before starting calculations, if any part of the problem statement is ambiguous, you must state your interpretation and the reasoning behind it.

3. Step-by-Step Derivation and Process Demonstration:
   - For each component of the problem, provide a detailed step-by-step derivation.
   - You must show all intermediate calculation steps, formulas used, and logical judgments. Do not skip or summarize critical calculation processes.
   - For any step involving complex calculations, multi-case analysis, or iterative enumeration (e.g., filtering combinations that meet a condition, solving systems of equations, analyzing multiple scenarios), you must clearly list all cases or combinations considered.

4. Synthesis and Final Calculation:
   - Integrate the results from all preceding steps to perform the final calculation.
   - Clearly show the final calculation that leads to the final answer.

Respond in the following plain-text format **only** (do not include JSON or any additional commentary):

###thought###
<step-by-step reasoning process>

###answer###
<final answer>

Output Notice:
- Replace <step-by-step reasoning process> with your detailed derivation.
- Replace <final answer> with the concise final answer (e.g., a number or fraction), without units or extra words.

Output Example:

Question: A cleaning company produces two sanitizer sprays. One spray kills 50% of germs, and another spray kills 25% of germs. However, 5% of the germs they kill are the same ones. What percentage of germs would be left after using both sanitizer sprays together?

Output(must match the specified format exactly):
###thought###
To correctly calculate the percentage of germs left, we must use the Principle of Inclusion-Exclusion to find the total percentage of unique germs killed.

Step 1: Identify given information
- Spray A kills 50% of germs
- Spray B kills 25% of germs
- Overlap (both sprays kill the same 5% of germs)

Step 2: Apply Inclusion-Exclusion Principle
- Total killed = A + B - (A ∩ B)
- Total killed = 50% + 25% - 5%
- Total killed = 70%

Step 3: Calculate percentage left
- Percentage left = 100% - Total killed
- Percentage left = 100% - 70%
- Percentage left = 30%

###answer###
30

Question: {question}

Output:
"""


def create_solver_prompt(question: str, language: str = "auto") -> str:
    """
    Create a solver prompt for a given math problem.

    Args:
        question: The math problem to solve
        language: Language hint ("en", "zh", or "auto"). Default "auto" detects from question.

    Returns:
        Complete prompt string ready to send to LLM

    Example:
        >>> prompt = create_solver_prompt("Solve: 2x + 3 = 11")
        >>> print(prompt[:50])
        As a mathematics problem solving expert, analyze...
    """
    # For now, use the English template
    # Future: Add Chinese template support based on language parameter
    return SOLVER_PROMPT_TEMPLATE.format(question=question)


def create_solver_prompt_zh(question: str) -> str:
    """
    Create a Chinese solver prompt (future implementation).

    Args:
        question: The math problem to solve in Chinese

    Returns:
        Complete Chinese prompt string

    Note:
        Currently uses English template. Chinese template to be added.
    """
    # TODO: Implement Chinese-specific prompt template
    # For now, delegate to main function
    return create_solver_prompt(question, language="zh")
