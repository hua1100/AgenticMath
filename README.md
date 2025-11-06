# AgenticMath

An intelligent agent system for generating high-quality mathematics problems that enhance student learning.

## Overview

AgenticMath helps students improve their mathematical understanding by generating conceptually similar practice problems. Students can upload problems they find confusing or have made mistakes on, and the system creates clear, logically consistent, error-free questions that help learners discover concepts, strategies, and patterns.

## Core Features

- **Photo Upload & OCR**: Students can upload photos of math problems (printed or handwritten)
- **Problem Upload**: Students submit math problems they struggle with
- **Conceptual Analysis**: System identifies the underlying mathematical concepts
- **Problem Generation**: Creates similar problems that target the same concepts
- **Quality Control Loop**: Automated review and revision until quality threshold is met
- **Solution Generation**: Detailed step-by-step solutions with chain-of-thought reasoning
- **Learning Support**: Generated problems help students discover patterns and strategies
- **Quality Assurance**: All problems are mathematically correct and pedagogically effective

## Technical Stack

- **Agent Framework**: CrewAI (MIT licensed, role-based multi-agent orchestration)
- **LLM**: OpenAI GPT-4.1 (GPT-4o/GPT-4 Turbo) for optimal math problem quality
- **OCR**: PaddleOCR 2.7.0 (Apache 2.0, Traditional Chinese support)
- **Database**: SQLAlchemy 2.0+ with SQLite (dev) or PostgreSQL (production)
- **Language**: Python 3.11+

## Project Principles

This project follows Specification-Driven Development (SDD) and is guided by six core principles:

1. **Educational Value First** - Prioritize pedagogical effectiveness
2. **Mathematical Correctness** - Ensure rigor and clarity
3. **Conceptual Consistency** - Maintain concept alignment across problems
4. **Testability** - Enable automated verification
5. **Simplicity** - Favor maintainable architectures
6. **Explainability** - Make generation decisions transparent

See [`.specify/memory/constitution.md`](.specify/memory/constitution.md) for full details.

## Project Structure

```
AgenticMath/
├── .specify/                    # SDD framework files
│   ├── memory/
│   │   └── constitution.md      # Project constitution and principles
│   └── templates/
│       ├── plan-template.md     # Implementation plan template
│       ├── spec-template.md     # Feature specification template
│       └── tasks-template.md    # Task list template
├── specs/                       # Feature specifications
│   └── 001-multi-agent-problem-generator/
│       ├── spec.md             # Feature specification
│       ├── plan.md             # Implementation plan
│       ├── research.md         # Research findings
│       ├── data-model.md       # Data models
│       ├── quickstart.md       # Getting started guide
│       ├── workflow-state-machine.md  # State machine definition
│       ├── config-schema.md    # Configuration schema
│       ├── contracts/          # Agent contracts
│       │   ├── image-extraction-agent.md
│       │   ├── rephrase-agent.md
│       │   ├── review-agent.md
│       │   ├── revise-agent.md
│       │   └── solver-agent.md
│       └── tasks.md            # Implementation tasks
├── src/                        # Source code
│   ├── agents/                 # Agent implementations
│   ├── models/                 # Pydantic data models
│   ├── ocr/                    # OCR and image processing
│   ├── storage/                # Database and repositories
│   ├── orchestration/          # Pipeline and workflow
│   ├── config/                 # Configuration management
│   ├── cli/                    # Command-line interface
│   └── api/                    # REST API (optional)
├── tests/                      # Test suites
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── logs/                       # Application logs
├── uploads/                    # Uploaded photos
├── pyproject.toml              # Project configuration
├── requirements.txt            # Python dependencies
└── .env.example               # Environment variables template
```

## Development Workflow

### SDD Process

This project uses Specification-Driven Development. For each new feature:

1. **Create Specification** (`/speckit.spec`):
   - Define user stories with priorities
   - Document requirements and success criteria
   - Identify key entities and edge cases

2. **Create Implementation Plan** (`/speckit.plan`):
   - Research technical approaches
   - Design data models
   - Define API contracts
   - Create quickstart guide

3. **Generate Tasks** (`/speckit.tasks`):
   - Break down into actionable tasks
   - Organize by user story
   - Enable incremental delivery

4. **Implement**:
   - Follow task list
   - Test each user story independently
   - Deliver MVP incrementally

### Next Steps

To start developing features:

1. Review the constitution: `.specify/memory/constitution.md`
2. Create your first feature specification using the SDD commands
3. Follow the implementation plan to build incrementally

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- OpenAI API key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/AgenticMath.git
   cd AgenticMath
   ```

2. **Create virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Initialize database**:
   ```bash
   alembic upgrade head
   ```

### Quick Start

#### Process a photo of a math problem:
```bash
python -m src.cli.main process-photo ./examples/math_problem.jpg
```

#### Process text directly:
```bash
python -m src.cli.main process "Solve for x: 2x + 3 = 11"
```

#### Check OCR result only:
```bash
python -m src.cli.main ocr ./examples/math_problem.jpg
```

For detailed usage instructions, see [specs/001-multi-agent-problem-generator/quickstart.md](specs/001-multi-agent-problem-generator/quickstart.md).

### Configuration

All configuration is done through environment variables in `.env`:

- **LLM Settings**: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE`
- **OCR Settings**: `OCR_LANGUAGE`, `OCR_CONFIDENCE_THRESHOLD`, `OCR_USE_GPU`
- **Quality Control**: `QUALITY_THRESHOLD`, `MAX_REVISE_ITERATIONS`

See [specs/001-multi-agent-problem-generator/config-schema.md](specs/001-multi-agent-problem-generator/config-schema.md) for full configuration reference.

### Development

#### Running tests:
```bash
pytest tests/
```

#### Code formatting:
```bash
black src/ tests/
ruff check src/ tests/
```

#### Type checking:
```bash
mypy src/
```

## Contributing

All contributions must:
- Align with project principles in the constitution
- Include a Constitution Check in specifications
- Follow SDD workflow for new features
- Maintain test coverage and documentation

## License

*To be determined*

---

**Project Status**: Initialized (2025-11-06)

This project structure supports systematic, principled development of educational software that truly serves student learning.
