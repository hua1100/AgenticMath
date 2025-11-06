# Contract: Review Agent

**Agent Type**: `REVIEW`
**Purpose**: Evaluate rephrased math problems on three quality dimensions (Clarity, Logic, Mathematical Validity) and provide specific improvement suggestions when below threshold.

## Input Contract

### Input Schema

```python
class ReviewAgentInput(BaseModel):
    rephrased_question: str  # The problem to evaluate
    original_question: Optional[str] = None  # Original for context (optional)
```

### Input JSON Example

```json
{
  "rephrased_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden in meters.",
  "original_question": "Solve for x: 2x + 3 = 11"
}
```

## Output Contract

### Output Format

The agent MUST respond in this exact plain-text format:

```
###thought###
<Analytical reasoning addressing each criterion sequentially>

###rating_score###
["<Clarity & Grammar score>", "<Logical Consistency score>", "<Mathematical Relevance & Solvability score>"]

###suggestions###
###Specific improvement 1###
<Specific improvement 1>
###Specific improvement 2###
<Specific improvement 2>
...more improvements if needed...
```

### Output Schema (Parsed)

```python
class ReviewAgentOutput(BaseModel):
    thought_process: str  # Parsed from ###thought###
    clarity_grammar_score: float  # First element of rating_score, range 1.0-5.0
    logical_coherence_score: float  # Second element, range 1.0-5.0
    mathematical_validity_score: float  # Third element, range 1.0-5.0
    overall_score: float  # Computed average or separate if LLM provides
    suggestions: List[str]  # Parsed from ###Specific improvement N###
```

### Output JSON Example (Parsed)

```json
{
  "thought_process": "Clarity & Grammar (4.5/5): The problem is well-phrased with clear mathematical language. Minor improvement: specify units consistently.\n\nLogical Coherence (5.0/5): All elements are interconnected - length definition depends on width, perimeter provides the constraint, question asks for width. Complete information provided.\n\nMathematical Validity & Solvability (5.0/5): Problem is solvable with unique answer. Perimeter formula P=2(l+w) with l=2w+3 gives 2(2w+3+w)=22, solving yields w=2.67 meters. All constraints are consistent.",
  "clarity_grammar_score": 4.5,
  "logical_coherence_score": 5.0,
  "mathematical_validity_score": 5.0,
  "overall_score": 4.83,
  "suggestions": [
    "Consider explicitly stating 'Express your answer as a decimal rounded to two decimal places' for clarity on expected answer format."
  ]
}
```

## Prompt Template

### Full Prompt

```text
As a mathematics quality checker, your task is to rigorously assess whether a given mathematical question is high-quality and provide rewrite suggestions:

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
```

### Prompt Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{rephrased_question}` | String | The problem to evaluate | "A rectangular garden has..." |

### Prompt Template (Python)

```python
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
    return REVIEW_PROMPT_TEMPLATE.format(rephrased_question=rephrased_question)
```

## Output Parser

### Parser Logic

```python
import re
import json
from typing import List

class ReviewParser:
    @staticmethod
    def parse(raw_response: str) -> ReviewAgentOutput:
        """Parse Review Agent's structured response."""

        # Extract thought process
        thought_match = re.search(
            r"###thought###\s*\n(.*?)(?=###rating_score###|$)",
            raw_response,
            re.DOTALL
        )
        thought_process = thought_match.group(1).strip() if thought_match else ""

        # Extract rating scores
        rating_match = re.search(
            r"###rating_score###\s*\n(\[.*?\])",
            raw_response,
            re.DOTALL
        )
        if not rating_match:
            raise ReviewParseError("Could not find rating_score in response")

        rating_text = rating_match.group(1)
        try:
            # Parse the list - handle both string numbers and floats
            scores = json.loads(rating_text)
            if len(scores) != 3:
                raise ReviewParseError(f"Expected 3 scores, got {len(scores)}")

            clarity_score = float(scores[0])
            logical_score = float(scores[1])
            validity_score = float(scores[2])

            # Validate range
            for score in [clarity_score, logical_score, validity_score]:
                if not (1.0 <= score <= 5.0):
                    raise ReviewParseError(f"Score {score} out of range [1.0, 5.0]")

        except (json.JSONDecodeError, ValueError) as e:
            raise ReviewParseError(f"Failed to parse rating_score: {e}")

        # Calculate overall score (average)
        overall_score = round((clarity_score + logical_score + validity_score) / 3, 2)

        # Extract suggestions
        suggestions_match = re.search(
            r"###suggestions###\s*\n(.*?)$",
            raw_response,
            re.DOTALL
        )
        suggestions_text = suggestions_match.group(1).strip() if suggestions_match else ""

        # Parse individual suggestions (###Specific improvement N###)
        suggestion_items = re.findall(
            r"###Specific improvement \d+###\s*\n(.*?)(?=###Specific improvement \d+###|$)",
            suggestions_text,
            re.DOTALL
        )
        suggestions = [s.strip() for s in suggestion_items if s.strip()]

        return ReviewAgentOutput(
            thought_process=thought_process,
            clarity_grammar_score=clarity_score,
            logical_coherence_score=logical_score,
            mathematical_validity_score=validity_score,
            overall_score=overall_score,
            suggestions=suggestions
        )


class ReviewParseError(Exception):
    """Raised when Review Agent output cannot be parsed."""
    pass
```

## Validation Rules

### Input Validation

1. `rephrased_question` MUST be non-empty, minimum 20 characters
2. `rephrased_question` MUST contain mathematical keywords or symbols

### Output Validation

