# Contract: Rephrase Agent

**Agent Type**: `REPHRASE`
**Purpose**: Transform original math problems into more complex versions while preserving core concepts through systematic escalation protocols.

## Input Contract

### Input Schema

```python
class RephraseAgentInput(BaseModel):
    problem_content: str  # The original problem text
    domain: Optional[MathDomain] = None  # If known, constrains domain identification
    escalation_dimensions: List[str]  # Which dimensions to apply (≥3 required)
    target_difficulty: Optional[int] = None  # Target difficulty 1-5, if specified
```

### Input JSON Example

```json
{
  "problem_content": "What is 2x + 3 = 11?",
  "domain": null,
  "escalation_dimensions": [
    "Multi-stage Transformation",
    "Cross-domain Integration",
    "Real-world Parameterization"
  ],
  "target_difficulty": null
}
```

## Output Contract

### Output Format

The agent MUST respond in this exact plain-text format:

```
Stage 1 #Problem Deconstruction#:
<deconstruction text>

Stage 2 #Escalation Protocol#:
<escalation protocol text>

Stage 3 #Finally Rewritten question#:
<the rephrased problem>
```

### Output Schema (Parsed)

```python
class RephraseAgentOutput(BaseModel):
    stage1_problem_deconstruction: str  # Parsed from "Stage 1 #Problem Deconstruction#:"
    stage2_escalation_protocol: str     # Parsed from "Stage 2 #Escalation Protocol#:"
    stage3_rewritten_question: str      # Parsed from "Stage 3 #Finally Rewritten question#:"

    # Extracted from stage1
    identified_domain: str
    core_competencies: List[str]
    baseline_difficulty: int

    # Extracted from stage2
    applied_dimensions: List[str]  # Should match ≥3 dimensions from input
```

### Output JSON Example (Parsed)

```json
{
  "stage1_problem_deconstruction": "Domain Identification: Algebra\nCore Competencies: Linear equations, variable isolation, basic arithmetic\nBaseline Difficulty: 1 (Recall/Reproduction)",
  "stage2_escalation_protocol": "Selected Dimensions:\n1. Multi-stage Transformation: Convert to perimeter problem requiring multiple steps...\n2. Cross-domain Integration: Combine algebra with basic geometry...\n3. Real-world Parameterization: Embed in rectangle context with realistic constraints...",
  "stage3_rewritten_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal.",
  "identified_domain": "Algebra",
  "core_competencies": ["Linear equations", "variable isolation", "basic arithmetic"],
  "baseline_difficulty": 1,
  "applied_dimensions": [
    "Multi-stage Transformation",
    "Cross-domain Integration",
    "Real-world Parameterization"
  ]
}
```

## Prompt Template

### Full Prompt

```text
Act as an expert mathematics educator specializing in problem complexity escalation. Systematically transform the given problem while preserving its core concepts, using the following framework:

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
```

### Prompt Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{problem_content}` | String | The original problem text | "What is 2x + 3 = 11?" |
| `{escalation_dimensions}` | String | Comma-separated list of required dimensions | "Multi-stage Transformation, Cross-domain Integration, Real-world Parameterization" |

### Prompt Template (Python)

```python
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
    return REPHRASE_PROMPT_TEMPLATE.format(
        problem_content=problem_content,
        escalation_dimensions=", ".join(escalation_dimensions)
    )
```

## Output Parser

### Parser Logic

```python
import re
from typing import Optional

class RephraseParser:
    @staticmethod
    def parse(raw_response: str) -> RephraseAgentOutput:
        """Parse Rephrase Agent's structured response."""

        # Extract stage 1
        stage1_match = re.search(
            r"Stage 1 #Problem Deconstruction#:\s*\n(.*?)(?=Stage 2|$)",
            raw_response,
            re.DOTALL
        )
        stage1_text = stage1_match.group(1).strip() if stage1_match else ""

        # Extract stage 2
        stage2_match = re.search(
            r"Stage 2 #Escalation Protocol#:\s*\n(.*?)(?=Stage 3|$)",
            raw_response,
            re.DOTALL
        )
        stage2_text = stage2_match.group(1).strip() if stage2_match else ""

        # Extract stage 3
        stage3_match = re.search(
            r"Stage 3 #Finally Rewritten question#:\s*\n(.*?)$",
            raw_response,
            re.DOTALL
        )
        stage3_text = stage3_match.group(1).strip() if stage3_match else ""

        # Extract domain from stage1
        domain_match = re.search(r"Domain Identification:\s*(\w+)", stage1_text)
        identified_domain = domain_match.group(1) if domain_match else "Unknown"

        # Extract competencies from stage1
        competencies_match = re.search(
            r"Core Competencies:\s*(.*?)(?=\n|Baseline Difficulty)",
            stage1_text,
            re.DOTALL
        )
        competencies_text = competencies_match.group(1).strip() if competencies_match else ""
        core_competencies = [c.strip() for c in competencies_text.split(",")]

        # Extract baseline difficulty from stage1
        difficulty_match = re.search(r"Baseline Difficulty:\s*(\d)", stage1_text)
        baseline_difficulty = int(difficulty_match.group(1)) if difficulty_match else 3

        # Extract applied dimensions from stage2
        # Look for numbered list items
        dimension_matches = re.findall(r"\d+\.\s+([^:]+):", stage2_text)
        applied_dimensions = [dim.strip() for dim in dimension_matches]

        return RephraseAgentOutput(
            stage1_problem_deconstruction=stage1_text,
            stage2_escalation_protocol=stage2_text,
            stage3_rewritten_question=stage3_text,
            identified_domain=identified_domain,
            core_competencies=core_competencies,
            baseline_difficulty=baseline_difficulty,
            applied_dimensions=applied_dimensions
        )
```

