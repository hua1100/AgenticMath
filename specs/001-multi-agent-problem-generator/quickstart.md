# QuickStart: Multi-Agent Math Problem Generator

**Feature**: 001-multi-agent-problem-generator
**Last Updated**: 2025-11-06

## Overview

This quickstart guide demonstrates how to use the AgenticMath multi-agent system to transform math problems into high-quality, pedagogically effective practice questions with detailed solutions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Student Input                            │
│        Photo Upload OR Text: "Solve for x: 2x + 3 = 11"    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│              OCR Agent (if photo)                           │
│  - Extracts text from image using PaddleOCR                │
│  - Detects diagrams and generates descriptions             │
│  - Produces: Text content with confidence score            │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                 Rephrase Agent                              │
│  - Identifies domain (Algebra)                             │
│  - Applies ≥3 escalation dimensions                        │
│  - Produces: "A rectangular garden has length 2w+3..."     │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                  Review Agent                               │
│  - Scores: Clarity (4.5), Logic (5.0), Math (5.0)         │
│  - Overall: 4.83 (≥ 4.5 threshold)                         │
│  - Suggestions: ["Add answer format specification"]        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ├─── Score < 4.5? ────┐
                     │                     │
                     │ No (4.83)           │ Yes
                     │                     ▼
                     │            ┌──────────────────┐
                     │            │  Revise Agent    │
                     │            │  - Applies fixes  │
                     │            └────────┬─────────┘
                     │                     │
                     │                     └─────► Back to Review
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   Solver Agent                              │
│  - Generates detailed CoT solution                         │
│  - Shows all intermediate steps                            │
│  - Produces final answer: "2.67"                           │
└────────────────────────────────────────────────────────────┘
```

## Workflow Stages

### Stage 0: Photo Upload & OCR (Optional)

**Input**: Math problem photo (JPEG/PNG)
**Agent**: Image Extraction (OCR) Agent
**Output**: Extracted text with confidence score

**Example**:
```
Input: photo of printed textbook problem "求解方程式：在直角三角形 ABC 中，∠C = 90°，若 AB = 10，AC = 6，求 BC 的長度。"

Output:
  OCR Confidence: 0.92 (92%)
  Extracted Text: "求解方程式：在直角三角形 ABC 中，∠C = 90°，若 AB = 10，AC = 6，求 BC 的長度。"
  Contains Diagram: Yes
  Diagram Description: "包含直角三角形 ABC，標註直角於 C 點，斜邊 AB 標註長度 10，直角邊 AC 標註長度 6"
  Processing Time: 2.3 seconds
```

### Stage 1: Problem Rephrase

**Input**: Original problem from student
**Agent**: Rephrase Agent
**Output**: Rephrased problem with increased complexity

**Example**:
```
Input: "Solve for x: 2x + 3 = 11"

Output:
  Stage 1: Domain=Algebra, Competencies=[Linear equations], Difficulty=1
  Stage 2: Applied dimensions=Multi-stage Transformation, Cross-domain Integration, Real-world Parameterization
  Stage 3: "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter is 22 meters, find the width."
```

### Stage 2: Quality Review

**Input**: Rephrased problem
**Agent**: Review Agent
**Output**: Quality scores (1-5) and improvement suggestions

**Example**:
```
Input: "A rectangular garden has length 3 more than twice width. Perimeter is 22. Find width."

Output:
  Clarity & Grammar: 4.5/5 (minor: add answer format)
  Logical Coherence: 5.0/5 (complete information)
  Mathematical Validity: 5.0/5 (solvable, consistent)
  Overall: 4.83/5
  Suggestions: ["Specify answer format: decimal rounded to 2 places"]
```

### Stage 3: Iterative Revision (if needed)

**Condition**: Overall score < threshold (default 4.5)
**Agent**: Revise Agent → Review Agent (loop)
**Output**: Improved problem

**Example**:
```
Iteration 1:
  Review Score: 3.8/5
  Suggestions: ["Fix mathematical contradiction: probability > 1"]

  Revise Agent applies fix:
  "Changed marble counts to make probabilities consistent..."

Iteration 2:
  Review Score: 4.6/5 ✓ (passes threshold)
```

### Stage 4: Solution Generation

**Input**: High-quality problem (score ≥ threshold)
**Agent**: Solver Agent
**Output**: Detailed solution with Chain-of-Thought reasoning

**Example**:
```
Input: "A rectangular garden has length 3 meters more than twice its width. Perimeter is 22 meters. Find width (decimal, 2 places)."

