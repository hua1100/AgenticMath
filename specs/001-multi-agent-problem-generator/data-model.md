# Data Model: Multi-Agent Math Problem Generator

**Version**: 1.0.0
**Last Updated**: 2025-11-06
**Feature**: 001-multi-agent-problem-generator

## Overview

This document defines the core data entities for the multi-agent math problem generator system. All models use Pydantic for validation and will be persisted in a relational database (SQLite for development, PostgreSQL for production).

## Entity Relationship Diagram

```
┌──────────────────────────┐
│   UploadedImage (NEW)    │
│  - file_path             │
│  - ocr_extracted_text    │
│  - ocr_confidence        │
│  - diagram_description   │
└──────────┬───────────────┘
           │
           │ creates (via OCR)
           ▼
┌─────────────────┐
│    Problem      │
│  (original)     │
└────────┬────────┘
         │
         │ spawns (via rephrase)
         ▼
┌─────────────────────────────┐
│    RephraseSession         │
│  - iteration_count         │
│  - escalation_dimensions   │
│  - final_status           │
└──────────┬──────────────────┘
           │
           │ produces
           ▼
┌─────────────────┐        ┌──────────────────────┐
│    Problem      │◄───────│  QualityAssessment  │
│  (rephrased)    │        │  - scores (1-5)     │
└────────┬────────┘        │  - suggestions      │
         │                 └──────────────────────┘
         │                          ▲
         │                          │
         │                          │ evaluates
         │                          │
         │                 ┌────────┴────────┐
         │                 │  Problem        │
         │                 │  (revised)      │
         │                 └─────────────────┘
         │
         │ when score ≥ threshold
         ▼
┌─────────────────┐
│    Solution     │
│  - thought      │
│  - answer       │
└─────────────────┘

         All interactions logged in:

┌─────────────────────────────┐
│    AgentExecution           │
│  - agent_type (incl. OCR)   │
│  - input/output             │
│  - execution_time           │
└─────────────────────────────┘
```

## Core Entities

### 1. UploadedImage

Represents a photo uploaded by a student, processed through OCR to extract mathematical problem text.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `file_path` | String | Yes | Storage location of image file (e.g., `/uploads/2025/11/abc123.jpg`) |
| `file_size` | Integer | Yes | File size in bytes |
| `file_format` | Enum | Yes | IMAGE_FORMAT: JPEG, PNG |
| `upload_timestamp` | Timestamp | Yes | When photo was uploaded |
| `ocr_extracted_text` | Text | Yes | Text extracted by PaddleOCR |
| `ocr_confidence_score` | Float | Yes | Average confidence 0.0-1.0 from OCR engine |
| `contains_diagram` | Boolean | Yes | Whether diagram/chart was detected |
| `diagram_description` | String | No | Description of detected diagram (e.g., "包含直角三角形，標註邊長 a, b, c") |
| `preprocessing_applied` | List[String] | Yes | Preprocessing steps: rotation_corrected, noise_reduced, contrast_enhanced |
| `ocr_processing_time_ms` | Integer | Yes | Time taken for OCR processing in milliseconds |
| `problem_id` | UUID | No | Reference to Problem created from this image |
| `created_at` | Timestamp | Yes | When record was created |

#### Pydantic Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4

class ImageFormat(str, Enum):
    JPEG = "jpeg"
    PNG = "png"

class UploadedImage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    file_path: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., gt=0, le=10_000_000)  # Max 10MB
    file_format: ImageFormat
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    ocr_extracted_text: str = Field(..., min_length=0, max_length=10000)
    ocr_confidence_score: float = Field(..., ge=0.0, le=1.0)
    contains_diagram: bool = False
    diagram_description: Optional[str] = Field(None, max_length=1000)
    preprocessing_applied: List[str] = Field(default_factory=list)
    ocr_processing_time_ms: int = Field(..., ge=0)
    problem_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Database Schema

