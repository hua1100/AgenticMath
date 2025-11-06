# Problem Revision Examples

**Feature**: 001-multi-agent-problem-generator
**Source**: AgenticMath Research Paper (Appendix A.4)
**Last Updated**: 2025-11-06

## Overview

This document contains real examples of problem revisions from the AgenticMath system, demonstrating the Rephrase → Review → Revise workflow with actual outputs from the agents. These examples are derived from two mathematical reasoning datasets:

- **GSM8K**: Grade-school math word problems
- **MATH**: Competition mathematics problems

Each example shows:
1. **Original Problem** (or Rephrased Problem from Rephrase Agent)
2. **Review Score** (3 dimensions: Clarity, Logic, Math Validity)
3. **Review Agent Suggestions** (specific improvements)
4. **Revised Problem** (after applying suggestions)

---

## GSM8K Examples

### Example 1: Riddle Competition Problem

**Problem Type**: Arithmetic word problem with relationships
**Domain**: Algebra (linear relationships)
**Complexity Escalation**: Added contextual scenario, introduced decision element

#### Original Seed Problem

```
Ivory got four more riddles than Josh did. Taso got twice as many riddles as Ivory did. If Josh has 8 riddles, how many riddles does Taso have?
```

#### Rephrased Problem (from Rephrase Agent)

```
Josh is participating in a school riddle competition. He has 8 riddles. Ivory, his friend, has four more riddles than Josh. Taso, another competitor, has twice as many riddles as Ivory. If Josh decides to give away 3 of his riddles and that affects the total number of riddles in the competition, how many riddles does Taso have after accounting for Josh's decision?
```

