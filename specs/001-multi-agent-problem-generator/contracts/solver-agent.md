# Contract: Solver Agent

**Agent Type**: `SOLVER`
**Purpose**: Generate detailed, mathematically rigorous solutions with Chain-of-Thought (CoT) reasoning for math problems, showing all intermediate steps and logical judgments.

## Input Contract

### Input Schema

```python
class SolverAgentInput(BaseModel):
    question: str  # The math problem to solve
    problem_id: Optional[UUID] = None  # For reference tracking
```

### Input JSON Example

```json
{
  "question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places.",
  "problem_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Output Contract

### Output Format

The agent MUST respond in this exact plain-text format:

```
###thought###
<step-by-step reasoning process>

###answer###
<final answer>
```

### Output Schema (Parsed)

```python
class SolverAgentOutput(BaseModel):
    thought_process: str  # Parsed from ###thought###, detailed step-by-step reasoning
    final_answer: str     # Parsed from ###answer###, concise final answer (number/fraction)
    intermediate_steps: Optional[List[str]] = None  # Extracted steps for structured access
```

### Output JSON Example (Parsed)

```json
{
  "thought_process": "Step 1: Define variables and given information\n- Let w = width of the garden (in meters)\n- Length l = 2w + 3 (given: \"3 meters more than twice its width\")\n- Perimeter P = 22 meters (given)\n\nStep 2: Recall perimeter formula for rectangle\n- Perimeter = 2(length + width)\n- P = 2(l + w)\n\nStep 3: Substitute the expression for length\n- P = 2((2w + 3) + w)\n- 22 = 2(2w + 3 + w)\n- 22 = 2(3w + 3)\n\nStep 4: Solve for width\n- 22 = 6w + 6\n- 22 - 6 = 6w\n- 16 = 6w\n- w = 16/6\n- w = 8/3\n- w ≈ 2.67 meters (rounded to two decimal places)\n\nStep 5: Verification\n- Width w = 8/3 meters\n- Length l = 2(8/3) + 3 = 16/3 + 9/3 = 25/3 meters\n- Perimeter = 2(25/3 + 8/3) = 2(33/3) = 2(11) = 22 meters ✓\n\nThe answer is 2.67 meters.",
  "final_answer": "2.67",
  "intermediate_steps": [
    "Define variables: w = width, l = 2w + 3, P = 22",
    "Perimeter formula: P = 2(l + w)",
    "Substitute: 22 = 2((2w + 3) + w) = 2(3w + 3)",
    "Simplify: 22 = 6w + 6",
    "Solve: 16 = 6w, w = 16/6 = 8/3",
    "Convert to decimal: w ≈ 2.67 meters",
    "Verify: l = 25/3, P = 2(25/3 + 8/3) = 22 ✓"
  ]
}
```

## Prompt Template

### Full Prompt (GSM8K style)

```text
As a mathematics problem solving expert, analyze and answer the following question.

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
```

### Prompt Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{question}` | String | The math problem to solve | "A rectangular garden has..." |

### Prompt Template (Python)

```python
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

def create_solver_prompt(question: str) -> str:
    return SOLVER_PROMPT_TEMPLATE.format(question=question)
```

## Output Parser

### Parser Logic

```python
import re
from typing import List, Optional

class SolverParser:
    @staticmethod
    def parse(raw_response: str) -> SolverAgentOutput:
        """Parse Solver Agent's structured response."""

        # Extract thought process
        thought_match = re.search(
            r"###thought###\s*\n(.*?)(?=###answer###|$)",
            raw_response,
            re.DOTALL
        )
        if not thought_match:
            raise SolverParseError("Could not find thought process in response")

        thought_process = thought_match.group(1).strip()

        # Extract final answer
        answer_match = re.search(
            r"###answer###\s*\n(.*?)$",
            raw_response,
            re.DOTALL
        )
        if not answer_match:
            raise SolverParseError("Could not find answer in response")

        final_answer = answer_match.group(1).strip()

        # Extract intermediate steps (optional, for structured access)
        intermediate_steps = SolverParser._extract_steps(thought_process)

        return SolverAgentOutput(
            thought_process=thought_process,
            final_answer=final_answer,
            intermediate_steps=intermediate_steps
        )

    @staticmethod
    def _extract_steps(thought_process: str) -> Optional[List[str]]:
        """Extract numbered steps from thought process."""
        # Match "Step N:" patterns
        step_matches = re.findall(
            r"Step \d+:?\s*([^\n]+(?:\n(?!Step \d+)[^\n]+)*)",
            thought_process,
            re.MULTILINE
        )

        if step_matches:
            return [step.strip() for step in step_matches]

        # Fallback: split by double newlines
        paragraphs = [p.strip() for p in thought_process.split('\n\n') if p.strip()]
        return paragraphs if len(paragraphs) > 1 else None


class SolverParseError(Exception):
    """Raised when Solver Agent output cannot be parsed."""
    pass
```

