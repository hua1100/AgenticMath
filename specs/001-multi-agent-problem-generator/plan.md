# Implementation Plan: Multi-Agent Math Problem Generator

**Branch**: `001-multi-agent-problem-generator` | **Date**: 2025-11-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-multi-agent-problem-generator/spec.md`

## Summary

Build a multi-agent system with four specialized agents (Rephrase, Review, Revise, Solver) that transforms student-uploaded math problems into high-quality, pedagogically effective practice problems. The system maintains conceptual similarity while increasing complexity through systematic escalation protocols, validates quality through iterative review-revise cycles (threshold ≥ 4.5), and generates detailed Chain-of-Thought solutions for both original and rephrased problems.

**Technical Approach**:
- Agent-based architecture with four distinct agents, each with specialized prompts
- Orchestration layer manages agent workflow: Rephrase → Review → (Revise loop if needed) → Solver
- LLM-powered agents using structured output parsing
- Persistent storage for problems, assessments, solutions, and complete workflow traceability

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- LangChain or similar agent framework for LLM orchestration
- OpenAI API / Anthropic Claude API for LLM backend
- Pydantic for structured data validation and parsing
- SQLite/PostgreSQL for persistent storage
**Storage**: SQLite for development, PostgreSQL for production (stores Problems, QualityAssessments, Solutions, RephraseSessions, Agent execution logs)
**Testing**: pytest with contract tests for agent output formats, integration tests for full workflows
**Target Platform**: Python CLI initially, API server (FastAPI) for production
**Project Type**: Single project (Python backend + CLI)
**Performance Goals**:
- <60 seconds average for full pipeline (Rephrase → Review → Revise loop → Solution)
- Support concurrent processing of multiple problems
- <2 seconds per individual agent invocation
**Constraints**:
- LLM token limits (typically 4K-8K for input, need to handle long problems gracefully)
- Quality threshold τ_rev = 4.5 by default (configurable 3.0-5.0)
- Maximum 5 review-revise iterations to prevent infinite loops
- Must preserve mathematical correctness (zero tolerance for invalid problems passing threshold)
**Scale/Scope**:
- Initial: Single-user CLI processing 10-50 problems per session
- Production: Multi-user API supporting 100+ concurrent users, 1000+ problems per day
- Agent execution logs retained for traceability and training data

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle 1: Educational Value First
- **Status**: PASS
- **Justification**: Every component prioritizes learning - Rephrase agent maintains conceptual similarity, Review agent evaluates pedagogical clarity, Solver agent demonstrates reasoning. Quality threshold ensures only educationally valuable problems proceed.

### ✅ Principle 2: Mathematical Correctness and Clarity
- **Status**: PASS
- **Justification**: Review agent explicitly evaluates Mathematical Validity & Solvability (FR-013 detects contradictions). Zero invalid problems pass threshold (SC-006). Solver agent shows all steps preventing ambiguity.

### ✅ Principle 3: Conceptual Consistency
- **Status**: PASS
- **Justification**: Rephrase agent preserves core concepts while varying surface features (FR-006). System verifies >95% conceptual alignment (SC-002). Problem deconstruction tracks domain and competencies.

### ✅ Principle 4: Testability and Validation
- **Status**: PASS
- **Justification**: All agents produce structured, parseable outputs (###thought###, ###rating_score###, etc.). Quality scores are measurable. Contract tests verify output formats. Success criteria include measurable metrics (SC-001 through SC-010).

### ✅ Principle 5: Simplicity and Maintainability
- **Status**: PASS with JUSTIFICATION
- **Potential Violation**: Four agents might seem complex
- **Justification**: Each agent has single responsibility (rephrase/review/revise/solve). Separation mirrors natural human workflow for problem quality assurance. Attempting to combine agents would create monolithic, untestable components. Complexity is essential, not accidental.
- **Simpler Alternative Rejected**: Single "do everything" agent would be impossible to test individual quality dimensions, couldn't iterate on specific weaknesses, and would violate single-responsibility principle.

### ✅ Principle 6: Explainability and Transparency
- **Status**: PASS
- **Justification**: Every agent outputs explicit reasoning (###thought###). Review agent provides detailed suggestions. System logs all agent decisions (FR-029). Complete workflow traceability (SC-009). Educators can inspect why problems were rephrased certain ways.

### 🚦 Overall Assessment: APPROVED
All principles satisfied. The four-agent architecture is justified by distinct responsibilities and testability requirements. Proceed to implementation.

## Project Structure

### Documentation (this feature)

```
specs/001-multi-agent-problem-generator/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: LLM framework comparison, prompt engineering research
├── data-model.md        # Phase 1: Entity schemas, database design
├── quickstart.md        # Phase 1: Getting started guide
├── contracts/           # Phase 1: Agent input/output contracts
│   ├── rephrase-agent.md
│   ├── review-agent.md
│   ├── revise-agent.md
│   └── solver-agent.md
└── tasks.md             # Phase 2: Implementation task list
```

### Source Code (repository root)

```
AgenticMath/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py    # Abstract base class for all agents
│   │   ├── rephrase_agent.py
│   │   ├── review_agent.py
│   │   ├── revise_agent.py
│   │   └── solver_agent.py
│   ├── models/              # Data models (Pydantic)
│   │   ├── __init__.py
│   │   ├── problem.py
│   │   ├── quality_assessment.py
│   │   ├── solution.py
│   │   ├── rephrase_session.py
│   │   └── agent_execution.py
│   ├── orchestration/       # Workflow orchestration
│   │   ├── __init__.py
│   │   ├── pipeline.py      # Main pipeline coordinator
│   │   └── iteration_manager.py  # Manages review-revise loops
│   ├── storage/             # Database layer
│   │   ├── __init__.py
│   │   ├── database.py      # Database connection and setup
│   │   └── repositories/    # Data access objects
│   │       ├── __init__.py
│   │       ├── problem_repository.py
│   │       ├── assessment_repository.py
│   │       └── solution_repository.py
│   ├── prompts/             # LLM prompt templates
│   │   ├── __init__.py
│   │   ├── rephrase_prompt.py
│   │   ├── review_prompt.py
│   │   ├── revise_prompt.py
│   │   └── solver_prompt.py
│   ├── parsers/             # Output parsers for structured responses
│   │   ├── __init__.py
│   │   ├── rephrase_parser.py
│   │   ├── review_parser.py
│   │   ├── revise_parser.py
│   │   └── solver_parser.py
│   ├── cli/                 # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── logging.py
│       └── validators.py
├── tests/
│   ├── contract/            # Contract tests for agent outputs
│   │   ├── test_rephrase_contract.py
│   │   ├── test_review_contract.py
│   │   ├── test_revise_contract.py
│   │   └── test_solver_contract.py
│   ├── integration/         # Integration tests for full workflows
│   │   ├── test_full_pipeline.py
│   │   ├── test_review_revise_loop.py
│   │   └── test_solution_generation.py
│   └── unit/                # Unit tests for individual components
│       ├── test_agents/
│       ├── test_models/
│       ├── test_parsers/
│       └── test_orchestration/
├── examples/                # Example problems and outputs
│   ├── algebra_example.json
│   ├── geometry_example.json
│   └── calculus_example.json
├── .specify/                # SDD framework (already exists)
├── specs/                   # Feature specs (already exists)
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Python project config
├── README.md               # Project README
└── .env.example            # Environment variables template
```

**Structure Decision**: Single project structure selected because:
- All components are tightly coupled (agents → orchestration → storage)
- Shared data models across all agents
- No separate frontend (CLI only for MVP, API can be added to same project)
- Deployment as single service simplifies operations
- Python's module system provides sufficient separation

## Complexity Tracking

*No constitution violations requiring justification.*

### Architectural Note: Why Four Agents?

While four agents might initially seem complex, this design is justified:

| Design Aspect | Rationale | Simpler Alternative & Why Rejected |
|---------------|-----------|-----------------------------------|
| Separate Review + Revise agents | Review evaluates (read-only), Revise modifies (write). Different prompts and objectives. Enables focused testing. | Combined "ReviewAndRevise" agent would conflate evaluation and modification, making it impossible to test evaluation accuracy independently. Cannot improve one without affecting the other. |
| Separate Rephrase + Solver agents | Rephrase transforms problems, Solver generates solutions. Completely different outputs and success criteria. | Single "DoEverything" agent would need two modes, doubling prompt complexity. Testing which mode failed becomes ambiguous. Violates single responsibility. |
| Four agents vs. configuration | Each agent's prompt is fundamentally different in structure and purpose, not just parameter variations. | Parameterized single agent would require massive prompt with conditional logic, reducing clarity and making prompt engineering nearly impossible. |

**Conclusion**: Four agents is the *simplest* architecture that maintains clear responsibilities, testability, and prompt clarity. Reducing agent count would increase *accidental* complexity in prompts and testing.

---

## Next Steps

### Phase 0: Research (to be documented in research.md)
1. Compare LLM frameworks (LangChain vs. LlamaIndex vs. plain API calls)
2. Evaluate LLM providers (OpenAI GPT-4 vs. Anthropic Claude vs. open-source models)
3. Research prompt engineering best practices for structured output
4. Investigate output parsing libraries and validation approaches
5. Review mathematical validation techniques

### Phase 1: Design (to be documented in data-model.md, contracts/, quickstart.md)
1. Design database schema for all entities
2. Define agent input/output contracts (exact JSON/text formats)
3. Design orchestration workflow with state machine diagram
4. Create quickstart guide with example workflows
5. Define configuration schema (quality threshold, escalation dimensions, etc.)

### Phase 2: Implementation (to be documented in tasks.md)
- Generated by `/speckit.tasks` command
- Will include task breakdown by user story
- Organized for incremental delivery (P1 → P2 → P3)