1. All three scores MUST be present and in range [1.0, 5.0]
2. `thought_process` MUST address all three criteria
3. `suggestions` SHOULD be empty if `overall_score >= threshold` (warning, not error)
4. Each suggestion MUST be specific (minimum 20 characters)
5. Suggestions MUST NOT be generic (e.g., "improve clarity" without details)

## Error Handling

### Parsing Errors

```python
try:
    output = ReviewParser.parse(raw_response)
except ReviewParseError as e:
    logger.error(f"Failed to parse review output: {e}")
    # Option 1: Retry with clarified prompt
    # Option 2: Use default low scores and flag for manual review
    output = ReviewAgentOutput(
        thought_process="PARSE_ERROR: " + str(e),
        clarity_grammar_score=1.0,
        logical_coherence_score=1.0,
        mathematical_validity_score=1.0,
        overall_score=1.0,
        suggestions=["SYSTEM: Failed to parse LLM response, manual review required"]
    )
```

### Score Range Violations

If LLM provides scores outside [1, 5]:

```python
def clamp_score(score: float) -> float:
    """Clamp score to valid range with warning."""
    if score < 1.0 or score > 5.0:
        logger.warning(f"Score {score} out of range, clamping to [1.0, 5.0]")
        return max(1.0, min(5.0, score))
    return score
```

## Testing Strategy

### Contract Tests

```python
def test_review_agent_output_format():
    """Test that Review Agent produces expected format."""
    raw_response = """
###thought###
Clarity & Grammar (4.5/5): Well-phrased, minor unit consistency issue.
Logical Coherence (5.0/5): All elements interconnected, complete information.
Mathematical Validity (5.0/5): Solvable with unique answer, all constraints consistent.

###rating_score###
["4.5", "5.0", "5.0"]

###suggestions###
###Specific improvement 1###
Explicitly state answer format: "Express your answer as a decimal rounded to two decimal places"
"""

    parsed = ReviewParser.parse(raw_response)

    assert 1.0 <= parsed.clarity_grammar_score <= 5.0
    assert 1.0 <= parsed.logical_coherence_score <= 5.0
    assert 1.0 <= parsed.mathematical_validity_score <= 5.0
    assert 1.0 <= parsed.overall_score <= 5.0
    assert len(parsed.suggestions) >= 0
```

### Integration Tests

```python
async def test_review_agent_detects_invalid_problem():
    """Test Review Agent catches mathematical contradictions."""
    agent = ReviewAgent(llm_client=mock_llm)

    # Problem with contradiction: probability > 1
    invalid_problem = """
    A bag contains red and blue marbles. The probability of drawing a red marble is 0.6.
    If we add 5 more red marbles, the probability becomes 0.9. If we then add 3 more red
    marbles, the probability becomes 1.2. How many marbles were originally in the bag?
    """

    input_data = ReviewAgentInput(rephrased_question=invalid_problem)
    output = await agent.execute(input_data)

    # Should detect probability > 1 is invalid
    assert output.mathematical_validity_score < 2.0
    assert any("probability" in s.lower() and ("1.2" in s or "> 1" in s) for s in output.suggestions)
```

## Example Execution

### Example 1: High-Quality Problem

**Input**:
```json
{
  "rephrased_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden in meters."
}
```

**Output** (Parsed):
```json
{
  "thought_process": "Clarity & Grammar (4.5/5): The problem statement is clear and grammatically correct. Uses precise mathematical language. Minor point: could specify decimal precision expected.\n\nLogical Coherence & Completeness (5.0/5): All elements are logically interconnected. The length is defined in terms of width (l = 2w + 3), perimeter constraint is given (P = 22), and the question asks for width. Complete information for solving.\n\nMathematical Validity & Solvability (5.0/5): The problem is mathematically sound. Using P = 2(l + w) with l = 2w + 3: 2((2w + 3) + w) = 22, simplifying to 6w + 6 = 22, thus w = 16/6 ≈ 2.67 meters. Unique solution exists, all constraints are consistent.",
  "clarity_grammar_score": 4.5,
  "logical_coherence_score": 5.0,
  "mathematical_validity_score": 5.0,
  "overall_score": 4.83,
  "suggestions": [
    "Explicitly state answer format: 'Express your answer as a decimal rounded to two decimal places' to eliminate ambiguity about whether student should simplify 16/6 or provide decimal."
  ]
}
```

### Example 2: Problem with Mathematical Contradiction

**Input**:
```json
{
  "rephrased_question": "In a class, 60% of students play soccer, 70% play basketball, and 50% play both sports. What percentage of students play neither sport?"
}
```

**Output** (Parsed):
```json
{
  "thought_process": "Clarity & Grammar (4.0/5): Clear wording, grammatically correct.\n\nLogical Coherence (3.0/5): The given percentages create a logical issue when applying set theory.\n\nMathematical Validity & Solvability (1.0/5): CRITICAL ERROR - The problem contains a mathematical contradiction. Using inclusion-exclusion principle: P(S ∪ B) = P(S) + P(B) - P(S ∩ B) = 60% + 70% - 50% = 80%. This means 80% play at least one sport, implying 20% play neither. However, let's verify: if 50% play both, then soccer-only = 60% - 50% = 10%, basketball-only = 70% - 50% = 20%. Total = 10% + 20% + 50% = 80%, leaving 20% for neither. Actually, this IS mathematically consistent! Re-evaluating: The problem is solvable and consistent. Score should be higher.",
  "clarity_grammar_score": 4.0,
  "logical_coherence_score": 5.0,
  "mathematical_validity_score": 5.0,
  "overall_score": 4.67,
  "suggestions": []
}
```

*(Note: This example shows the LLM self-correcting during reasoning - a feature of CoT)*

---

**End of Review Agent Contract**