Output:
  Thought Process:
    Step 1: Define variables: w=width, l=2w+3, P=22
    Step 2: Perimeter formula: P=2(l+w)
    Step 3: Substitute: 22 = 2((2w+3)+w) = 2(3w+3) = 6w+6
    Step 4: Solve: 16=6w, w=8/3≈2.67
    Step 5: Verify: l=25/3, P=2(25/3+8/3)=22 ✓

  Final Answer: 2.67
```

## Installation & Setup

### Prerequisites

```bash
# Python 3.11+
python --version  # Should be ≥ 3.11

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Core Dependencies** (see `requirements.txt`):
```
# Agent Framework
crewai>=0.1.0

# LLM Providers
openai>=1.0.0

# OCR (Photo Upload Feature)
paddleocr==2.7.0
paddlepaddle==2.5.0  # CPU version
# or paddlepaddle-gpu==2.5.0  # GPU version

# Image Processing
Pillow==10.0.0
opencv-python==4.8.0
numpy==1.24.0

# Data & Storage
pydantic>=2.0.0
sqlalchemy>=2.0.0
alembic>=1.13.0  # For database migrations

# Testing
pytest>=7.4.0

# Utilities
python-dotenv>=1.0.0
```

### Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# LLM Provider
OPENAI_API_KEY=sk-...  # Your API key
OPENAI_MODEL=gpt-4o  # or 'gpt-4-turbo'
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4096

# OCR Configuration (Photo Upload Feature)
OCR_LANGUAGE=chinese_cht  # Traditional Chinese
OCR_USE_GPU=false  # Set to true if you have CUDA-enabled GPU
OCR_CONFIDENCE_THRESHOLD=0.70  # Minimum confidence to accept OCR result
OCR_AUTO_ROTATION=true
OCR_NOISE_REDUCTION=true
OCR_CONTRAST_ENHANCEMENT=true

# File Upload Settings
UPLOAD_DIR=./uploads  # Directory to store uploaded photos
MAX_FILE_SIZE_MB=10  # Maximum file size for uploads

# Quality Settings
QUALITY_THRESHOLD=4.5  # Range: 3.0-5.0
MAX_REVIEW_REVISE_ITERATIONS=5

# Escalation Dimensions (comma-separated)
DEFAULT_ESCALATION_DIMENSIONS=Multi-stage Transformation,Cross-domain Integration,Real-world Parameterization

# Database
DATABASE_URL=sqlite:///./agenticmath.db  # For development
# DATABASE_URL=postgresql://user:pass@localhost/agenticmath  # For production

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/agenticmath.log
```

### Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify database created
ls -lh agenticmath.db  # Should see database file
```

## Basic Usage (CLI)

### Process a Photo (with OCR)

```bash
# Upload and process a photo of a math problem
python -m src.cli.main process-photo ./examples/math_problem_01.jpg
```

**Output**:
```
┌─────────────────────────────────────────────────────┐
│ AgenticMath Problem Generator (Photo Mode)          │
└─────────────────────────────────────────────────────┘

[0/5] Uploading photo... ✓ (0.1s)
   File: math_problem_01.jpg
   Size: 2.3MB
   Format: JPEG

[1/5] Performing OCR... ✓ (2.3s)
   Confidence: 92%
   Contains diagram: Yes
   Extracted text: "求解方程式：在直角三角形 ABC 中..."

[2/5] Rephrasing problem... ✓ (2.8s)
   Domain: Geometry
   Difficulty: Medium

[3/5] Reviewing quality... ✓ (1.9s)
   Overall score: 4.7/5.0
   Status: PASSED threshold (≥4.5)

[4/5] Generating solution... ✓ (3.2s)
   Solution steps: 5
   Final answer: BC = 8

┌─────────────────────────────────────────────────────┐
│ Results                                              │
└─────────────────────────────────────────────────────┘

Original Problem (from OCR):
──────────────────────────────
求解方程式：在直角三角形 ABC 中，∠C = 90°，
若 AB = 10，AC = 6，求 BC 的長度。

[Diagram detected: 包含直角三角形 ABC...]

Rephrased Problem:
──────────────────
在一個直角三角形 PQR 中，∠R = 90°。
已知斜邊 PQ 長度為 10 公分，直角邊 PR 長度為 6 公分。
若 QR 與 PR 的比值需保持相同幾何關係，
請求出直角邊 QR 的長度。（答案四捨五入至小數點後一位）

Solution:
─────────
Step 1: 使用畢氏定理...
[Full solution shown]

Final Answer: 8.0

Session ID: a1b2c3d4-...
Saved to: ./output/a1b2c3d4.json
```

