# Contract: Revise Agent

**Agent Type**: `REVISE`
**Purpose**: Improve rephrased math problems based on specific suggestions from Review Agent, addressing quality issues while preserving mathematical intent.

## Input Contract

### Input Schema

```python
class ReviseAgentInput(BaseModel):
    rephrased_question: str  # The problem to improve
    suggestions: List[str]  # Specific improvements from Review Agent
    quality_assessment: Optional[QualityAssessmentSummary] = None  # Scores for context
```

```python
class QualityAssessmentSummary(BaseModel):
    clarity_grammar_score: float
    logical_coherence_score: float
    mathematical_validity_score: float
    overall_score: float
```

### Input JSON Example

```json
{
  "rephrased_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden in meters.",
  "suggestions": [
    "Explicitly state answer format: 'Express your answer as a decimal rounded to two decimal places' to eliminate ambiguity about whether student should simplify 16/6 or provide decimal.",
    "Consider adding units clarification: specify if intermediate calculations should include units or only final answer."
  ],
  "quality_assessment": {
    "clarity_grammar_score": 4.5,
    "logical_coherence_score": 5.0,
    "mathematical_validity_score": 5.0,
    "overall_score": 4.83
  }
}
```

## Output Contract

### Output Format

The agent MUST respond in this exact plain-text format:

```
###revised_question###
<improved full question>

###revision_notes###
<Specific revision note>
```

### Output Schema (Parsed)

```python
class ReviseAgentOutput(BaseModel):
    revised_question: str  # Parsed from ###revised_question###
    revision_notes: str    # Parsed from ###revision_notes###, explains what was changed
```

### Output JSON Example (Parsed)

```json
{
  "revised_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places, including units (meters) in your final answer.",
  "revision_notes": "Added explicit answer format requirement ('decimal rounded to two decimal places') to address clarity suggestion. Included unit specification for final answer. Preserved all mathematical constraints and relationships from original problem."
}
```

## Prompt Template

### Full Prompt

```text
As an expert in mathematical question improvement, please optimize the question according to the following suggestions:

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
```

### Prompt Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{rephrased_question}` | String | The problem to improve | "A rectangular garden has..." |
| `{suggestions}` | String | Newline-separated list of suggestions | "- Explicitly state answer format...\n- Consider adding units..." |

### Prompt Template (Python)

```python
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
    # Format suggestions as bullet list
    suggestions_text = "\n".join(f"- {s}" for s in suggestions)

    return REVISE_PROMPT_TEMPLATE.format(
        rephrased_question=rephrased_question,
        suggestions=suggestions_text
    )
```

## Output Parser

### Parser Logic

```python
import re

class ReviseParser:
    @staticmethod
    def parse(raw_response: str) -> ReviseAgentOutput:
        """Parse Revise Agent's structured response."""

        # Extract revised question
        question_match = re.search(
            r"###revised_question###\s*\n(.*?)(?=###revision_notes###|$)",
            raw_response,
            re.DOTALL
        )
        if not question_match:
            raise ReviseParseError("Could not find revised_question in response")

        revised_question = question_match.group(1).strip()

        # Extract revision notes
        notes_match = re.search(
            r"###revision_notes###\s*\n(.*?)$",
            raw_response,
            re.DOTALL
        )
        revision_notes = notes_match.group(1).strip() if notes_match else ""

        if not revised_question:
            raise ReviseParseError("revised_question is empty")

        return ReviseAgentOutput(
            revised_question=revised_question,
            revision_notes=revision_notes
        )


class ReviseParseError(Exception):
    """Raised when Revise Agent output cannot be parsed."""
    pass
```

## Validation Rules

### Input Validation

1. `rephrased_question` MUST be non-empty, minimum 20 characters
2. `suggestions` MUST be non-empty list (at least 1 suggestion)
3. Each suggestion MUST be non-empty string

### Output Validation

1. `revised_question` MUST be non-empty
2. `revised_question` MUST be different from input `rephrased_question` (at least some change)
3. `revised_question` MUST maintain mathematical content (cannot remove all numbers/variables)
4. `revised_question` length should be similar to input (±50% to prevent major deletions/additions that change intent)
5. `revision_notes` SHOULD explain what was changed (minimum 20 characters)

### Preservation Validation

Ensure revised question preserves mathematical intent:

```python
def validate_mathematical_preservation(original: str, revised: str) -> bool:
    """Check that revision preserves mathematical content."""

    # Extract numbers from both
    original_numbers = set(re.findall(r'\d+(?:\.\d+)?', original))
    revised_numbers = set(re.findall(r'\d+(?:\.\d+)?', revised))

    # Numbers should be mostly preserved (allow small additions for clarification)
    if len(original_numbers - revised_numbers) > 1:
        logger.warning("Revision removed multiple numbers, may have changed intent")
        return False

    # Mathematical keywords should be preserved
    math_keywords = ['find', 'calculate', 'solve', 'determine', 'compute', 'prove', 'simplify']
    original_has_keywords = any(kw in original.lower() for kw in math_keywords)
    revised_has_keywords = any(kw in revised.lower() for kw in math_keywords)

    if original_has_keywords and not revised_has_keywords:
        logger.warning("Revision removed mathematical action verbs")
        return False

    return True
```