## Validation Rules

### Input Validation

1. `question` MUST be non-empty, minimum 20 characters
2. `question` MUST contain mathematical content (numbers, variables, or mathematical keywords)

### Output Validation

1. `thought_process` MUST be non-empty, minimum 50 characters
2. `thought_process` MUST show intermediate calculations (contain numbers or equations)
3. `final_answer` MUST be non-empty
4. `final_answer` SHOULD be concise (maximum 100 characters, preferably < 20)
5. `final_answer` SHOULD NOT contain explanatory text (just the answer value)

### Answer Format Validation

```python
def validate_answer_format(answer: str) -> bool:
    """Check that answer is concise and properly formatted."""

    # Too long
    if len(answer) > 100:
        logger.warning(f"Answer too long ({len(answer)} chars): {answer[:50]}...")
        return False

    # Contains unnecessary words
    unnecessary_words = [
        "the answer is", "therefore", "thus", "so", "finally",
        "in conclusion", "meters", "units", "approximately"
    ]
    answer_lower = answer.lower()
    if any(word in answer_lower for word in unnecessary_words):
        logger.warning(f"Answer contains explanatory text: {answer}")
        # Don't fail, but warn
        return True

    return True
```

### Completeness Validation

```python
def validate_solution_completeness(thought_process: str, question: str) -> bool:
    """Check that solution addresses the question."""

    # Extract question's target (what to find)
    find_match = re.search(r"find\s+(?:the\s+)?(\w+)", question.lower())
    if find_match:
        target = find_match.group(1)
        if target not in thought_process.lower():
            logger.warning(f"Solution may not address finding '{target}'")
            return False

    # Check for calculation steps
    if not re.search(r'\d+\s*[+\-*/=]\s*\d+', thought_process):
        logger.warning("Solution lacks visible calculations")
        return False

    return True
```

## Error Handling

### Parsing Errors

```python
try:
    output = SolverParser.parse(raw_response)
except SolverParseError as e:
    logger.error(f"Failed to parse solver output: {e}")
    # Retry with clarified prompt emphasizing format
    raise
```

### Incomplete Solutions

If solution is too short or lacks calculations:

```python
if len(output.thought_process) < 100:
    logger.error("Solution thought process too brief")
    # Retry with instruction: "Show ALL intermediate calculation steps"
    raise ValidationError("Solution lacks sufficient detail")
```

## Testing Strategy

### Contract Tests

```python
def test_solver_agent_output_format():
    """Test that Solver Agent produces expected format."""
    raw_response = """
###thought###
Step 1: Define variables
Let w = width. Length l = 2w + 3. Perimeter P = 22.

Step 2: Use perimeter formula
P = 2(l + w) = 2((2w + 3) + w) = 2(3w + 3) = 6w + 6

Step 3: Solve for w
22 = 6w + 6
16 = 6w
w = 16/6 = 8/3 ≈ 2.67

###answer###
2.67
"""

    parsed = SolverParser.parse(raw_response)

    assert len(parsed.thought_process) > 50
    assert "step" in parsed.thought_process.lower()
    assert len(parsed.final_answer) < 50
    assert "2.67" in parsed.final_answer
```

### Integration Tests

```python
async def test_solver_agent_correct_answer():
    """Test that Solver Agent produces mathematically correct answer."""
    agent = SolverAgent(llm_client=real_llm)

    # Problem with known answer
    question = "If 2x + 3 = 11, what is x?"

    input_data = SolverAgentInput(question=question)
    output = await agent.execute(input_data)

    # Check answer is 4
    assert "4" in output.final_answer

    # Check thought process shows steps
    assert "2x" in output.thought_process
    assert "11" in output.thought_process
    assert any(op in output.thought_process for op in ["-", "subtract", "minus"])
```

### Accuracy Tests

For problems with known ground truth:

```python
@pytest.mark.parametrize("question,expected_answer", [
    ("What is 2 + 2?", "4"),
    ("Solve for x: x + 5 = 12", "7"),
    ("Find the area of a rectangle with length 5 and width 3.", "15"),
    (
        "A triangle has sides of length 3, 4, and 5. Is it a right triangle?",
        ["yes", "right triangle", "true"]  # Accept multiple forms
    )
])
async def test_solver_accuracy(question, expected_answer):
    """Test solver produces correct answers for known problems."""
    agent = SolverAgent(llm_client=real_llm)

    output = await agent.execute(SolverAgentInput(question=question))

    if isinstance(expected_answer, list):
        assert any(ans.lower() in output.final_answer.lower() for ans in expected_answer)
    else:
        assert expected_answer in output.final_answer
```