## Validation Rules

### Input Validation

1. `problem_content` MUST be non-empty, minimum 10 characters
2. `escalation_dimensions` MUST contain ≥3 valid dimension names
3. Valid dimension names (exact match):
   - "Multi-stage Transformation"
   - "Cross-domain Integration"
   - "Real-world Parameterization"
   - "Conditional Branching"
   - "Inverse Problem Design"
   - "Uncertainty Integration"
   - "Optimization Extension"

### Output Validation

1. All three stages MUST be present in response
2. `stage3_rewritten_question` MUST be non-empty
3. `identified_domain` MUST be one of: Algebra, Geometry, Calculus, Probability, Number Theory, Combinatorics, Statistics, Trigonometry, Other
4. `baseline_difficulty` MUST be 1-5
5. `applied_dimensions` MUST match ≥3 dimensions from input (fuzzy match acceptable)
6. Rephrased question MUST be longer than original (complexity increase indicator)
7. Rephrased question MUST end with a question mark or imperative (e.g., "Find...", "Calculate...")

## Error Handling

### Parsing Errors

If parser cannot extract required fields:

```python
class RephrasePa rseError(Exception):
    """Raised when Rephrase Agent output cannot be parsed."""
    pass

# Usage
try:
    output = RephraseParser.parse(raw_response)
except RephraseParseError as e:
    # Log error, retry with clarified prompt, or fail gracefully
    logger.error(f"Failed to parse rephrase output: {e}")
    # Option: Retry with additional instruction in prompt
```

### LLM Refusal

If LLM refuses or provides non-mathematical response:

```python
def is_valid_mathematical_problem(question: str) -> bool:
    """Check if question is mathematical."""
    math_keywords = [
        "calculate", "find", "solve", "determine", "compute",
        "what is", "how many", "prove", "simplify",
        "x", "y", "equation", "number", "angle", "area", "volume"
    ]
    return any(keyword in question.lower() for keyword in math_keywords)

# Validation
if not is_valid_mathematical_problem(output.stage3_rewritten_question):
    raise ValueError("Rephrased question is not a valid mathematical problem")
```

## Testing Strategy

### Contract Tests

```python
def test_rephrase_agent_output_format():
    """Test that Rephrase Agent produces expected format."""
    raw_response = """
Stage 1 #Problem Deconstruction#:
Domain Identification: Algebra
Core Competencies: Linear equations, variable isolation
Baseline Difficulty: 1

Stage 2 #Escalation Protocol#:
1. Multi-stage Transformation: Added perimeter calculation step
2. Cross-domain Integration: Combined algebra with geometry
3. Real-world Parameterization: Embedded in garden context

Stage 3 #Finally Rewritten question#:
A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter is 22 meters, find the width.
"""

    parsed = RephraseParser.parse(raw_response)

    assert parsed.identified_domain == "Algebra"
    assert len(parsed.core_competencies) >= 1
    assert 1 <= parsed.baseline_difficulty <= 5
    assert len(parsed.applied_dimensions) >= 3
    assert len(parsed.stage3_rewritten_question) > 0
```

### Integration Tests

```python
async def test_rephrase_agent_end_to_end():
    """Test Rephrase Agent with real LLM."""
    agent = RephraseAgent(llm_client=mock_llm)

    input_data = RephraseAgentInput(
        problem_content="What is 2x + 3 = 11?",
        escalation_dimensions=[
            "Multi-stage Transformation",
            "Cross-domain Integration",
            "Real-world Parameterization"
        ]
    )

    output = await agent.execute(input_data)

    assert output.identified_domain in ["Algebra", "Arithmetic"]
    assert len(output.applied_dimensions) >= 3
    assert len(output.stage3_rewritten_question) > len(input_data.problem_content)
    assert "?" in output.stage3_rewritten_question or "find" in output.stage3_rewritten_question.lower()
```

## Example Execution

### Example 1: Simple Algebra

**Input**:
```json
{
  "problem_content": "Solve for x: 2x + 3 = 11",
  "escalation_dimensions": [
    "Multi-stage Transformation",
    "Real-world Parameterization",
    "Cross-domain Integration"
  ]
}
```

**Output** (Parsed):
```json
{
  "stage1_problem_deconstruction": "Domain Identification: Algebra\nCore Competencies: Linear equations, variable isolation, basic arithmetic\nBaseline Difficulty: 1",
  "stage2_escalation_protocol": "1. Multi-stage Transformation: Convert to multi-step problem requiring perimeter calculation first, then solving for variable\n2. Real-world Parameterization: Embed in garden/construction context with realistic constraints\n3. Cross-domain Integration: Combine algebra with basic geometry (perimeter formula)",
  "stage3_rewritten_question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden in meters.",
  "identified_domain": "Algebra",
  "core_competencies": ["Linear equations", "variable isolation", "basic arithmetic"],
  "baseline_difficulty": 1,
  "applied_dimensions": [
    "Multi-stage Transformation",
    "Real-world Parameterization",
    "Cross-domain Integration"
  ]
}
```

---

**End of Rephrase Agent Contract**