```sql
CREATE TABLE uploaded_images (
    id UUID PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL UNIQUE,
    file_size INTEGER NOT NULL CHECK (file_size > 0 AND file_size <= 10000000),
    file_format VARCHAR(10) NOT NULL CHECK (file_format IN ('jpeg', 'png')),
    upload_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ocr_extracted_text TEXT NOT NULL,
    ocr_confidence_score NUMERIC(4,3) NOT NULL CHECK (ocr_confidence_score BETWEEN 0.0 AND 1.0),
    contains_diagram BOOLEAN NOT NULL DEFAULT FALSE,
    diagram_description VARCHAR(1000),
    preprocessing_applied JSONB NOT NULL DEFAULT '[]', -- Array of strings
    ocr_processing_time_ms INTEGER NOT NULL CHECK (ocr_processing_time_ms >= 0),
    problem_id UUID REFERENCES problems(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_uploaded_images_upload_time ON uploaded_images(upload_timestamp DESC);
CREATE INDEX idx_uploaded_images_problem ON uploaded_images(problem_id);
CREATE INDEX idx_uploaded_images_confidence ON uploaded_images(ocr_confidence_score);
```

---

### 2. Problem

Represents a mathematical problem at any stage (original/rephrased/revised).

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `content` | Text | Yes | Full problem statement (plain text or markdown) |
| `domain` | Enum | Yes | Mathematical domain: ALGEBRA, GEOMETRY, CALCULUS, PROBABILITY, NUMBER_THEORY, COMBINATORICS, OTHER |
| `competencies` | List[String] | Yes | Required concepts/methods (e.g., ["quadratic equations", "factoring"]) |
| `baseline_difficulty` | Integer | Yes | Difficulty level 1-5 (Krathwohl's Cognitive Rigor Index) |
| `source` | Enum | Yes | ORIGINAL (user-uploaded), REPHRASED, REVISED |
| `source_type` | Enum | Yes | OCR (from photo), MANUAL_TEXT (direct text input) |
| `parent_id` | UUID | No | Reference to parent Problem (null for original, set for rephrased/revised) |
| `uploaded_image_id` | UUID | No | Reference to UploadedImage if source_type=OCR |
| `created_at` | Timestamp | Yes | When problem was created |
| `metadata` | JSON | No | Additional properties (e.g., language, grade level, tags) |

#### Pydantic Schema (Conceptual)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4

class MathDomain(str, Enum):
    ALGEBRA = "algebra"
    GEOMETRY = "geometry"
    CALCULUS = "calculus"
    PROBABILITY = "probability"
    NUMBER_THEORY = "number_theory"
    COMBINATORICS = "combinatorics"
    OTHER = "other"

class ProblemSource(str, Enum):
    ORIGINAL = "original"
    REPHRASED = "rephrased"
    REVISED = "revised"

class SourceType(str, Enum):
    OCR = "ocr"
    MANUAL_TEXT = "manual_text"

class Problem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content: str = Field(..., min_length=10, max_length=5000)
    domain: MathDomain
    competencies: List[str] = Field(..., min_items=1)
    baseline_difficulty: int = Field(..., ge=1, le=5)
    source: ProblemSource
    source_type: SourceType
    parent_id: Optional[UUID] = None
    uploaded_image_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None
```

#### Database Schema (SQL)

```sql
CREATE TABLE problems (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL CHECK (length(content) >= 10),
    domain VARCHAR(50) NOT NULL,
    competencies JSONB NOT NULL, -- Array of strings
    baseline_difficulty INTEGER NOT NULL CHECK (baseline_difficulty BETWEEN 1 AND 5),
    source VARCHAR(20) NOT NULL CHECK (source IN ('original', 'rephrased', 'revised')),
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('ocr', 'manual_text')),
    parent_id UUID REFERENCES problems(id),
    uploaded_image_id UUID REFERENCES uploaded_images(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    -- Constraint: if source_type=ocr, uploaded_image_id must be set
    CONSTRAINT check_ocr_has_image CHECK (
        (source_type = 'ocr' AND uploaded_image_id IS NOT NULL) OR
        (source_type = 'manual_text')
    )
);

CREATE INDEX idx_problems_parent ON problems(parent_id);
CREATE INDEX idx_problems_domain ON problems(domain);
CREATE INDEX idx_problems_source ON problems(source);
CREATE INDEX idx_problems_source_type ON problems(source_type);
CREATE INDEX idx_problems_uploaded_image ON problems(uploaded_image_id);
```

---

### 3. QualityAssessment

Represents a Review Agent's evaluation of a problem.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `problem_id` | UUID | Yes | Reference to evaluated Problem |
| `clarity_grammar_score` | Float | Yes | Score 1.0-5.0 for clarity & grammar |
| `logical_coherence_score` | Float | Yes | Score 1.0-5.0 for logical coherence & completeness |
| `mathematical_validity_score` | Float | Yes | Score 1.0-5.0 for mathematical validity & solvability |
| `overall_score` | Float | Yes | Overall score 1.0-5.0 (computed or LLM-provided) |
| `thought_process` | Text | Yes | Detailed reasoning (from ###thought###) |
| `suggestions` | List[String] | No | List of improvement recommendations (empty if score ≥ threshold) |
| `created_at` | Timestamp | Yes | When assessment was performed |

#### Pydantic Schema

```python
class QualityAssessment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    problem_id: UUID
    clarity_grammar_score: float = Field(..., ge=1.0, le=5.0)
    logical_coherence_score: float = Field(..., ge=1.0, le=5.0)
    mathematical_validity_score: float = Field(..., ge=1.0, le=5.0)
    overall_score: float = Field(..., ge=1.0, le=5.0)
    thought_process: str = Field(..., min_length=20)
    suggestions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Database Schema

```sql
CREATE TABLE quality_assessments (
    id UUID PRIMARY KEY,
    problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    clarity_grammar_score NUMERIC(3,2) NOT NULL CHECK (clarity_grammar_score BETWEEN 1.0 AND 5.0),
    logical_coherence_score NUMERIC(3,2) NOT NULL CHECK (logical_coherence_score BETWEEN 1.0 AND 5.0),
    mathematical_validity_score NUMERIC(3,2) NOT NULL CHECK (mathematical_validity_score BETWEEN 1.0 AND 5.0),
    overall_score NUMERIC(3,2) NOT NULL CHECK (overall_score BETWEEN 1.0 AND 5.0),
    thought_process TEXT NOT NULL,
    suggestions JSONB NOT NULL DEFAULT '[]', -- Array of strings
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assessments_problem ON quality_assessments(problem_id);
CREATE INDEX idx_assessments_score ON quality_assessments(overall_score);
```

---

### 4. Solution

Represents a Solver Agent's generated solution with Chain-of-Thought reasoning.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `problem_id` | UUID | Yes | Reference to solved Problem |
| `thought_process` | Text | Yes | Detailed CoT reasoning (from ###thought###) |
| `final_answer` | String | Yes | Concise final answer (from ###answer###) |
| `intermediate_steps` | List[String] | No | Parsed intermediate calculation steps |
| `created_at` | Timestamp | Yes | When solution was generated |

#### Pydantic Schema

```python
class Solution(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    problem_id: UUID
    thought_process: str = Field(..., min_length=50)
    final_answer: str = Field(..., min_length=1, max_length=500)
    intermediate_steps: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Database Schema

```sql
CREATE TABLE solutions (
    id UUID PRIMARY KEY,
    problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    thought_process TEXT NOT NULL CHECK (length(thought_process) >= 50),
    final_answer VARCHAR(500) NOT NULL,
    intermediate_steps JSONB, -- Array of strings
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_solutions_problem ON solutions(problem_id);
```

---

### 5. RephraseSession

Represents a complete rephrase workflow from original problem to final high-quality rephrased problem.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `original_problem_id` | UUID | Yes | Reference to original Problem |
| `final_problem_id` | UUID | No | Reference to final accepted Problem (null if failed) |
| `escalation_dimensions` | List[String] | Yes | Applied complexity dimensions (e.g., ["Multi-stage Transformation", "Cross-domain Integration"]) |
| `iteration_count` | Integer | Yes | Number of review-revise cycles performed |
| `quality_threshold` | Float | Yes | Threshold used (default 4.5) |
| `final_status` | Enum | Yes | SUCCESS, MAX_ITERATIONS_EXCEEDED, ERROR |
| `created_at` | Timestamp | Yes | When session started |
| `completed_at` | Timestamp | No | When session finished (null if in progress) |

#### Pydantic Schema

```python
class SessionStatus(str, Enum):
    SUCCESS = "success"
    MAX_ITERATIONS_EXCEEDED = "max_iterations_exceeded"
    ERROR = "error"

class RephraseSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    original_problem_id: UUID
    final_problem_id: Optional[UUID] = None
    escalation_dimensions: List[str] = Field(..., min_items=3)
    iteration_count: int = Field(default=0, ge=0)
    quality_threshold: float = Field(default=4.5, ge=3.0, le=5.0)
    final_status: SessionStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
```

#### Database Schema

```sql
CREATE TABLE rephrase_sessions (
    id UUID PRIMARY KEY,
    original_problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    final_problem_id UUID REFERENCES problems(id),
    escalation_dimensions JSONB NOT NULL, -- Array of strings
    iteration_count INTEGER NOT NULL DEFAULT 0 CHECK (iteration_count >= 0),
    quality_threshold NUMERIC(3,2) NOT NULL DEFAULT 4.5 CHECK (quality_threshold BETWEEN 3.0 AND 5.0),
    final_status VARCHAR(50) NOT NULL CHECK (final_status IN ('success', 'max_iterations_exceeded', 'error')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_sessions_original ON rephrase_sessions(original_problem_id);
CREATE INDEX idx_sessions_status ON rephrase_sessions(final_status);
```

---

### 6. AgentExecution

Represents a single agent invocation for complete traceability and debugging.

#### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `agent_type` | Enum | Yes | OCR, REPHRASE, REVIEW, REVISE, SOLVER |
| `session_id` | UUID | No | Reference to RephraseSession (null for solver-only calls) |
| `input_data` | JSON | Yes | Agent input (e.g., problem content, suggestions) |
| `output_data` | JSON | Yes | Agent output (parsed structured response) |
| `prompt_template` | Text | Yes | Full prompt sent to LLM |
| `raw_llm_response` | Text | Yes | Unparsed LLM response |
| `execution_time_ms` | Integer | Yes | Time taken in milliseconds |
| `llm_model` | String | Yes | LLM model used (e.g., "gpt-4", "claude-3") |
| `created_at` | Timestamp | Yes | When execution occurred |

#### Pydantic Schema

```python
class AgentType(str, Enum):
    OCR = "ocr"
    REPHRASE = "rephrase"
    REVIEW = "review"
    REVISE = "revise"
    SOLVER = "solver"

class AgentExecution(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    agent_type: AgentType
    session_id: Optional[UUID] = None
    input_data: dict
    output_data: dict
    prompt_template: str = Field(..., min_length=100)
    raw_llm_response: Optional[str] = Field(None, min_length=10)  # Null for OCR
    execution_time_ms: int = Field(..., ge=0)
    llm_model: Optional[str] = None  # Null for OCR (uses PaddleOCR instead)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Database Schema

```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('ocr', 'rephrase', 'review', 'revise', 'solver')),
    session_id UUID REFERENCES rephrase_sessions(id),
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    prompt_template TEXT NOT NULL,
    raw_llm_response TEXT,  -- Null for OCR executions
    execution_time_ms INTEGER NOT NULL CHECK (execution_time_ms >= 0),
    llm_model VARCHAR(100),  -- Null for OCR (uses PaddleOCR)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraint: Non-OCR agents must have LLM response and model
    CONSTRAINT check_llm_fields CHECK (
        (agent_type = 'ocr') OR
        (agent_type != 'ocr' AND raw_llm_response IS NOT NULL AND llm_model IS NOT NULL)
    )
);

CREATE INDEX idx_executions_agent ON agent_executions(agent_type);
CREATE INDEX idx_executions_session ON agent_executions(session_id);
CREATE INDEX idx_executions_created ON agent_executions(created_at);
```

---

## Relationships Summary

1. **UploadedImage → Problem** (one-to-one):
   - Each uploaded image creates one original Problem via OCR
   - Stored in Problem's `uploaded_image_id` field

2. **Problem → Problem** (parent-child via `parent_id`):
   - Original problem spawns rephrased problems
   - Rephrased problem spawns revised problems

3. **Problem → QualityAssessment** (one-to-many):
   - Each problem can have multiple assessments (one per review iteration)

4. **Problem → Solution** (one-to-one or one-to-many):
   - Each problem can have one canonical solution
   - In practice, one-to-one for simplicity

5. **RephraseSession → Problem** (one-to-many):
   - Session references original problem and tracks all intermediate/final problems

6. **RephraseSession → AgentExecution** (one-to-many):
   - Session contains all agent executions for that workflow (OCR, Rephrase, Review, Revise, Solver)

7. **AgentExecution** standalone for solver-only calls or OCR-only calls (when `session_id` is null)

---

## Data Flow Example

### Scenario 1: Student uploads photo, system performs OCR and rephrases problem

1. **Upload and Store Image**:
   ```
   UploadedImage(
       id=IMG1,
       file_path="/uploads/2025/11/student_photo_001.jpg",
       file_size=2458693,  # ~2.4MB
       file_format=JPEG,
       upload_timestamp=2025-11-06T10:30:00Z
   )
   ```

2. **OCR Processing (via OCR Agent)**:
   ```
   AgentExecution(
       id=E0,
       agent_type=OCR,
       session_id=null,  # OCR is standalone
       input_data={"image_id": "IMG1", "file_path": "/uploads/..."},
       output_data={"extracted_text": "求解方程式：2x + 3 = 11", "confidence": 0.92, "contains_diagram": false},
       prompt_template="N/A (uses PaddleOCR, not LLM)",
       raw_llm_response=null,
       execution_time_ms=2340,  # 2.34 seconds
       llm_model=null,
       created_at=2025-11-06T10:30:02Z
   )
   ```

3. **Update UploadedImage with OCR Results**:
   ```
   UploadedImage(
       id=IMG1,
       ...
       ocr_extracted_text="求解方程式：2x + 3 = 11",
       ocr_confidence_score=0.92,
       contains_diagram=false,
       diagram_description=null,
       preprocessing_applied=["rotation_corrected", "contrast_enhanced"],
       ocr_processing_time_ms=2340
   )
   ```

4. **Create Original Problem from OCR**:
   ```
   Problem(
       id=P1,
       content="求解方程式：2x + 3 = 11",
       source=ORIGINAL,
       source_type=OCR,
       domain=ALGEBRA,
       uploaded_image_id=IMG1,
       ...
   )
   UploadedImage(id=IMG1, problem_id=P1, ...)  # Link back
   ```

5. **Continue to Rephrase Flow** (same as Scenario 2 below)...

---

### Scenario 2: Student types problem directly (manual text), system rephrases it

1. **Create Original Problem** (direct text input):
   ```
   Problem(
       id=P1,
       content="What is 2x + 3 = 11?",
       source=ORIGINAL,
       source_type=MANUAL_TEXT,
       domain=ALGEBRA,
       uploaded_image_id=null,
       ...
   )
   ```

2. **Create RephraseSession**:
   ```
   RephraseSession(id=S1, original_problem_id=P1, escalation_dimensions=[...], ...)
   ```

3. **Rephrase Agent Execution**:
   ```
   AgentExecution(id=E1, agent_type=REPHRASE, session_id=S1, input_data={"problem": "..."}, ...)
   Problem(id=P2, content="<rephrased>", source=REPHRASED, parent_id=P1, ...)
   ```

4. **Review Agent Execution**:
   ```
   AgentExecution(id=E2, agent_type=REVIEW, session_id=S1, input_data={"problem": P2.content}, ...)
   QualityAssessment(id=A1, problem_id=P2, overall_score=4.2, suggestions=[...], ...)
   ```

5. **Revise Agent Execution** (score < 4.5):
   ```
   AgentExecution(id=E3, agent_type=REVISE, session_id=S1, input_data={"problem": P2, "suggestions": [...]}, ...)
   Problem(id=P3, content="<revised>", source=REVISED, parent_id=P2, ...)
   ```

6. **Review Again**:
   ```
   AgentExecution(id=E4, agent_type=REVIEW, session_id=S1, input_data={"problem": P3.content}, ...)
   QualityAssessment(id=A2, problem_id=P3, overall_score=4.7, ...)
   ```

7. **Update Session** (score ≥ 4.5):
   ```
   RephraseSession(id=S1, final_problem_id=P3, iteration_count=2, final_status=SUCCESS, completed_at=<now>)
   ```

8. **Solver Agent Execution**:
   ```
   AgentExecution(id=E5, agent_type=SOLVER, session_id=S1, input_data={"problem": P3.content}, ...)
   Solution(id=SOL1, problem_id=P3, thought_process="...", final_answer="4", ...)
   ```

---

## Validation Rules

### Cross-Entity Constraints

1. **Problem Parent-Child**:
   - `source=REPHRASED` MUST have `parent_id` pointing to `source=ORIGINAL`
   - `source=REVISED` MUST have `parent_id` pointing to `source=REPHRASED` or `source=REVISED`
   - No circular references (parent cannot be descendant)

2. **RephraseSession Completion**:
   - `final_status=SUCCESS` REQUIRES `final_problem_id` to be set
   - `completed_at` MUST be set when `final_status` is not null

3. **QualityAssessment Scores**:
   - `overall_score` SHOULD be close to average of three dimension scores (allow LLM flexibility)
   - `suggestions` SHOULD be empty if `overall_score ≥ quality_threshold`

4. **Solution Requirements**:
   - Can only create Solution for Problems with QualityAssessment where `overall_score ≥ threshold`

---

## Indexing Strategy

### Primary Indexes (already defined above)
- Primary keys on all `id` fields
- Foreign key indexes for joins

### Additional Performance Indexes

```sql
-- Find all problems in a rephrase chain
CREATE INDEX idx_problems_parent_recursive ON problems(parent_id, id);

-- Find recent high-quality problems
CREATE INDEX idx_recent_quality ON quality_assessments(created_at DESC, overall_score DESC);

-- Find sessions by completion status and time
CREATE INDEX idx_sessions_completed ON rephrase_sessions(completed_at DESC, final_status);

-- Analyze agent performance
CREATE INDEX idx_agent_performance ON agent_executions(agent_type, execution_time_ms);
```

---

## Configuration Schema

For User Story 3 (configurable thresholds), store configuration in separate table or environment variables.

### Configuration (Environment Variables)

```bash
# OCR Configuration
OCR_ENABLED=true
OCR_ENGINE=paddleocr  # PaddleOCR
OCR_LANGUAGE=chinese_cht  # Traditional Chinese
OCR_USE_ANGLE_CLS=true  # Auto-rotation correction
OCR_USE_GPU=false  # Use CPU by default
OCR_CONFIDENCE_THRESHOLD=0.7  # Minimum confidence to accept OCR result
MAX_IMAGE_SIZE_MB=10  # Maximum upload size
ALLOWED_IMAGE_FORMATS=jpeg,png
IMAGE_STORAGE_PATH=/uploads/  # Where to store uploaded images

# Quality threshold
QUALITY_THRESHOLD=4.5  # Range: 3.0-5.0

# Max iterations
MAX_REVIEW_REVISE_ITERATIONS=5

# Escalation dimensions (comma-separated)
DEFAULT_ESCALATION_DIMENSIONS="Multi-stage Transformation,Cross-domain Integration,Real-world Parameterization"

# LLM Configuration
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4.1  # GPT-4o/GPT-4 Turbo for best quality
LLM_API_KEY=<secret>
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Database
DATABASE_URL=sqlite:///./agenticmath.db  # or postgresql://...
```

### Configuration Model

```python
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # OCR Configuration
    ocr_enabled: bool = True
    ocr_engine: str = "paddleocr"
    ocr_language: str = "chinese_cht"
    ocr_use_angle_cls: bool = True
    ocr_use_gpu: bool = False
    ocr_confidence_threshold: float = 0.7
    max_image_size_mb: int = 10
    allowed_image_formats: List[str] = ["jpeg", "png"]
    image_storage_path: str = "/uploads/"

    # Quality threshold
    quality_threshold: float = 4.5
    max_review_revise_iterations: int = 5
    default_escalation_dimensions: List[str] = [
        "Multi-stage Transformation",
        "Cross-domain Integration",
        "Real-world Parameterization"
    ]

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1"  # GPT-4o/GPT-4 Turbo
    llm_api_key: str
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000

    # Database
    database_url: str = "sqlite:///./agenticmath.db"

    class Config:
        env_file = ".env"
```

---

## Migration Strategy

### Initial Schema Creation

Use Alembic for database migrations:

```bash
# Initialize alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Create initial schema"

# Apply migration
alembic upgrade head
```

### Future Schema Changes

- Add new fields with `ALTER TABLE ... ADD COLUMN ... DEFAULT ...`
- Never remove fields (deprecate instead)
- Version all migrations with timestamps
- Test migrations on sample data before production

---

## Data Retention Policy

### Production Considerations

- **Problems**: Retain indefinitely (valuable training data)
- **QualityAssessments**: Retain 90 days for debugging, archive older to cold storage
- **Solutions**: Retain indefinitely (educational content)
- **RephraseSessions**: Retain 90 days for debugging, summarize to metrics
- **AgentExecutions**: Retain 30 days, then sample 10% for analysis

### Privacy & Compliance

- If students can upload personal data in problems, implement:
  - PII detection and redaction
  - User consent tracking
  - Right to deletion (GDPR/CCPA compliance)
  - Anonymization for training data

---

**End of Data Model Document**
