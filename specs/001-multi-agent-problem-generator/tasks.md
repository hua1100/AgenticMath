# Implementation Tasks: Multi-Agent Math Problem Generator

**Feature Branch**: `001-multi-agent-problem-generator`
**Created**: 2025-11-06
**Status**: Planning
**Based on**: [spec.md](./spec.md), [plan.md](./plan.md), [data-model.md](./data-model.md)

## Overview

This document organizes implementation tasks by User Story priority (P0 → P1 → P2 → P3), following incremental delivery principles. Each task includes acceptance criteria, estimated complexity, and dependencies.

## Task Organization by User Story

```
P0: Photo Upload & OCR (Entry point) ← Must complete first
  ↓
P1: Problem Rephrase + Review/Revise Loop (Core value)
  ↓
P2: Solution Generation (Educational content)
  ↓
P3: Configuration & Advanced Features
```

---

## Phase 0: Project Setup (Foundation)

### Task 0.1: Initialize Project Structure ⭐ CRITICAL

**Priority**: P0 (Blocker)
**Complexity**: 2 hours
**Dependencies**: None
**Assignee**: TBD

**Description**: Set up the Python project with all required directories, configuration files, and dependencies.

**Acceptance Criteria**:
- [ ] Project structure matches plan.md layout
- [ ] `pyproject.toml` configured with Python 3.11+
- [ ] `requirements.txt` includes all dependencies:
  - PaddleOCR 2.7.0
  - OpenAI SDK (for GPT-4.1)
  - CrewAI (MIT)
  - Pydantic 2.0+
  - SQLAlchemy 2.0+
  - FastAPI (for future API)
  - Pillow, OpenCV-python
  - pytest, pytest-asyncio
- [ ] `.env.example` created with all configuration variables
- [ ] `README.md` with setup instructions
- [ ] `.gitignore` configured for Python

**Implementation Steps**:
1. Create directory structure (src/, tests/, specs/, .specify/)
2. Initialize `pyproject.toml` and `requirements.txt`
3. Create `.env.example` with OCR, LLM, and database config
4. Set up Git repository and initial commit
5. Document setup in README.md

**Verification**:
```bash
python --version  # ≥ 3.11
pip install -r requirements.txt  # No errors
pytest tests/  # Passes (even if no tests yet)
```

---

### Task 0.2: Database Schema Setup

**Priority**: P0
**Complexity**: 3 hours
**Dependencies**: Task 0.1
**Assignee**: TBD

**Description**: Implement the database schema defined in data-model.md using SQLAlchemy and Alembic.

**Acceptance Criteria**:
- [ ] SQLAlchemy models created for all 6 entities:
  - UploadedImage
  - Problem
  - QualityAssessment
  - Solution
  - RephraseSession
  - AgentExecution
- [ ] Alembic migration system initialized
- [ ] Initial migration script creates all tables with constraints
- [ ] All indexes defined (foreign keys, performance indexes)
- [ ] Database connection utility created (`src/storage/database.py`)
- [ ] Works with both SQLite (dev) and PostgreSQL (prod)

**Implementation Steps**:
1. Create SQLAlchemy models in `src/models/`
2. Initialize Alembic: `alembic init alembic`
3. Configure `alembic.ini` with database URL
4. Generate initial migration: `alembic revision --autogenerate -m "Initial schema"`
5. Review and test migration: `alembic upgrade head`
6. Create database connection utility

**Verification**:
```bash
alembic upgrade head  # Creates all tables
python -c "from src.storage.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"  # Shows 6 tables
```

---

## Phase 1: User Story 0 - Photo Upload & OCR (P0) 🎯

### Task 1.1: Image Upload & Validation

**Priority**: P0
**Complexity**: 4 hours
**Dependencies**: Task 0.2
**Related**: FR-001, FR-002, SC-006

**Description**: Implement photo upload handling with validation (format, size, content).

**Acceptance Criteria**:
- [ ] Accepts JPEG/PNG uploads (max 10MB)
- [ ] Validates file format and size
- [ ] Stores files in `/uploads/YYYY/MM/` structure
- [ ] Generates unique filenames (UUID-based)
- [ ] Creates UploadedImage database record
- [ ] Returns image_id to caller
- [ ] Handles upload errors gracefully