### OCR Only (No Problem Generation)

```bash
# Just extract text from photo
python -m src.cli.main ocr ./examples/math_problem_01.jpg
```

**Output**:
```
OCR Results:
─────────────────────────────────────
Confidence: 92%
Processing time: 2.3s

Extracted Text:
求解方程式：在直角三角形 ABC 中，∠C = 90°，
若 AB = 10，AC = 6，求 BC 的長度。

Diagram Detected: Yes
Description: 包含直角三角形 ABC，標註直角於 C 點，
斜邊 AB 標註長度 10，直角邊 AC 標註長度 6
```

### Process Text Problem (Skip OCR)

```bash
python -m src.cli.main process "Solve for x: 2x + 3 = 11"
```

**Output**:
```
┌─────────────────────────────────────────────────────┐
│ AgenticMath Problem Generator                        │
└─────────────────────────────────────────────────────┘

[1/4] Rephrasing problem... ✓ (2.3s)
   Domain: Algebra
   Applied dimensions: 3
   Rephrased length: 142 chars

[2/4] Reviewing quality... ✓ (1.8s)
   Overall score: 4.83/5.0
   Status: PASSED threshold (≥4.5)

[3/4] Generating solution... ✓ (3.1s)
   Solution length: 856 chars
   Answer: 2.67

┌─────────────────────────────────────────────────────┐
│ Results                                              │
└─────────────────────────────────────────────────────┘

Rephrased Problem:
──────────────────
A rectangular garden has a length that is 3 meters more
than twice its width. If the perimeter of the garden is
22 meters, find the width of the garden. Express your
answer as a decimal rounded to two decimal places.

Solution:
─────────
Step 1: Define variables...
[Full thought process shown]

Final Answer: 2.67

Session ID: 550e8400-e29b-41d4-a716-446655440000
Saved to database: problems, quality_assessments, solutions
```

### Process with Custom Escalation Dimensions

```bash
python -m src.cli.main process \
  "Find the area of a circle with radius 5" \
  --dimensions "Multi-stage Transformation" "Optimization Extension" "Uncertainty Integration"
```

### Process with Custom Quality Threshold

```bash
python -m src.cli.main process \
  "What is 10% of 50?" \
  --threshold 4.0
```

### Batch Processing

```bash
# From JSON file
python -m src.cli.main batch problems.json

# problems.json format:
# [
#   {"id": 1, "content": "Solve for x: 3x + 7 = 22"},
#   {"id": 2, "content": "Find the perimeter of a square with side 8"}
# ]
```

### View Results

```bash
# List all sessions
python -m src.cli.main list

# View specific session
python -m src.cli.main view 550e8400-e29b-41d4-a716-446655440000

# Export session to JSON
python -m src.cli.main export 550e8400-e29b-41d4-a716-446655440000 --output session.json
```

## Advanced Usage (Python API)

### Process Photo with Python

```python
from src.orchestration.pipeline import MathProblemPipeline
from src.config.settings import Settings

# Initialize pipeline
settings = Settings()  # Loads from .env
pipeline = MathProblemPipeline(settings)

# Process photo
with open("./examples/math_problem_01.jpg", "rb") as photo_file:
    result = pipeline.process_photo(
        image_file=photo_file,
        quality_threshold=4.5,
        max_iterations=5
    )

# Access OCR results
print(f"OCR Confidence: {result.ocr_metadata.confidence_score:.2%}")
print(f"Contains Diagram: {result.ocr_metadata.contains_diagram}")
if result.ocr_metadata.contains_diagram:
    print(f"Diagram: {result.ocr_metadata.diagram_description}")

# Access problem results
print(f"\nOriginal Text: {result.original_problem.content}")
print(f"Rephrased: {result.rephrased_problem.content}")
print(f"Quality Score: {result.quality_assessment.overall_score:.1f}/5.0")
print(f"Solution: {result.solution.final_answer}")
```

### Process Text Problem with Python

```python
# Process text directly (skip OCR)
result = await pipeline.process_problem(
    problem_content="Solve for x: 2x + 3 = 11",
    escalation_dimensions=[
        "Multi-stage Transformation",
        "Cross-domain Integration",
        "Real-world Parameterization"
    ],
    quality_threshold=4.5
)

# Access results
print(f"Session ID: {result.session_id}")
print(f"Final Status: {result.final_status}")
print(f"Iterations: {result.iteration_count}")
print(f"Rephrased Problem: {result.final_problem.content}")
print(f"Quality Score: {result.final_assessment.overall_score}")
print(f"Solution: {result.solution.final_answer}")
```

