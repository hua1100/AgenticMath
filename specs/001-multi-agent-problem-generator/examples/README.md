# Problem Revision Examples

This directory contains real-world examples from the AgenticMath research demonstrating the multi-agent problem generation and refinement workflow.

## Contents

### Documentation

- **[problem-revision-examples.md](problem-revision-examples.md)**: Detailed analysis of 5 example problems showing the complete Rephrase → Review → Revise → Solution workflow with commentary on improvement patterns.

### Test Data (JSON Format)

Ready-to-use test cases in JSON format:

1. **[gsm8k_example_1_riddles.json](gsm8k_example_1_riddles.json)**
   - **Type**: Arithmetic word problem with relationships
   - **Domain**: Algebra
   - **Iterations**: 2
   - **Key Issue**: Ambiguous conditional (Josh giving away riddles)
   - **Resolution**: Explicit independence statement

2. **[gsm8k_example_2_truck.json](gsm8k_example_2_truck.json)**
   - **Type**: Work rate + geometry
   - **Domain**: Algebra + Geometry (cross-domain)
   - **Iterations**: 2
   - **Key Issue**: Complex sentence structure, unclear task transitions
   - **Resolution**: Simplified phrasing, numbered steps

3. **[math_example_1_marbles.json](math_example_1_marbles.json)**
   - **Type**: Conditional probability
   - **Domain**: Probability + Combinatorics
   - **Iterations**: 2
   - **Key Issue**: Overly complex nested conditionals
   - **Resolution**: Numbered rules list, explicit case enumeration

## JSON Schema

Each JSON file follows this structure:

```json
{
  "example_id": "unique_identifier",
  "dataset": "GSM8K | MATH",
  "domain": "Primary mathematical domain(s)",
  "problem_type": "Description of problem type",
  "seed_problem": "Original problem text",
  "escalation_dimensions": ["Dimension 1", "Dimension 2", "..."],
  "rephrased_problem": "Problem after Rephrase Agent",
  "review_iteration_1": {
    "scores": {
      "clarity_grammar": 1-5,
      "logical_coherence": 1-5,
      "mathematical_validity": 1-5
    },
    "overall_score": 1-5,
    "suggestions": ["Suggestion 1", "Suggestion 2", "..."],
    "passed_threshold": true | false
  },
  "revised_problem": "Problem after Revise Agent",
  "review_iteration_2": { /* ... */ },
  "final_problem": "Final accepted problem (score ≥ threshold)",
  "expected_answer": "Answer or calculation notes",
  "solution_steps": ["Step 1", "Step 2", "..."],
  "key_improvements": ["Improvement 1", "Improvement 2", "..."],
  "metadata": {
    "difficulty_increase": "Low | Medium | High",
    "iteration_count": 1-5,
    "final_status": "SUCCESS | MAX_ITERATIONS_EXCEEDED",
    "source": "Reference to source",
    "notes": "Additional notes"
  }
}
```

## Usage

### For Integration Testing

```python
import json
from pathlib import Path

def load_example(example_id: str):
    """Load a test example by ID."""
    examples_dir = Path("specs/001-multi-agent-problem-generator/examples")

    # Map IDs to files
    file_map = {
        "gsm8k_1": "gsm8k_example_1_riddles.json",
        "gsm8k_2": "gsm8k_example_2_truck.json",
        "math_1": "math_example_1_marbles.json"
    }

    file_path = examples_dir / file_map[example_id]
    with open(file_path) as f:
        return json.load(f)

# Usage
example = load_example("gsm8k_1")
print(example["seed_problem"])
print(example["final_problem"])
```

### Test Complete Pipeline

```python
@pytest.mark.parametrize("example_id", ["gsm8k_1", "gsm8k_2", "math_1"])
async def test_pipeline_with_examples(example_id):
    """Test full pipeline with documented examples."""
    example = load_example(example_id)

    result = await pipeline.process_problem(
        problem_content=example["seed_problem"],
        escalation_dimensions=example["escalation_dimensions"],
        quality_threshold=4.5
    )

    # Verify successful completion
    assert result.final_status == "SUCCESS"
    assert result.final_assessment.overall_score >= 4.5

    # Verify solution generated
    assert result.solution is not None
    assert len(result.solution.thought_process) > 100

    # Verify reasonable iteration count
    assert result.iteration_count <= 5
```