**Implementation**:
- File: `src/ocr/image_uploader.py`
- Tests: `tests/unit/test_image_uploader.py`

**Verification**:
```python
from src.ocr.image_uploader import upload_image
result = upload_image(file_bytes, filename="test.jpg")
assert result["success"] == True
assert result["image_id"] is not None
```

---

### Task 1.2: Image Preprocessing Pipeline

**Priority**: P0
**Complexity**: 5 hours
**Dependencies**: Task 1.1
**Related**: FR-003, SC-005

**Description**: Implement image preprocessing to improve OCR accuracy (rotation correction, noise reduction, contrast enhancement).

**Acceptance Criteria**:
- [ ] Auto-detects and corrects rotation (±15° tolerance)
- [ ] Applies noise reduction (cv2.fastNlMeansDenoisingColored)
- [ ] Enhances contrast (cv2.equalizeHist or CLAHE)
- [ ] Logs which preprocessing steps were applied
- [ ] Rotation correction success rate ≥95%
- [ ] Processing time < 1 second per image

**Implementation**:
- File: `src/ocr/image_preprocessor.py`
- Tests: `tests/unit/test_image_preprocessor.py`

**Verification**:
```python
from src.ocr.image_preprocessor import preprocess_image
result = preprocess_image(image_path, config)
assert "rotation_corrected" in result["preprocessing_applied"]
assert result["processing_time_ms"] < 1000
```

---

### Task 1.3: PaddleOCR Integration

**Priority**: P0
**Complexity**: 6 hours
**Dependencies**: Task 1.2
**Related**: FR-004, FR-005, FR-006, SC-001, SC-002

**Description**: Integrate PaddleOCR for Traditional Chinese text extraction with math symbol support.

**Acceptance Criteria**:
- [ ] Initializes PaddleOCR with `lang='chinese_cht'`, `use_angle_cls=True`
- [ ] Extracts text with confidence scores
- [ ] Returns text regions with bounding boxes
- [ ] Calculates average confidence score
- [ ] Text extraction accuracy ≥85% (printed)
- [ ] Processing time <3 seconds (CPU mode)
- [ ] Handles empty/no-text images gracefully

**Implementation**:
- File: `src/ocr/text_extractor.py`
- Tests: `tests/unit/test_text_extractor.py`
- Test data: `tests/fixtures/images/` (sample math problem photos)

**Verification**:
```python
from src.ocr.text_extractor import extract_text
result = extract_text(image_path)
assert result["confidence_score"] >= 0.85
assert result["processing_time_ms"] < 3000
assert len(result["text_regions"]) > 0
```

---

### Task 1.4: Diagram Analysis & Understanding

**Priority**: P0
**Complexity**: 10 hours
**Dependencies**: Task 1.3
**Related**: FR-007, SC-003

**Description**: Detect diagrams in images and analyze them to understand diagram type, math concepts, and features. This analysis will be used to generate similar problems with different difficulty levels.

**Two-Stage Approach**:
1. **Basic Detection** (OpenCV): Fast detection of diagram presence and location
2. **Deep Analysis** (Vision LLM): Understand diagram content, math concepts, and features

**Acceptance Criteria**:

**Stage 1 - Basic Detection (已完成 ✅)**:
- [x] Detects geometric figures (triangles, circles, rectangles)
- [x] Returns diagram bounding boxes
- [x] Detection success rate ≥80% for geometric figures
- [x] Handles images with no diagrams (returns empty)

**Stage 2 - Deep Analysis (已完成 ✅)**:
- [x] Uses GPT-4 Vision to analyze diagram content
- [x] Identifies diagram type (right_triangle, equilateral_triangle, circle, etc.)
- [x] Extracts key math concepts (pythagorean_theorem, similarity, trigonometry, etc.)
- [x] Extracts diagram features (vertices, labeled sides, angles, etc.)
- [x] Provides difficulty indicators for problem generation
- [x] Analysis accuracy ≥85% (with mocked tests, will verify with real API)
- [x] Only calls Vision LLM when diagram is detected (cost optimization verified in tests)