**Escalation Applied**:
- Real-world Parameterization (school competition context)
- Multi-stage Transformation (Josh's decision adds complexity)
- Conditional element (accounting for Josh's decision)

#### Review Scores

| Dimension | Score | Analysis |
|-----------|-------|----------|
| Clarity & Grammar | 3/5 | Ambiguous phrasing about "affects the total" |
| Logical Coherence | 4/5 | Mostly clear relationships, but confusing implication |
| Mathematical Validity | 4/5 | Solvable but unclear if Josh's action changes Taso's count |
| **Overall** | **3.67/5** | **Below threshold (4.5)** |

#### Review Agent Suggestions

1. **Clarify Independence**: "Clarify the influence of Josh giving away his riddles on Taso's total. For instance, specify that Taso's riddle count is independent and remains unchanged despite Josh's actions. This removes ambiguity regarding the competition's overall structure."

2. **Rephrase Ambiguous Statement**: "Instead of saying 'and that affects the total number of riddles in the competition,' use 'Josh's decision to give away his riddles does not change how many riddles Taso has.' This direct statement enhances comprehension and ensures readers understand that Taso's initial count remains constant."

3. **Provide Context**: "Consider providing context as to whether the riddles given away affect only Josh or extend to others. A statement like 'regardless of how many riddles Josh gives away, Taso's number of riddles is based on the original count' would maintain logical clarity."

#### Revised Problem (after Revise Agent)

```
Josh is participating in a school riddle competition. He has 8 riddles. Ivory, his friend, has four more riddles than Josh. Taso, another competitor, has twice as many riddles as Ivory. Josh's decision to give away 3 of his riddles does not change how many riddles Taso has. Regardless of how many riddles Josh gives away, Taso's number of riddles is based on the original count. How many riddles does Taso have?
```

**Expected Answer**: 24 riddles
- Josh: 8
- Ivory: 8 + 4 = 12
- Taso: 12 × 2 = 24

**Key Improvements**:
- ✅ Explicitly states independence of Taso's count
- ✅ Removes ambiguous "affects the total" phrase
- ✅ Clarifies that calculations use original counts
- ✅ Mathematical validity improved to 5/5

---

### Example 2: Truck Loading Problem

**Problem Type**: Work rate problem with geometric calculation
**Domain**: Algebra + Geometry (cross-domain)
**Complexity Escalation**: Multi-stage calculation, geometric component added

#### Original/Rephrased Problem

```
Stella and Twinkle are filling a truck with a capacity of 6000 stone blocks at the rate of 250 blocks per hour per person. They work for four hours without any breaks, after which they are joined by 6 other people who work at the same rate. Calculate the total time taken to fill the truck. Additionally, if the blocks are in the shape of cubes with a side length of 2 units, determine the area of the base of the truck that would hold these blocks when filled to capacity. Provide the total hours taken and the area of the base in square units.
```

#### Further Rephrased (for clarity)

```
Stella and Twinkle are filling a truck with a capacity of 6000 cubic blocks at the rate of 250 blocks per hour per person. They work for four hours without any breaks. After this, they are joined by 6 additional people who work at the same rate. Calculate the total time taken to fill the truck.

To begin, calculate the total number of blocks filled by both Stella and Twinkle during their initial 4 hours. Next, determine how long it will take for all workers (Stella, Twinkle, and the 6 additional people) to finish filling the truck.

Additionally, the blocks are in the shape of cubes with a side length of 2 units. Calculate the area of the rectangular base of the truck needed to accommodate the cubes when filled to its full capacity, expressed in square units. Provide the total hours taken and the area of the base in square units.
```

#### Review Scores

| Dimension | Score | Analysis |
|-----------|-------|----------|
| Clarity & Grammar | 4/5 | Good but could be more concise |
| Logical Coherence | 4/5 | Clear steps but transitions could be smoother |
| Mathematical Validity | 4/5 | Solvable but geometric part needs clarification |
| **Overall** | **4.0/5** | **Below threshold (4.5)** |

#### Review Agent Suggestions

1. **Simplify Initial Sentence**: "Rephrase the initial sentence to: 'Stella and Twinkle are filling a truck with a capacity of 6000 cubic blocks, working at a rate of 250 blocks per hour each for four hours without breaks.' This enhances clarity by simplifying the phrase structure."

2. **Clarify Task Transitions**: "Provide a clearer description of the mathematical operations to carry out after working four hours. For instance, 'After 4 hours of work, determine the total blocks filled, and then calculate the time required for the remaining blocks with the help of the additional workers.' This improves logical coherence by clarifying the task transition."

3. **Specify Output Format**: "Clearly request the output format by stating, 'Finally, report both the total hours taken to fill the truck and the area of the rectangular base in square units,' ensuring the conclusion is definitive and straightforward for the reader to apprehend."

#### Revised Problem

```
Stella and Twinkle are filling a truck with a capacity of 6000 cubic blocks, working at a rate of 250 blocks per hour each for four hours without breaks. After 4 hours of work, determine the total blocks filled by both Stella and Twinkle, and then calculate the time required for the remaining blocks with the help of 6 additional workers who work at the same rate. Finally, report both the total hours taken to fill the truck and the area of the rectangular base in square units needed to accommodate the blocks when filled to its full capacity, given that each block is a cube with a side length of 2 units.
```

**Expected Answer**:
- **Time**: 6 hours total
  - First 4 hours: 2 workers × 250 blocks/hour × 4 hours = 2000 blocks
  - Remaining: 4000 blocks / (8 workers × 250 blocks/hour) = 2 hours
  - Total: 4 + 2 = 6 hours
- **Base Area**: Depends on arrangement assumptions (problem needs more constraints for unique answer)

**Key Improvements**:
- ✅ Simplified opening sentence
- ✅ Clearer step-by-step instructions
- ✅ Explicit output format requirements
- ⚠️ Note: Geometric part still needs arrangement assumptions for unique answer

---

### Example 3: Chase Problem (Rabbit and Cat)

**Problem Type**: Relative motion with terrain effects
**Domain**: Algebra (rates, distance)
**Complexity Escalation**: Terrain penalty, coordinate system mention

#### Rephrased Problem

```
Tom's rabbit can run at a speed of 25 miles per hour, while his cat runs at 20 miles per hour. If the cat gets a 15-minute head start, during which it covers a distance on a flat path, determine the time (in hours) it will take the rabbit to catch up with the cat assuming that for every mile, the rabbit encounters terrain that slows it down by 1 minute for every 5 miles traveled. Additionally, calculate the total distance (in square miles) covered by both animals until the rabbit catches up, assuming their paths can be represented as lines on a coordinate plane.
```

#### Further Rephrased (with coordinate clarification)

```
Tom's rabbit can run at a speed of 25 miles per hour, while his cat runs at a speed of 20 miles per hour. The cat gets a 15-minute head start, covering a distance on a flat path during this time. Determine the time (in hours) it will take for the rabbit to catch up to the cat, defined as the moment when both animals have traveled the same linear distance from the starting point. Consider that for every mile the rabbit travels, it encounters terrain that slows its speed by an additional minute for every 5 miles traveled. Finally, calculate the total distance traveled (in miles) by both animals until the rabbit catches up with the cat.
```

#### Review Scores

| Dimension | Score | Analysis |
|-----------|-------|----------|
| Clarity & Grammar | 3/5 | Complex terrain penalty description |
| Logical Coherence | 4/5 | Mostly clear but terrain effect confusing |
| Mathematical Validity | 3/5 | Unclear how terrain penalty accumulates |
| **Overall** | **3.33/5** | **Below threshold (4.5)** |

#### Review Agent Suggestions

1. **Streamline Question**: "State: 'Tom's rabbit runs at 25 mph and his cat at 20 mph. The cat has a 15-minute head start. When will the rabbit catch up to the cat, considering that every mile the rabbit travels adds an extra minute to its speed?' This revision reduces complexity and provides clearer instructions."

2. **Clarify Terrain Impact**: "Instead of stating that its speed will decrease, specify how to adjust the time taken due to the terrain. For instance, rephrase the condition regarding the rabbit's speed to enhance understanding, such as, 'For every 5 miles the rabbit runs, add 1 extra minute to its travel time.'"

3. **Simplify Problem**: "Remove unnecessary details and ensure the question leads to a unique solution. Consider separating the catch-up time and total distance calculations into distinct questions or minimizing the effects of terrain to make the problem more straightforward. This way, students can focus on the primary aspects of the problem without layers of complexity that introduce potential for confusion."

#### Revised Problem

```
Tom's rabbit runs at 25 mph and his cat at 20 mph. The cat has a 15-minute head start. For every 5 miles the rabbit travels, add an extra minute to its travel time. How long (in hours) will it take for the rabbit to catch up to the cat? Also, calculate the total distance (in miles) traveled by both animals when the rabbit catches up.
```

**Expected Answer** (approximate):
- Cat's head start distance: 20 mph × 0.25 hours = 5 miles
- Rabbit catches up: Solving with terrain penalty requires iterative calculation
- [Exact answer depends on how penalty accumulates]

**Key Improvements**:
- ✅ Simplified terrain penalty description
- ✅ Removed confusing coordinate plane reference
- ✅ Clearer question structure
- ✅ Separated two calculation requests

---

## MATH Dataset Examples

### Example 4: Marble Expected Value Problem

**Problem Type**: Probability with conditional drawing rules
**Domain**: Probability, Combinatorics
**Complexity Escalation**: Conditional branching, replacement rules

#### Original Seed Problem

```
I have 5 marbles numbered 1 through 5 in a bag. Suppose I take out two different marbles at random. What is the expected value of the sum of the numbers on the marbles?
```

#### Rephrased Problem

```
You have a bag containing 5 marbles numbered 1 through 5. You randomly draw two different marbles. If marble 1 is drawn first, then the drawn marbles are put back in the bag, and you draw again. If the first marble drawn is not 1, you keep it and draw the second marble without replacement. What is the expected value of the sum of the numbers on the marbles drawn, given that if you draw an odd-numbered marble first, you will always draw marble 2 next, while if you draw an even-numbered marble first, you will draw the next higher number available if possible? Calculate the sum for each scenario and give the overall expected value.
```

**Escalation Applied**:
- Conditional Branching (different rules based on first draw)
- Multi-stage Transformation (replacement vs. no replacement)
- Layered constraints (odd vs. even rules)

#### Review Scores

| Dimension | Score | Analysis |
|-----------|-------|----------|
| Clarity & Grammar | 3/5 | Overly complex conditional structure |
| Logical Coherence | 4/5 | Rules are defined but hard to follow |
| Mathematical Validity | 3/5 | Unique answer exists but complexity is excessive |
| **Overall** | **3.33/5** | **Below threshold (4.5)** |

#### Review Agent Suggestions

1. **Simplify Language**: "Instead of saying 'if marble 1 is drawn first, then the drawn marbles are put back in the bag,' you could say 'if marble 1 is drawn first, put the marbles back and draw again.' This succinctly conveys the same information without ambiguity."

2. **Define All Scenarios Explicitly**: "Clearly define what happens in all scenarios after each draw. It would be beneficial to write separate scenarios or cases explicitly (e.g., drawing 1, drawing an odd number, drawing an even number), ensuring that all potential outcomes are evident to the reader to aid in understanding and solving the problem."

#### Revised Problem

```
You have a bag with 5 marbles numbered 1 through 5. You will randomly draw two different marbles according to the following rules:

1. If you draw marble 1 first, put it back in the bag and draw again.
2. If the first marble drawn is not marble 1, you keep that marble and draw a second marble without putting the first back.

Additionally:
- If the first marble drawn is odd (3 or 5), you will draw marble 2 next.
- If the first marble drawn is even (2 or 4), you will draw the next higher number available (for example, if you draw 2 first, you will draw 3 next; if you draw 4, you will draw 5 next).

Calculate the expected value of the sum of the numbers on the marbles drawn, considering each scenario.
```

**Expected Answer** (calculation required):
- Need to enumerate all scenarios with their probabilities
- Scenario 1: Draw 1 first → redraw (probability 1/5)
- Scenario 2: Draw odd (3 or 5) first → draw 2 next
- Scenario 3: Draw even (2 or 4) first → draw next higher
- Expected value = sum of (probability × sum) for all scenarios

**Key Improvements**:
- ✅ Numbered list format for clarity
- ✅ Explicit case enumeration
- ✅ Examples provided for even-number rule
- ✅ Clearer structure improves readability

---

### Example 5: Number Combination Problem

**Problem Type**: Combinatorics with digit constraints
**Domain**: Number Theory, Combinatorics
**Complexity Escalation**: Real-world context, constraint specification

#### Original Seed Problem

```
Find the number of ordered pairs of positive integers (a,b) such that a+b=1000 and neither a nor b has a zero digit.
```

#### Rephrased Problem

```
In a community project, two teams need to collectively gather exactly 1000 units of resources. Let (a) represent the units collected by Team A and (b) represent those collected by Team B, such that (a + b = 1000). If neither team can collect resources in amounts represented by a number containing the digit zero, how many ordered combinations of (a, b) can the teams realistically plan for their collection, considering all above constraints?
```

**Escalation Applied**:
- Real-world Parameterization (community project context)
- Maintained mathematical constraint (no zero digits)

#### Review Scores

| Dimension | Score | Analysis |
|-----------|-------|----------|
| Clarity & Grammar | 4/5 | Good contextualization but needs precision |
| Logical Coherence | 4/5 | Clear constraints but terminology could be sharper |
| Mathematical Validity | 3/5 | Valid but "ordered combinations" is ambiguous |
| **Overall** | **3.67/5** | **Below threshold (4.5)** |

#### Review Agent Suggestions

1. **Clarify Zero-Digit Constraint**: "Clarify the constraint regarding the digit zero by explicitly stating that both (a) and (b) can only consist of the digits 1-9. This can help eliminate any potential confusion about what is meant by not containing the digit zero."

2. **Define "Ordered Combinations"**: "Define what is meant by 'ordered combinations'. It could be interpreted in different ways—does it mean different pairings of (a) and (b) that total 1000, or is it simply asking for the number of distinct pairs? Providing examples or additional context could further enhance comprehension."

3. **Use Mathematical Language**: "Instead of stating 'the teams realistically plan for their collection,' consider specifying that this refers to the mathematical combinations that satisfy all conditions. This would reinforce the focus of the question on mathematics rather than a broader planning context."

#### Revised Problem

```
In a community project, two teams need to collectively gather exactly 1000 units of resources. Let (a) represent the units collected by Team A and (b) represent those collected by Team B, such that (a + b = 1000). Both (a) and (b) must be composed exclusively of the digits 1 through 9, meaning neither can include the digit zero. How many distinct ordered pairs ((a, b)) satisfy this condition, ensuring all constraints are met?
```

**Expected Answer**: 738 ordered pairs
- Total pairs where a+b=1000: 999 pairs (a from 1 to 999)
- Pairs where a has zero digit: count numbers 1-999 with zero = 261
- Pairs where b has zero digit: count numbers 1-999 with zero = 261
- Pairs where both have zero: overcounted intersection
- Using inclusion-exclusion: Answer = 738

**Key Improvements**:
- ✅ Explicitly states "digits 1 through 9"
- ✅ Uses precise term "ordered pairs" with notation ((a,b))
- ✅ Focuses on mathematical interpretation
- ✅ Removes ambiguous "realistically plan" phrase

---

## Common Improvement Patterns

### Pattern 1: Clarifying Ambiguous Conditions

**Problem**: Vague statements that could be interpreted multiple ways
**Examples**:
- "affects the total number" → "does not change Taso's count"
- "slows it down" → "add 1 extra minute for every 5 miles"

**Solution**: Use explicit, quantitative statements

### Pattern 2: Separating Complex Instructions

**Problem**: Long sentences with multiple clauses
**Examples**:
- Single sentence with "after which" clauses
- Nested conditional statements

**Solution**: Use numbered lists, bullet points, or separate sentences

### Pattern 3: Removing Unnecessary Complexity

**Problem**: Added complexity doesn't serve learning objectives
**Examples**:
- Coordinate plane reference in chase problem (not needed)
- "Square miles" when asking for linear distance

**Solution**: Strip to essential mathematical elements

### Pattern 4: Explicit Scenario Enumeration

**Problem**: Conditional logic hidden in prose
**Examples**:
- Marble drawing rules
- Work rate changes

**Solution**: Enumerate cases explicitly with formatting

### Pattern 5: Specifying Output Format

**Problem**: Unclear what form the answer should take
**Examples**:
- "Provide the time and area" → "Report both X and Y in [units]"
- Missing decimal precision requirements

**Solution**: State exact output format and units

---

## Usage as Test Cases

These examples can be used for:

### 1. Integration Testing

Test the complete pipeline:

```python
@pytest.mark.parametrize("example_id", ["gsm8k_1", "gsm8k_2", "gsm8k_3", "math_1", "math_2"])
async def test_complete_pipeline_with_real_examples(example_id):
    """Test full pipeline with documented examples."""
    example = load_example(example_id)

    result = await pipeline.process_problem(
        problem_content=example["seed_problem"],
        quality_threshold=4.5
    )

    # Verify rephrasing occurred
    assert result.final_problem.content != example["seed_problem"]

    # Verify quality threshold reached
    assert result.final_assessment.overall_score >= 4.5

    # Verify solution generated
    assert result.solution is not None
```

### 2. Review Agent Calibration

Compare agent scores with documented scores:

```python
def test_review_agent_scores_match_examples():
    """Verify Review Agent produces scores similar to documented examples."""
    example = load_example("gsm8k_1_rephrased")

    result = review_agent.execute(example["rephrased_problem"])

    # Allow some tolerance (±0.5)
    assert abs(result.clarity_grammar_score - 3.0) <= 0.5
    assert abs(result.logical_coherence_score - 4.0) <= 0.5
    assert abs(result.mathematical_validity_score - 4.0) <= 0.5
```

### 3. Revise Agent Effectiveness

Test that revisions improve scores:

```python
def test_revise_agent_improves_scores():
    """Verify Revise Agent produces improvements matching examples."""
    example = load_example("gsm8k_1")

    # Initial review
    review1 = review_agent.execute(example["rephrased_problem"])
    assert review1.overall_score < 4.5

    # Apply revisions
    revised = revise_agent.execute(example["rephrased_problem"], review1.suggestions)

    # Re-review
    review2 = review_agent.execute(revised.revised_question)
    assert review2.overall_score > review1.overall_score
```

### 4. Regression Testing

Ensure system maintains quality over time:

```python
def test_no_regression_on_known_examples():
    """Ensure system still handles documented examples correctly."""
    for example in load_all_examples():
        result = await pipeline.process_problem(example["seed_problem"])

        # Should reach quality threshold
        assert result.final_status == "SUCCESS"
        assert result.final_assessment.overall_score >= 4.5

        # Should not exceed max iterations (efficiency check)
        assert result.iteration_count <= 5
```

---

## JSON Format for Test Data

Example format for storing these cases:

```json
{
  "example_id": "gsm8k_1_riddles",
  "dataset": "GSM8K",
  "domain": "Algebra",
  "seed_problem": "Ivory got four more riddles than Josh did. Taso got twice as many riddles as Ivory did. If Josh has 8 riddles, how many riddles does Taso have?",
  "escalation_dimensions": [
    "Real-world Parameterization",
    "Multi-stage Transformation"
  ],
  "rephrased_problem": "Josh is participating in a school riddle competition...",
  "review_iteration_1": {
    "scores": [3, 4, 4],
    "overall": 3.67,
    "suggestions": [
      "Clarify the influence of Josh giving away his riddles...",
      "Instead of saying 'and that affects the total'...",
      "Consider providing context as to whether..."
    ]
  },
  "revised_problem": "Josh is participating in a school riddle competition...",
  "review_iteration_2": {
    "scores": [5, 5, 5],
    "overall": 5.0,
    "suggestions": []
  },
  "final_problem": "Josh is participating in a school riddle competition...",
  "expected_answer": "24",
  "solution_steps": [
    "Josh has 8 riddles",
    "Ivory = Josh + 4 = 8 + 4 = 12",
    "Taso = Ivory × 2 = 12 × 2 = 24"
  ]
}
```

---

## Conclusion

These examples demonstrate:

1. **Rephrase Agent** successfully adds complexity while preserving mathematical intent
2. **Review Agent** identifies real quality issues with specific, actionable suggestions
3. **Revise Agent** effectively applies improvements to raise quality scores
4. **Iterative refinement** (1-2 cycles) typically sufficient to reach quality threshold

**Key Takeaway**: The multi-agent system consistently improves problem quality through structured, measurable improvements rather than arbitrary changes.

---

**Next Steps**:
- Create test data files in JSON format from these examples
- Implement integration tests using these documented cases
- Use as benchmark for LLM model selection (which models handle these effectively?)
- Extend with more examples from diverse mathematical domains
