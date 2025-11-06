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
- **Agent Framework**: CrewAI (MIT licensed, simple API for role-based multi-agent orchestration)
- **LLM Backend**: OpenAI GPT-4.1 (GPT-4o/GPT-4 Turbo) for optimal math problem quality
- **OCR**: PaddleOCR (Apache 2.0, open-source Chinese OCR with math symbol support)
- **Data Validation**: Pydantic for structured data validation and parsing
- **Image Processing**: PIL/OpenCV for photo preprocessing
- **Storage**: SQLite/PostgreSQL for persistent storage

**Storage**: SQLite for development, PostgreSQL for production (stores Problems, QualityAssessments, Solutions, RephraseSessions, Agent execution logs, UploadedImages)

**Testing**: pytest with contract tests for agent output formats, integration tests for full workflows

**Target Platform**: Python CLI initially, API server (FastAPI) for production

**Project Type**: Single project (Python backend + CLI)

**Performance Goals**:
- <60 seconds average for full pipeline (Photo OCR → Rephrase → Review → Revise loop → Solution)
- Support concurrent processing of multiple problems
- <2 seconds per individual agent invocation (excluding LLM API latency)
- OCR processing: <3 seconds per image (CPU mode)

**Constraints**:
- LLM token limits (GPT-4.1: 128K context window, typically 4K-8K per agent call)
- Quality threshold τ_rev = 4.5 by default (configurable 3.0-5.0)
- Maximum 5 review-revise iterations to prevent infinite loops
- Must preserve mathematical correctness (zero tolerance for invalid problems passing threshold)
- OCR accuracy target: ≥85% for printed Chinese math problems
- Photo upload: Max 10MB per image, JPEG/PNG formats

**Scale/Scope**:
- Initial: Single-user CLI processing 10-50 problems per session
- Production: Multi-user API supporting 100+ concurrent users, 1000+ problems per day
- Agent execution logs retained for traceability and training data
- OCR logs retained for accuracy monitoring and improvement

**Cost Considerations**:
- GPT-4.1 API: ~$0.05 per problem (including 2 iterations)
- Daily budget (100 problems): ~$5/day, $150/month
- Trade-off: Higher cost for premium problem quality (education value first)

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
│   ├── ocr/                 # OCR processing
│   │   ├── __init__.py
│   │   ├── image_preprocessor.py  # Image cleaning and enhancement
│   │   ├── text_extractor.py      # PaddleOCR integration
│   │   ├── diagram_detector.py    # Detect and describe diagrams
│   │   └── ocr_pipeline.py        # Complete OCR workflow
│   ├── models/              # Data models (Pydantic)
│   │   ├── __init__.py
│   │   ├── problem.py
│   │   ├── quality_assessment.py
│   │   ├── solution.py
│   │   ├── rephrase_session.py
│   │   ├── uploaded_image.py      # Image metadata
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
│   │       ├── solution_repository.py
│   │       └── image_repository.py
│   ├── prompts/             # LLM prompt templates (Traditional Chinese)
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

### ✅ Phase 0: Research (COMPLETED - see research.md)

**研究結論** (詳見 [research.md](./research.md))：

**確定技術棧**：
- **Agent 框架**: CrewAI (MIT, 角色明確、API 簡潔)
- **OCR**: PaddleOCR (Apache 2.0, 中文優秀、CPU 可用、支援 LaTeX)
- **LLM**: OpenAI GPT-4.1 (GPT-4o/GPT-4 Turbo, 題目品質優先)
- **數據庫**: PostgreSQL (生產), SQLite (開發)
- **API 框架**: FastAPI

**關鍵決策**：
1. **Agent 框架**: 選擇 CrewAI 而非 AutoAgent/LangGraph
   - AutoAgent: 零代碼框架，不適合精確控制迭代邏輯
   - LangGraph: 功能強大但學習曲線陡峭，MVP 過度設計
   - CrewAI: 最佳平衡（簡單、角色明確、符合需求）

2. **OCR 技術**: 選擇 PaddleOCR 而非 DeepSeek OCR
   - PaddleOCR: 96-98% 中文準確度，CPU 可運行，部署簡單
   - DeepSeek OCR: 需 A100-40G GPU，MVP 成本過高（生產階段可考慮）

3. **LLM 選擇**: GPT-4.1 而非 DeepSeek-V3
   - 原因：**題目品質決定教育價值**，這是系統核心價值
   - 成本：每題 ~$0.05 (¥0.35)，每月 100 題/天約 $150
   - 權衡：品質優先 > 成本優化（符合憲章 Principle 1）

4. **開源原則遵循**：
   - Agent 框架 ✅ 開源 (CrewAI - MIT)
   - OCR ✅ 開源 (PaddleOCR - Apache 2.0)
   - LLM ⚠️ 商業 API（教育品質優先，權衡後接受）

**備選方案**：
- 若 GPT-4.1 成本超出預算 → 降級至 DeepSeek-V3
- 若 PaddleOCR 準確度不足 → 升級至 DeepSeek OCR（需 GPU）
- 若 CrewAI 迭代控制複雜 → 遷移至 LangGraph

### 🔄 Phase 1: Design (IN PROGRESS - to be documented in data-model.md, contracts/, quickstart.md)

**待完成任務**：
1. ✅ 更新 `spec.md` - 加入照片上傳需求 (User Story 0)
2. ✅ 更新 `data-model.md` - 加入 UploadedImage 實體
3. ✅ 創建 `contracts/image-extraction-agent.md` - OCR 合約
4. ✅ 更新所有 Agent contracts - 改為繁體中文
5. 🔄 設計 OCR → Agent 流程的狀態機
6. 🔄 創建 quickstart guide - 含照片上傳範例
7. 🔄 定義配置 schema - 加入 OCR 設定

### ⏭️ Phase 2: Implementation (to be documented in tasks.md)
- Generated by `/speckit.tasks` command
- Will include task breakdown by user story
- Organized for incremental delivery (P0: OCR → P1: Agents → P2: Solution → P3: Config)