**Implementation**:
- File: `src/ocr/diagram_detector.py` (基礎檢測，已完成)
- File: `src/ocr/diagram_analyzer.py` (深度分析，已完成 ✅)
- File: `src/ocr/diagram_processor.py` (整合模組，已完成 ✅)
- Tests: `tests/unit/test_diagram_detector.py` (已完成)
- Tests: `tests/unit/test_diagram_analyzer.py` (已完成 ✅)
- Tests: `tests/unit/test_diagram_processor.py` (已完成 ✅)
- Test data: Images with geometry diagrams

**Output Format**:
```json
{
  "contains_diagram": true,
  "diagram_regions": [...],
  "diagram_analysis": {
    "diagram_type": "right_triangle",
    "key_concepts": ["pythagorean_theorem", "trigonometry"],
    "features": {
      "vertices": ["A", "B", "C"],
      "right_angle_at": "C",
      "labeled_sides": {"AB": "10", "AC": "6"},
      "unlabeled_sides": ["BC"]
    },
    "difficulty_indicators": {
      "has_labels": true,
      "requires_calculation": true,
      "complexity": "medium"
    }
  }
}
```

**Verification**:
```python
from src.ocr.diagram_processor import process_diagram_for_ocr

# Process image with diagram analysis
result = process_diagram_for_ocr(image_path, enable_deep_analysis=True)

if result["contains_diagram"]:
    assert result["diagram_analysis"] is not None
    assert "diagram_type" in result["diagram_analysis"]
    assert "key_concepts" in result["diagram_analysis"]
    assert "features" in result["diagram_analysis"]
    assert "difficulty_indicators" in result["diagram_analysis"]
```

**Note**: 圖表生成功能（diagram generation）將在題目生成階段實現，不在 OCR 階段。

---

### Task 1.5: OCR Pipeline Integration

**Priority**: P0
**Complexity**: 4 hours
**Dependencies**: Tasks 1.1, 1.2, 1.3, 1.4
**Related**: SC-011

**Description**: Integrate all OCR components into a single pipeline matching the image-extraction-agent.md contract.

**Acceptance Criteria**:
- [ ] Orchestrates: upload → preprocess → OCR → diagram detection
- [ ] Returns output matching contract format
- [ ] Updates UploadedImage record with results
- [ ] Logs AgentExecution record (agent_type=OCR)
- [ ] Total pipeline time <5 seconds
- [ ] Handles all error cases with proper error codes

**Implementation**:
- File: `src/ocr/ocr_pipeline.py`
- Tests: `tests/integration/test_ocr_pipeline.py`

**Verification**:
```python
from src.ocr.ocr_pipeline import OCRPipeline
pipeline = OCRPipeline()
result = pipeline.process(image_id, file_path)
assert result["success"] == True
assert result["extracted_text"] != ""
```

---

### Task 1.6: Problem Creation from OCR

**Priority**: P0
**Complexity**: 3 hours
**Dependencies**: Task 1.5
**Related**: FR-013

**Description**: Create Problem entity from OCR-extracted text.

**Acceptance Criteria**:
- [ ] Creates Problem with `source=ORIGINAL`, `source_type=OCR`
- [ ] Links Problem to UploadedImage (`uploaded_image_id`)
- [ ] Identifies domain using simple keyword matching (placeholder for P1)
- [ ] Sets baseline competencies (placeholder for P1)
- [ ] Stores in database
- [ ] Returns problem_id

**Implementation**:
- File: `src/orchestration/problem_creator.py`
- Tests: `tests/unit/test_problem_creator.py`

**Verification**:
```python
from src.orchestration.problem_creator import create_problem_from_ocr
problem = create_problem_from_ocr(ocr_result, image_id)
assert problem.source == ProblemSource.ORIGINAL
assert problem.source_type == SourceType.OCR
assert problem.uploaded_image_id == image_id
```

---

## Phase 2: User Story 1 - Problem Rephrase + Quality Control (P1) 🎯

### Task 2.1: LLM Client Setup (GPT-4.1)

**Priority**: P1
**Complexity**: 3 hours
**Dependencies**: Task 0.1
**Related**: Technical Context (GPT-4.1)

**Description**: Create OpenAI API client for GPT-4.1 (GPT-4o/GPT-4 Turbo) with retry logic.

**Acceptance Criteria**:
- [ ] Configures OpenAI client with API key from env
- [ ] Uses `gpt-4o` or `gpt-4-turbo` model
- [ ] Implements exponential backoff retry (max 3 retries)
- [ ] Handles rate limiting (429 errors)
- [ ] Logs token usage for cost tracking
- [ ] Supports temperature and max_tokens configuration