### Use OCR Agent Directly

```python
from src.agents.ocr_agent import ImageExtractionAgent

# Initialize OCR agent
ocr_agent = ImageExtractionAgent()

# Extract text from photo
result = ocr_agent.process({
    "image_id": "test-001",
    "file_path": "./examples/math_problem_01.jpg",
    "file_format": "jpeg",
    "file_size": 2458693,
    "ocr_config": {
        "language": "chinese_cht",
        "use_angle_cls": True,
        "use_gpu": False
    }
})

# Check results
if result["success"]:
    print(f"Extracted: {result['extracted_text']}")
    print(f"Confidence: {result['confidence_score']:.2%}")
    print(f"Processing time: {result['processing_time_ms']}ms")
else:
    print(f"Error: {result['error_message']}")
```

### Custom Agent Configuration

```python
from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from langchain.chat_models import ChatOpenAI

# Custom LLM with different parameters
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.5,  # More deterministic
    max_tokens=3000,
    request_timeout=60
)

# Initialize agents with custom LLM
rephrase_agent = RephraseAgent(llm_client=llm)
review_agent = ReviewAgent(llm_client=llm)

# Use in pipeline
pipeline = MathProblemPipeline(
    settings=settings,
    rephrase_agent=rephrase_agent,
    review_agent=review_agent
)
```

### Accessing Traceability Data

```python
from src.storage.repositories.agent_execution_repository import AgentExecutionRepository

# Get all agent executions for a session
repo = AgentExecutionRepository(database)
executions = repo.get_by_session(session_id)

for exec in executions:
    print(f"Agent: {exec.agent_type}")
    print(f"Duration: {exec.execution_time_ms}ms")
    print(f"Prompt: {exec.prompt_template[:100]}...")
    print(f"Output: {exec.output_data}")
    print("---")
```

## Configuration Options

### Quality Threshold

Controls when problems pass review:

```python
# Strict (research/publication quality)
threshold = 4.8

# Standard (classroom use)
threshold = 4.5  # Default

# Lenient (draft/brainstorming)
threshold = 4.0
```

### Escalation Dimensions

Choose ≥3 from:

1. **Multi-stage Transformation**: Chains of dependent calculations
2. **Cross-domain Integration**: Combines multiple math areas (e.g., algebra + geometry)
3. **Real-world Parameterization**: Contextual constraints, applied problems
4. **Conditional Branching**: Layered constraints, decision trees
5. **Inverse Problem Design**: Work backwards from solution
6. **Uncertainty Integration**: Measurement errors, probabilistic factors
7. **Optimization Extension**: Multi-objective optimization

**Examples**:

```python
# For beginners: Focus on multi-step and context
dimensions = [
    "Multi-stage Transformation",
    "Real-world Parameterization",
    "Cross-domain Integration"
]

# For advanced students: Complex reasoning
dimensions = [
    "Conditional Branching",
    "Inverse Problem Design",
    "Optimization Extension",
    "Uncertainty Integration"
]
```

### Maximum Iterations

Controls review-revise loop limit:

```python
# Quick iterations (may not reach threshold)
max_iterations = 3

# Standard
max_iterations = 5  # Default

# Thorough (expensive, more LLM calls)
max_iterations = 10
```

## Troubleshooting

### Problem: OCR confidence too low

**Symptom**: OCR result has confidence < 70%, system rejects photo

**Solution**:
1. **Retake photo with better conditions**:
   - Ensure good lighting (avoid shadows and reflections)
   - Hold camera steady (avoid blur)
   - Keep text horizontal (perpendicular to camera)
   - Fill frame with problem (avoid excessive whitespace)
2. **Manual preprocessing**: Use image editing app to crop, rotate, adjust contrast
3. **Manual input**: If OCR consistently fails, type problem manually
4. **Adjust threshold**: Lower `OCR_CONFIDENCE_THRESHOLD` in `.env` (e.g., 0.60)

```bash
# Check OCR quality first
python -m src.cli.main ocr problem.jpg

# If confidence is low (e.g., 65%), can still process with warning
python -m src.cli.main process-photo problem.jpg --force-ocr
```

### Problem: OCR misreads mathematical symbols

**Symptom**: Extracted text has wrong symbols (e.g., "∞" read as "8")

