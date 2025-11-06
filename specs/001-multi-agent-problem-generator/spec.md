# Feature Specification: Multi-Agent Math Problem Generator

**Feature Branch**: `001-multi-agent-problem-generator`
**Created**: 2025-11-06
**Status**: Draft
**Input**: User description: "學生可以上傳錯誤或概念不清楚的題目，生成概念近似，但能幫助學習者發現概念、策略或模式，明確、邏輯一致且沒有錯誤的問題"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Problem Upload and Quality-Controlled Rephrasing (Priority: P1) 🎯 MVP

A student uploads a math problem they find confusing or have made mistakes on. The system analyzes the problem, increases its complexity through systematic escalation protocols, and iterates through review-revise cycles until producing a high-quality rephrased problem (quality score ≥ 4.5) that maintains conceptual similarity while helping the learner discover patterns and strategies.

**Why this priority**: This is the core value proposition - transforming problematic student questions into pedagogically effective practice problems. Without this, no other features matter.

**Independent Test**: Student submits a simple algebra problem → System returns a rephrased problem with higher complexity that passed quality review (score ≥ 4.5) → Problem maintains the same mathematical concept but with enhanced difficulty and clarity.

**Acceptance Scenarios**:

1. **Given** a student uploads "What is 2x + 3 = 11?", **When** the system processes it through Rephrase → Review → (Revise if needed) agents, **Then** it produces a problem like "A rectangle's length is 3 units more than twice its width. If the perimeter is 22 units, find the width" with quality score ≥ 4.5

2. **Given** a rephrased problem receives review score < 4.5, **When** the Revise agent processes improvement suggestions, **Then** the revised problem is re-evaluated by Review agent until score ≥ 4.5 or maximum iterations reached

3. **Given** a student uploads a problem in a specific domain (e.g., Geometry), **When** the system rephrases it, **Then** the rephrased problem preserves the core domain and competencies while increasing complexity through ≥3 escalation dimensions

4. **Given** the Review agent evaluates a rephrased problem, **When** scoring across three dimensions, **Then** it provides detailed ratings for Clarity & Grammar, Logical Coherence, and Mathematical Validity, plus specific improvement suggestions

---

### User Story 2 - Solution Generation with Chain-of-Thought Reasoning (Priority: P2)

For both original seed problems and refined rephrased problems that pass quality review, the system generates detailed, step-by-step solutions using Chain-of-Thought (CoT) reasoning that demonstrates mathematical rigor and pedagogical clarity.

**Why this priority**: Solutions are essential for learning - students need to see correct reasoning paths. However, the problem generation itself (P1) must work first before solutions add value.

**Independent Test**: Given a high-quality problem (score ≥ 4.5) → System generates solution with explicit thought process showing all intermediate steps → Solution includes final numerical answer.

**Acceptance Scenarios**:

1. **Given** a high-quality rephrased problem, **When** the Solver agent processes it, **Then** it outputs a solution with ###thought### (detailed step-by-step derivation) and ###answer### (concise final answer)

2. **Given** a problem with ambiguous wording, **When** the Solver agent analyzes it, **Then** it explicitly states its interpretation and reasoning before proceeding with calculations

3. **Given** a problem requiring multi-case analysis, **When** the Solver generates solution, **Then** it clearly lists all cases considered, shows intermediate calculations, and uses appropriate formulas for each step

4. **Given** both the original seed problem and its rephrased version, **When** solutions are generated, **Then** both problems receive detailed CoT solutions demonstrating the conceptual connection between them

---

### User Story 3 - Configurable Quality Thresholds and Complexity Control (Priority: P3)

Educators or advanced users can configure the quality score threshold (τ_rev), select specific escalation dimensions, and adjust the difficulty baseline to customize problem generation for different learning contexts.

**Why this priority**: This is an enhancement for advanced use cases. The system should work with reasonable defaults first (P1, P2) before adding configurability.

**Independent Test**: User sets custom quality threshold to 4.0 → System accepts problems with score ≥ 4.0 → User selects specific escalation dimensions (e.g., only Multi-stage Transformation and Cross-domain Integration) → System respects these constraints.

**Acceptance Scenarios**:

1. **Given** an educator sets quality threshold to 4.0, **When** problems are reviewed, **Then** only problems scoring ≥ 4.0 proceed to solution generation

2. **Given** a user specifies 2 escalation dimensions (e.g., "Multi-stage Transformation" and "Real-world Parameterization"), **When** the Rephrase agent processes a problem, **Then** it applies exactly those dimensions

3. **Given** a user sets baseline difficulty level to 3 (using Krathwohl's Cognitive Rigor Index), **When** rephrasing a problem, **Then** the target difficulty escalates appropriately from that baseline

4. **Given** different subject domains (Algebra, Geometry, Calculus), **When** problems are processed, **Then** the system correctly identifies the domain and applies domain-appropriate escalation strategies

---

### Edge Cases

- **What happens when a problem is mathematically unsolvable?**
  - Review agent must detect this through "Mathematical Validity & Solvability" criterion and assign very low score, triggering Revise agent to fix contradictions

- **What happens when review-revise iterations exceed maximum attempts without reaching threshold?**
  - System should flag the problem as "Unable to achieve quality threshold" and provide diagnostic information to user

- **What happens when uploaded problem is too vague or not mathematical?**
  - Rephrase agent's Stage 1 should identify domain and competencies; if unable to identify mathematical content, system should request clarification

- **What happens when multiple valid solution paths exist?**
  - Solver agent should either: (a) show one complete solution path with note about alternatives, or (b) explicitly state "multiple valid approaches exist" in thought process

- **What happens with extremely long problems or solutions?**
  - System should handle token limits gracefully, potentially summarizing intermediate steps while preserving mathematical correctness

## Requirements *(mandatory)*

### Functional Requirements

#### Problem Input & Analysis
- **FR-001**: System MUST accept text-based mathematical problems as input from students
- **FR-002**: System MUST identify the mathematical domain (Algebra, Geometry, Calculus, etc.) of input problems
- **FR-003**: System MUST identify core competencies (theorems, formulas, methods) required for input problems
- **FR-004**: System MUST assess baseline difficulty using Krathwohl's Cognitive Rigor Index (Level 1-5)

#### Problem Rephrase Agent
- **FR-005**: Rephrase Agent MUST apply ≥3 complexity escalation dimensions from: Multi-stage Transformation, Cross-domain Integration, Real-world Parameterization, Conditional Branching, Inverse Problem Design, Uncertainty Integration, Optimization Extension
- **FR-006**: Rephrase Agent MUST preserve core mathematical concepts while varying surface features
- **FR-007**: Rephrase Agent MUST ensure rephrased problems are definitive mathematical problems with unique, specific answers
- **FR-008**: Rephrase Agent MUST output in structured format: Stage 1 (Problem Deconstruction), Stage 2 (Escalation Protocol), Stage 3 (Finally Rewritten question)

#### Problem Review Agent
- **FR-009**: Review Agent MUST evaluate problems on three dimensions, each scored 1-5:
  - Clarity & Grammar
  - Logical Coherence & Completeness
  - Mathematical Validity & Solvability
- **FR-010**: Review Agent MUST calculate an overall quality score (1-5) from dimension scores
- **FR-011**: Review Agent MUST generate specific, detailed improvement suggestions when score < threshold
- **FR-012**: Review Agent MUST output in structured format: ###thought###, ###rating_score###, ###suggestions###
- **FR-013**: Review Agent MUST detect mathematical contradictions (e.g., probability > 1, impossible geometric constraints) and flag them explicitly

#### Problem Revise Agent
- **FR-014**: Revise Agent MUST process improvement suggestions from Review Agent
- **FR-015**: Revise Agent MUST optimize problems to improve scores across all three quality dimensions
- **FR-016**: Revise Agent MUST output in structured format: ###revised_question###, ###revision_notes###
- **FR-017**: Revise Agent MUST preserve the original mathematical intent while addressing quality issues

#### Review-Revise Iteration Loop
- **FR-018**: System MUST iterate through Review → Revise cycles until quality score ≥ τ_rev (default: 4.5)
- **FR-019**: System MUST limit maximum review-revise iterations to prevent infinite loops (suggested: 5 iterations)
- **FR-020**: System MUST track and log all iteration attempts with scores and suggestions

#### Solution Generation Agent
- **FR-021**: Solver Agent MUST generate solutions for all problems with quality score ≥ τ_rev
- **FR-022**: Solver Agent MUST use Chain-of-Thought (CoT) reasoning showing:
  - Problem deconstruction with given data, variables, constraints, objectives
  - Clarification of any ambiguities
  - Step-by-step derivation with all intermediate calculations
  - Final calculation and answer
- **FR-023**: Solver Agent MUST output in structured format: ###thought###, ###answer###
- **FR-024**: Solver Agent MUST show all intermediate steps without skipping calculations
- **FR-025**: Solver Agent MUST list all cases/combinations for multi-case analysis problems
- **FR-026**: Solver Agent MUST generate solutions for both original seed problems and rephrased problems

#### Quality Assurance
- **FR-027**: System MUST verify that rephrased problems maintain conceptual similarity to original problems
- **FR-028**: System MUST ensure all generated problems are mathematically correct and solvable
- **FR-029**: System MUST log all agent decisions, scores, and transformations for traceability

#### Configuration (for User Story 3)
- **FR-030**: System SHOULD allow configuration of quality threshold τ_rev (default: 4.5, range: 3.0-5.0)
- **FR-031**: System SHOULD allow selection of specific escalation dimensions
- **FR-032**: System SHOULD allow configuration of baseline difficulty level

### Key Entities

- **Problem**: Represents a mathematical problem with attributes:
  - id (unique identifier)
  - content (problem text)
  - domain (e.g., Algebra, Geometry, Calculus)
  - competencies (list of required concepts/methods)
  - baseline_difficulty (1-5 using Krathwohl's index)
  - source (original/rephrased/revised)
  - parent_id (reference to original problem if rephrased)

- **QualityAssessment**: Represents a review evaluation with attributes:
  - problem_id (reference to Problem)
  - clarity_grammar_score (1-5)
  - logical_coherence_score (1-5)
  - mathematical_validity_score (1-5)
  - overall_score (1-5)
  - thought_process (detailed reasoning)
  - suggestions (list of improvement recommendations)
  - timestamp

- **Solution**: Represents a generated solution with attributes:
  - problem_id (reference to Problem)
  - thought_process (detailed CoT reasoning)
  - final_answer (concise numerical/analytical answer)
  - intermediate_steps (list of calculation steps)
  - timestamp

- **RephraseSession**: Represents a complete rephrase workflow with attributes:
  - original_problem_id
  - rephrased_problem_id
  - escalation_dimensions (list of applied dimensions)
  - iteration_count (number of review-revise cycles)
  - quality_assessments (list of QualityAssessment)
  - final_status (success/max_iterations_exceeded)
  - timestamp

- **Agent**: Represents an agent's execution with attributes:
  - agent_type (rephrase/review/revise/solver)
  - input (problem or suggestions)
  - output (structured response)
  - prompt_template (the prompt used)
  - execution_time
  - timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully rephrases ≥90% of valid input problems into high-quality problems (score ≥ 4.5) within 5 review-revise iterations

- **SC-002**: Rephrased problems maintain >95% conceptual alignment with original problems (measured by domain and competency preservation)

- **SC-003**: Generated solutions contain complete step-by-step reasoning for 100% of problems (no skipped steps, all intermediate calculations shown)

- **SC-004**: Review Agent's quality scores correlate with human expert ratings at ≥0.85 Pearson correlation coefficient

- **SC-005**: System processes a single problem through full pipeline (Rephrase → Review → Revise loop → Solution) in <60 seconds on average

- **SC-006**: Zero mathematically invalid problems pass quality threshold (all problems with score ≥ 4.5 are mathematically correct and solvable)

- **SC-007**: Rephrased problems demonstrate measurable complexity increase: ≥3 escalation dimensions applied, difficulty level increases by ≥1 point on Krathwohl's index

- **SC-008**: For problems requiring multiple iterations, 100% of revision notes explicitly address the suggestions from prior review

- **SC-009**: System maintains complete traceability: 100% of agent decisions, scores, and transformations are logged and retrievable

- **SC-010**: Student comprehension improvement: In pilot testing, students practicing with rephrased problems show ≥20% improvement in similar problem-solving tasks compared to control group using only original problems