### Test Review Agent Calibration

```python
def test_review_scores_match_examples():
    """Compare Review Agent scores with documented examples."""
    example = load_example("gsm8k_1")

    # Review the rephrased problem
    result = review_agent.execute(
        ReviewAgentInput(rephrased_question=example["rephrased_problem"])
    )

    # Expected scores from documentation
    expected = example["review_iteration_1"]["scores"]

    # Allow tolerance of ±0.5
    assert abs(result.clarity_grammar_score - expected["clarity_grammar"]) <= 0.5
    assert abs(result.logical_coherence_score - expected["logical_coherence"]) <= 0.5
    assert abs(result.mathematical_validity_score - expected["mathematical_validity"]) <= 0.5
```

### Test Revise Agent Effectiveness

```python
async def test_revise_improves_scores():
    """Verify Revise Agent produces measurable improvements."""
    example = load_example("gsm8k_1")

    # Initial review
    review1 = await review_agent.execute(
        ReviewAgentInput(rephrased_question=example["rephrased_problem"])
    )

    # Apply revisions
    revised = await revise_agent.execute(
        ReviseAgentInput(
            rephrased_question=example["rephrased_problem"],
            suggestions=review1.suggestions
        )
    )

    # Re-review
    review2 = await review_agent.execute(
        ReviewAgentInput(rephrased_question=revised.revised_question)
    )

    # Verify improvement
    assert review2.overall_score > review1.overall_score
    assert review2.overall_score >= 4.5
```

### Benchmark LLM Models

```python
@pytest.mark.parametrize("model", ["gpt-4", "gpt-3.5-turbo", "claude-3-opus"])
async def test_model_performance_on_examples(model):
    """Compare different LLM models on documented examples."""
    pipeline = MathProblemPipeline(llm_model=model)

    results = []
    for example_id in ["gsm8k_1", "gsm8k_2", "math_1"]:
        example = load_example(example_id)
        result = await pipeline.process_problem(example["seed_problem"])

        results.append({
            "example_id": example_id,
            "model": model,
            "success": result.final_status == "SUCCESS",
            "iterations": result.iteration_count,
            "final_score": result.final_assessment.overall_score
        })

    # Save benchmark results
    save_benchmark(model, results)
```

## Common Improvement Patterns

Based on these examples, common issues and resolutions include:

### 1. Ambiguous Conditionals
**Problem**: Vague "if-then" statements
**Solution**: Explicit independence or dependency statements

### 2. Complex Sentence Structure
**Problem**: Long sentences with multiple clauses
**Solution**: Break into numbered steps or bullet points

### 3. Unclear Output Requirements
**Problem**: Missing format or unit specifications
**Solution**: "Report both X and Y in [units]"

### 4. Nested Logic
**Problem**: Multiple conditional branches in prose
**Solution**: Explicit case enumeration with examples

### 5. Unnecessary Complexity
**Problem**: Added details that don't serve learning
**Solution**: Strip to essential mathematical elements

## Adding New Examples

To add new examples from production use:

1. Run the pipeline and save the complete session:
```python
result = await pipeline.process_problem(problem)
session = result.to_dict()
```

2. Convert to JSON format following the schema above

3. Add to this directory with descriptive filename

4. Update README.md with new example

5. Create corresponding test cases

## Statistics

Current examples:
- **Total Examples**: 3 (5 documented in markdown)
- **Datasets**: GSM8K (2), MATH (1)
- **Domains**: Algebra (2), Algebra+Geometry (1), Probability (1)
- **Avg Iterations**: 2.0
- **Success Rate**: 100%
- **Avg Final Score**: 4.94/5.0

## Source

These examples are derived from:
**AgenticMath: Agentic Mathematical Problem Solving via Refinement and Reflection**
Appendix A.4: Examples of Problem Revision
- A.4.1: GSM8K examples
- A.4.2: MATH examples

## Future Work

Planned additions:
- [ ] More diverse domain coverage (Geometry, Calculus, etc.)
- [ ] Examples with MAX_ITERATIONS_EXCEEDED status
- [ ] Examples with mathematical contradictions detected
- [ ] Multi-language examples (if supported)
- [ ] Performance benchmarks across LLM models