**Solution**:
1. **Check original photo quality**: Mathematical symbols need high resolution
2. **Use printed problems**: Handwritten symbols are harder to recognize
3. **Verify OCR output**: Always review extracted text before processing
4. **Manual correction**: Edit extracted text before passing to agents

```python
# Extract and manually correct
result = ocr_agent.process({...})
extracted_text = result["extracted_text"]

# Manual correction
corrected_text = extracted_text.replace("8", "∞")  # Fix misread symbol

# Continue with corrected text
pipeline.process_problem(problem_content=corrected_text)
```

### Problem: Photo contains diagram but not detected

**Symptom**: `contains_diagram=false` but photo clearly has geometric figure

**Solution**:
1. **Diagram quality**: Ensure diagram lines are clear and dark
2. **Check PaddleOCR version**: Older versions have weaker diagram detection
3. **Manual description**: Add diagram description manually if needed

```python
# Add diagram description manually
result = ocr_agent.process({...})

if not result["contains_diagram"] and has_diagram_in_photo:
    result["contains_diagram"] = True
    result["diagram_description"] = "手動描述：包含一個等腰三角形..."
```

### Problem: LLM refuses to generate mathematical content

**Symptom**: Agent returns non-mathematical response or apology

**Solution**:
1. Check that input problem contains clear mathematical content
2. Add mathematical keywords: "solve", "find", "calculate", "determine"
3. Verify LLM API key is valid and has sufficient credits

### Problem: Parsing errors in agent output

**Symptom**: `ParseError: Could not find ###thought### in response`

**Solution**:
1. Check LLM temperature (lower = more structured, try 0.5-0.7)
2. Verify LLM model supports instruction following (GPT-4, Claude-3+)
3. Increase max_tokens to prevent truncation
4. Check logs for raw LLM response

### Problem: Review-revise loop exceeds max iterations

**Symptom**: Final status = `MAX_ITERATIONS_EXCEEDED`, score still < threshold

**Solution**:
1. Lower quality threshold temporarily
2. Simplify original problem (may be too complex to improve)
3. Check if suggestions are being applied (view agent execution logs)
4. Increase max iterations or use manual revision

### Problem: Solutions are incorrect

**Symptom**: Solver Agent produces wrong answer

**Solution**:
1. Verify problem is mathematically solvable (check review score)
2. Use more capable LLM model (GPT-4 > GPT-3.5)
3. Add verification step in prompt (see solver-agent.md contract)
4. Report issue with problem/solution pair for debugging

## Performance Optimization

### Caching Strategies

```python
# Cache LLM responses for identical inputs
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

set_llm_cache(SQLiteCache(database_path=".langchain.db"))
```

### Parallel Processing

```python
import asyncio
from typing import List

async def process_batch(problems: List[str]):
    """Process multiple problems concurrently."""
    tasks = [pipeline.process_problem(p) for p in problems]
    results = await asyncio.gather(*tasks)
    return results

# Usage
problems = ["Problem 1", "Problem 2", "Problem 3"]
results = asyncio.run(process_batch(problems))
```

### Cost Estimation

Approximate LLM API costs per problem:

| Stage | Tokens (Input + Output) | Cost (GPT-4) | Cost (Claude-3) |
|-------|------------------------|--------------|-----------------|
| Rephrase | 1000 + 500 | $0.045 | $0.023 |
| Review | 800 + 400 | $0.036 | $0.018 |
| Revise (if needed) | 1000 + 500 | $0.045 | $0.023 |
| Solver | 1200 + 800 | $0.060 | $0.030 |
| **Total (no revise)** | **~3700 tokens** | **~$0.14** | **~$0.07** |
| **Total (1 revise iteration)** | **~5200 tokens** | **~$0.18** | **~$0.09** |

**Note**: Actual costs vary based on problem complexity and LLM pricing.

## Next Steps

- **Implement**: See `tasks.md` for implementation roadmap
- **Extend**: Add custom agents or escalation dimensions
- **Integrate**: Build web API (FastAPI) for production use
- **Evaluate**: Collect human ratings to validate quality scores

## Reference

- **Specification**: `spec.md` - Feature requirements and success criteria
- **Implementation Plan**: `plan.md` - Technical approach and architecture
- **Data Model**: `data-model.md` - Database schema and entities
- **Agent Contracts**: `contracts/` - Detailed input/output specifications for each agent

---

**Questions or Issues?**

Refer to project constitution (`.specify/memory/constitution.md`) for design principles and decision-making guidelines.