## Example Execution

### Example 1: Algebra Problem

**Input**:
```json
{
  "question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places."
}
```

**Output** (Parsed):
```json
{
  "thought_process": "Step 1: Analyze and Deconstruct\n\nGiven information:\n- The garden is rectangular\n- Length (l) is 3 meters more than twice the width (w): l = 2w + 3\n- Perimeter (P) is 22 meters: P = 22\n- Objective: Find the width w as a decimal rounded to two decimal places\n\nStep 2: Clarify Ambiguities\n\nNo ambiguities detected. The problem clearly defines the relationship between length and width, provides the perimeter, and asks for width.\n\nStep 3: Step-by-Step Derivation\n\nSubstep 3.1: Recall the perimeter formula for a rectangle\nPerimeter = 2 × (length + width)\nP = 2(l + w)\n\nSubstep 3.2: Substitute the expression for length into the perimeter formula\nGiven l = 2w + 3 and P = 22:\n22 = 2((2w + 3) + w)\n\nSubstep 3.3: Simplify the equation\n22 = 2(2w + 3 + w)\n22 = 2(3w + 3)\n22 = 6w + 6\n\nSubstep 3.4: Solve for width w\n22 - 6 = 6w\n16 = 6w\nw = 16/6\nw = 8/3\n\nSubstep 3.5: Convert to decimal\nw = 8 ÷ 3 = 2.666...\nRounded to two decimal places: w ≈ 2.67 meters\n\nStep 4: Verification (optional but recommended)\n\nCheck our answer:\n- Width w = 2.67 meters (using exact 8/3 for verification)\n- Length l = 2(8/3) + 3 = 16/3 + 9/3 = 25/3 meters\n- Perimeter = 2(l + w) = 2(25/3 + 8/3) = 2(33/3) = 2(11) = 22 meters ✓\n\nThe answer is verified correct.",
  "final_answer": "2.67",
  "intermediate_steps": [
    "Analyze and Deconstruct: l = 2w + 3, P = 22, find w",
    "Recall perimeter formula: P = 2(l + w)",
    "Substitute: 22 = 2((2w + 3) + w)",
    "Simplify: 22 = 2(3w + 3) = 6w + 6",
    "Solve: 16 = 6w, w = 16/6 = 8/3",
    "Convert to decimal: w = 8 ÷ 3 ≈ 2.67 meters",
    "Verification: l = 25/3, P = 2(25/3 + 8/3) = 22 ✓"
  ]
}
```

### Example 2: Multi-Case Problem

**Input**:
```json
{
  "question": "A fair six-sided die is rolled twice. What is the probability that the sum of the two rolls is 7?"
}
```

**Output** (Parsed):
```json
{
  "thought_process": "Step 1: Analyze and Deconstruct\n\nGiven:\n- Fair six-sided die (outcomes: 1, 2, 3, 4, 5, 6)\n- Rolled twice\n- Objective: Find P(sum = 7)\n\nStep 2: Clarify Ambiguities\n\nNo ambiguities. \"Fair die\" means each outcome has probability 1/6. Rolls are independent.\n\nStep 3: Step-by-Step Derivation\n\nSubstep 3.1: Identify total possible outcomes\nTwo rolls of a six-sided die:\nTotal outcomes = 6 × 6 = 36\n\nSubstep 3.2: Enumerate all favorable outcomes (sum = 7)\nList all pairs (first roll, second roll) where first + second = 7:\n- (1, 6): 1 + 6 = 7 ✓\n- (2, 5): 2 + 5 = 7 ✓\n- (3, 4): 3 + 4 = 7 ✓\n- (4, 3): 4 + 3 = 7 ✓\n- (5, 2): 5 + 2 = 7 ✓\n- (6, 1): 6 + 1 = 7 ✓\n\nTotal favorable outcomes = 6\n\nSubstep 3.3: Calculate probability\nP(sum = 7) = (Number of favorable outcomes) / (Total possible outcomes)\nP(sum = 7) = 6 / 36 = 1 / 6\n\nStep 4: Final Calculation\n\nP(sum = 7) = 1/6 ≈ 0.1667 (or approximately 16.67%)\n\nExpressing as a simplified fraction: 1/6",
  "final_answer": "1/6",
  "intermediate_steps": [
    "Total possible outcomes: 6 × 6 = 36",
    "Enumerate favorable outcomes: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) = 6 outcomes",
    "Calculate probability: 6/36 = 1/6"
  ]
}
```

---

**End of Solver Agent Contract**