## Error Handling

### Parsing Errors

```python
try:
    output = ReviseParser.parse(raw_response)
except ReviseParseError as e:
    logger.error(f"Failed to parse revise output: {e}")
    # Retry with clarified prompt or fail the iteration
    raise
```

### Validation Failures

If revised question fails preservation check:

```python
if not validate_mathematical_preservation(input.rephrased_question, output.revised_question):
    logger.error("Revised question failed preservation check")
    # Option 1: Retry with explicit preservation instruction
    # Option 2: Use original question and mark iteration as failed
    raise ValidationError("Revision changed mathematical intent")
```

## Testing Strategy

### Contract Tests

```python
def test_revise_agent_output_format():
    """Test that Revise Agent produces expected format."""
    raw_response = """
###revised_question###
A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places.

###revision_notes###
Added explicit answer format requirement to address clarity. Preserved all mathematical constraints.
"""

    parsed = ReviseParser.parse(raw_response)

    assert len(parsed.revised_question) > 0
    assert len(parsed.revision_notes) > 0
    assert "decimal" in parsed.revised_question.lower()
```

### Integration Tests

```python
async def test_revise_agent_preserves_math():
    """Test that Revise Agent preserves mathematical content."""
    agent = ReviseAgent(llm_client=mock_llm)

    input_data = ReviseAgentInput(
        rephrased_question="A rectangle has length 2w+3 and perimeter 22. Find width w.",
        suggestions=["Expand abbreviations", "Use full words instead of variables in prose"]
    )

    output = await agent.execute(input_data)

    # Should still contain numbers and mathematical relationships
    assert "2" in output.revised_question or "twice" in output.revised_question
    assert "3" in output.revised_question or "three" in output.revised_question
    assert "22" in output.revised_question
    assert any(word in output.revised_question.lower() for word in ["width", "length", "perimeter"])
```

### Regression Tests

Test that common revision scenarios work correctly:

```python
@pytest.mark.parametrize("scenario,original,suggestions,expected_changes", [
    (
        "add_answer_format",
        "Find the width of a rectangle with length 2w+3 and perimeter 22.",
        ["Specify answer format"],
        ["decimal", "rounded", "places"]
    ),
    (
        "fix_ambiguity",
        "A number is 5 more than another. Their sum is 15. Find them.",
        ["Clarify which number to find", "Give variables names"],
        ["first number", "second number", "x", "y"]
    ),
    (
        "fix_mathematical_error",
        "Probability of A is 0.6, B is 0.7, both is 0.5. Find neither.",
        ["Recalculate to ensure probabilities are consistent"],
        # Should preserve or fix to valid probabilities
        []
    )
])
async def test_revise_agent_scenarios(scenario, original, suggestions, expected_changes):
    """Test common revision scenarios."""
    agent = ReviseAgent(llm_client=real_llm)

    input_data = ReviseAgentInput(
        rephrased_question=original,
        suggestions=suggestions
    )

    output = await agent.execute(input_data)

    # Check that expected changes are present
    for change in expected_changes:
        assert change.lower() in output.revised_question.lower(), \
            f"Expected '{change}' in revised question for scenario '{scenario}'"

    # Ensure mathematical content preserved
    assert validate_mathematical_preservation(original, output.revised_question)
```

## Example Execution

### Example 1: Adding Answer Format Specification

**Input**:
```json
{
  "rephrased_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden in meters.",
  "suggestions": [
    "Explicitly state answer format: 'Express your answer as a decimal rounded to two decimal places'"
  ]
}
```

**Output** (Parsed):
```json
{
  "revised_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places, with units.",
  "revision_notes": "Added explicit answer format specification ('decimal rounded to two decimal places, with units') to eliminate ambiguity. All original mathematical constraints and relationships preserved: length = 2×width + 3, perimeter = 22 meters."
}
```

### Example 2: Fixing Mathematical Contradiction

**Input**:
```json
{
  "rephrased_question": "A bag contains 10 red and 15 blue marbles. The probability of drawing red is 0.5. If we add 5 red marbles, what is the new probability?",
  "suggestions": [
    "Mathematical inconsistency: 10 red out of 25 total gives probability 10/25 = 0.4, not 0.5. Either change the marble counts or remove the probability statement."
  ]
}
```

**Output** (Parsed):
```json
{
  "revised_question": "A bag contains red and blue marbles. The probability of drawing a red marble is 0.4. If we add 5 red marbles to the bag (without changing the number of blue marbles), what is the new probability of drawing a red marble? Express your answer as a decimal rounded to three decimal places.",
  "revision_notes": "Fixed mathematical contradiction by removing specific marble counts and starting with correct probability 0.4. Added clarification that only red marbles are added. Added answer format specification. Problem now mathematically consistent: if original has R red and B blue with R/(R+B) = 0.4, then after adding 5 red, probability becomes (R+5)/(R+B+5)."
}
```

---

**End of Revise Agent Contract**