**Implementation**:
- File: `src/agents/llm_client.py`
- Tests: `tests/unit/test_llm_client.py` (with mocking)

**Verification**:
```python
from src.agents.llm_client import LLMClient
client = LLMClient()
response = client.chat_completion(messages=[...])
assert response["content"] is not None
```

---

### Task 2.2: Rephrase Agent Implementation

**Priority**: P1
**Complexity**: 8 hours
**Dependencies**: Task 2.1
**Related**: FR-017, FR-018, FR-019, FR-020, Contract: rephrase-agent.md

**Description**: Implement Rephrase Agent using CrewAI and GPT-4.1, following 3-stage escalation protocol.

**Acceptance Criteria**:
- [ ] Implements rephrase-agent.md contract (input/output format)
- [ ] Uses CrewAI Agent with role="數學問題改寫專家"
- [ ] Applies ≥3 escalation dimensions
- [ ] Outputs 3 stages: Deconstruction, Escalation Protocol, Rewritten Question
- [ ] Parses structured output (###stage### markers)
- [ ] Logs execution to AgentExecution table
- [ ] Preserves mathematical correctness

**Implementation**:
- File: `src/agents/rephrase_agent.py`
- Prompt: `src/prompts/rephrase_prompt.py`
- Parser: `src/parsers/rephrase_parser.py`
- Tests: `tests/contract/test_rephrase_contract.py`

**Verification**:
```python
from src.agents.rephrase_agent import RephraseAgent
agent = RephraseAgent()
result = agent.rephrase(problem_content, escalation_dimensions)
assert result["stage3_rewritten_question"] is not None
assert len(result["applied_dimensions"]) >= 3
```

---

### Task 2.3: Review Agent Implementation

**Priority**: P1
**Complexity**: 6 hours
**Dependencies**: Task 2.1
**Related**: FR-021 to FR-025, Contract: review-agent.md

**Description**: Implement Review Agent for quality assessment (3 dimensions, 1-5 scoring).

**Acceptance Criteria**:
- [ ] Implements review-agent.md contract
- [ ] Evaluates 3 dimensions: Clarity, Logical Coherence, Mathematical Validity
- [ ] Returns scores (1.0-5.0) for each dimension + overall
- [ ] Provides detailed suggestions if score < threshold
- [ ] Detects mathematical contradictions
- [ ] Outputs in structured format (###thought###, ###rating_score###, ###suggestions###)
- [ ] Creates QualityAssessment database record

**Implementation**:
- File: `src/agents/review_agent.py`
- Prompt: `src/prompts/review_prompt.py`
- Parser: `src/parsers/review_parser.py`
- Tests: `tests/contract/test_review_contract.py`

**Verification**:
```python
from src.agents.review_agent import ReviewAgent
agent = ReviewAgent()
result = agent.review(problem_content)
assert 1.0 <= result["overall_score"] <= 5.0
assert all(1.0 <= result[f"{dim}_score"] <= 5.0 for dim in ["clarity_grammar", "logical_coherence", "mathematical_validity"])
```

---

### Task 2.4: Revise Agent Implementation

**Priority**: P1
**Complexity**: 5 hours
**Dependencies**: Task 2.1
**Related**: FR-026 to FR-029, Contract: revise-agent.md

**Description**: Implement Revise Agent to improve problems based on Review suggestions.

**Acceptance Criteria**:
- [ ] Implements revise-agent.md contract
- [ ] Takes original problem + suggestions as input
- [ ] Addresses each suggestion systematically
- [ ] Preserves original mathematical intent
- [ ] Outputs revised problem + revision notes
- [ ] Creates new Problem record (source=REVISED, parent_id set)

**Implementation**:
- File: `src/agents/revise_agent.py`
- Prompt: `src/prompts/revise_prompt.py`
- Parser: `src/parsers/revise_parser.py`
- Tests: `tests/contract/test_revise_contract.py`

**Verification**:
```python
from src.agents.revise_agent import ReviseAgent
agent = ReviseAgent()
result = agent.revise(problem_content, suggestions)
assert result["revised_question"] is not None
assert result["revision_notes"] is not None
```

---

### Task 2.5: Review-Revise Iteration Manager

**Priority**: P1
**Complexity**: 6 hours
**Dependencies**: Tasks 2.3, 2.4
**Related**: FR-030, FR-031, FR-032, SC-007

**Description**: Orchestrate Review → Revise loop until quality threshold met or max iterations reached.

**Acceptance Criteria**:
- [ ] Iterates Review → Revise until score ≥ τ_rev (default 4.5)
- [ ] Limits to max 5 iterations
- [ ] Tracks iteration count in RephraseSession
- [ ] Logs all QualityAssessments
- [ ] Sets final_status (SUCCESS or MAX_ITERATIONS_EXCEEDED)
- [ ] Returns final high-quality problem
- [ ] Achieves ≥90% success rate within 5 iterations (SC-007)

**Implementation**:
- File: `src/orchestration/iteration_manager.py`
- Tests: `tests/integration/test_review_revise_loop.py`

**Verification**:
```python
from src.orchestration.iteration_manager import IterationManager
manager = IterationManager(threshold=4.5, max_iterations=5)
result = manager.iterate_until_quality(initial_problem)
assert result["final_status"] in [SessionStatus.SUCCESS, SessionStatus.MAX_ITERATIONS_EXCEEDED]
if result["final_status"] == SessionStatus.SUCCESS:
    assert result["final_score"] >= 4.5
```

---

### Task 2.6: Full Rephrase Pipeline

**Priority**: P1
**Complexity**: 4 hours
**Dependencies**: Tasks 2.2, 2.5
**Related**: SC-008

**Description**: Integrate Rephrase + Review/Revise loop into complete pipeline.

**Acceptance Criteria**:
- [ ] Orchestrates: Rephrase → Review → (Revise loop) → Final Problem
- [ ] Creates RephraseSession record
- [ ] Links all Problems via parent_id
- [ ] Logs all AgentExecutions
- [ ] Maintains >95% conceptual alignment (SC-008)
- [ ] Total pipeline time <60 seconds (SC-011)

**Implementation**:
- File: `src/orchestration/rephrase_pipeline.py`
- Tests: `tests/integration/test_full_rephrase_pipeline.py`

**Verification**:
```python
from src.orchestration.rephrase_pipeline import RephrasePipeline
pipeline = RephrasePipeline()
result = pipeline.process(original_problem, escalation_dimensions)
assert result["session"]["final_status"] == SessionStatus.SUCCESS
assert result["final_problem_id"] is not None
```

---

## Phase 3: User Story 2 - Solution Generation (P2)

### Task 3.1: Solver Agent Implementation

**Priority**: P2
**Complexity**: 7 hours
**Dependencies**: Task 2.1
**Related**: FR-033 to FR-038, Contract: solver-agent.md

**Description**: Implement Solver Agent for Chain-of-Thought (CoT) solution generation.

**Acceptance Criteria**:
- [ ] Implements solver-agent.md contract
- [ ] Uses CoT reasoning (###thought###, ###answer###)
- [ ] Shows all intermediate steps
- [ ] Handles multi-case analysis
- [ ] Generates solutions for both original and rephrased problems
- [ ] Creates Solution database record
- [ ] 100% of solutions have complete step-by-step reasoning (SC-009)

**Implementation**:
- File: `src/agents/solver_agent.py`
- Prompt: `src/prompts/solver_prompt.py`
- Parser: `src/parsers/solver_parser.py`
- Tests: `tests/contract/test_solver_contract.py`

**Verification**:
```python
from src.agents.solver_agent import SolverAgent
agent = SolverAgent()
result = agent.solve(problem_content)
assert result["thought_process"] is not None
assert result["final_answer"] is not None
assert len(result["intermediate_steps"]) > 0
```

---

### Task 3.2: Solution Generation Pipeline

**Priority**: P2
**Complexity**: 3 hours
**Dependencies**: Task 3.1
**Related**: FR-038

**Description**: Generate solutions for both original and rephrased high-quality problems.

**Acceptance Criteria**:
- [ ] Generates solution for original problem
- [ ] Generates solution for final rephrased problem (if score ≥ threshold)
- [ ] Stores both Solutions in database
- [ ] Links Solutions to respective Problems

**Implementation**:
- File: `src/orchestration/solution_pipeline.py`
- Tests: `tests/integration/test_solution_generation.py`

**Verification**:
```python
from src.orchestration.solution_pipeline import generate_solutions
solutions = generate_solutions(original_problem_id, rephrased_problem_id)
assert len(solutions) == 2
assert all(s["thought_process"] is not None for s in solutions)
```

---

## Phase 4: User Story 3 - Configuration & CLI (P3)

### Task 4.1: Configuration Management

**Priority**: P3
**Complexity**: 3 hours
**Dependencies**: Task 0.1
**Related**: FR-042, FR-043, FR-044

**Description**: Implement configuration system with Pydantic Settings.

**Acceptance Criteria**:
- [ ] Reads from `.env` file
- [ ] Supports all config variables (OCR, LLM, quality threshold, etc.)
- [ ] Validates config values (thresholds 3.0-5.0, etc.)
- [ ] Allows runtime configuration overrides
- [ ] Provides default values

**Implementation**:
- File: `src/config/settings.py`
- Tests: `tests/unit/test_settings.py`

---

### Task 4.2: CLI Interface

**Priority**: P3
**Complexity**: 5 hours
**Dependencies**: Tasks 1.6, 2.6, 3.2
**Related**: All User Stories

**Description**: Create command-line interface for full pipeline.

**Acceptance Criteria**:
- [ ] Supports photo upload: `agenticmath upload photo.jpg`
- [ ] Supports text input: `agenticmath generate "problem text"`
- [ ] Shows progress indicators
- [ ] Displays results (rephrased problem, solution)
- [ ] Allows config overrides (`--threshold 4.0`)
- [ ] Handles errors gracefully

**Implementation**:
- File: `src/cli/main.py`
- Framework: Click or Typer
- Tests: `tests/integration/test_cli.py`

---

## Phase 5: Testing & Quality Assurance

### Task 5.1: Unit Test Coverage

**Priority**: All Phases
**Complexity**: Ongoing
**Target**: ≥80% code coverage

**Tests Required**:
- [ ] All agent parsers
- [ ] Database models
- [ ] Image preprocessing
- [ ] OCR integration
- [ ] Configuration
- [ ] Utility functions

---

### Task 5.2: Integration Test Suite

**Priority**: All Phases
**Complexity**: Ongoing

**Tests Required**:
- [ ] OCR Pipeline end-to-end
- [ ] Rephrase Pipeline end-to-end
- [ ] Review-Revise Loop
- [ ] Full workflow: Photo → OCR → Rephrase → Review → Solution
- [ ] Error handling scenarios

---

### Task 5.3: Contract Validation Tests

**Priority**: P1, P2
**Complexity**: 4 hours per agent
**Related**: All agent contracts

**Description**: Validate that agents strictly follow their contracts.

**Tests Required**:
- [ ] Image Extraction Agent contract
- [ ] Rephrase Agent contract
- [ ] Review Agent contract
- [ ] Revise Agent contract
- [ ] Solver Agent contract

---

## Summary

### Total Tasks by Phase

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 0: Setup | 2 | 5 hours |
| Phase 1: P0 (OCR) | 6 | 29 hours |
| Phase 2: P1 (Rephrase) | 6 | 32 hours |
| Phase 3: P2 (Solver) | 2 | 10 hours |
| Phase 4: P3 (Config/CLI) | 2 | 8 hours |
| Phase 5: Testing | 3 | Ongoing |
| **Total** | **21** | **~84 hours** |

### Critical Path

```
Setup (0.1, 0.2) → OCR (1.1-1.6) → LLM Client (2.1) → Agents (2.2-2.4) → Iteration (2.5-2.6) → Solution (3.1-3.2) → CLI (4.2)
```

### Milestone Targets

- **Milestone 1** (Week 1-2): Phase 0 + Phase 1 (P0) complete
  - Can upload photos and extract text via OCR
- **Milestone 2** (Week 3-4): Phase 2 (P1) complete
  - Can generate high-quality rephrased problems
- **Milestone 3** (Week 5): Phase 3 (P2) complete
  - Can generate CoT solutions
- **Milestone 4** (Week 6): Phase 4 (P3) + Testing complete
  - Full CLI working, tests passing

---

**Next Steps**:
1. Review and approve this task breakdown
2. Assign tasks to team members
3. Create GitHub issues/tickets for each task
4. Begin with Phase 0 (Setup)
