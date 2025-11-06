# AgenticMath

An intelligent agent system for generating high-quality mathematics problems that enhance student learning.

## Overview

AgenticMath helps students improve their mathematical understanding by generating conceptually similar practice problems. Students can upload problems they find confusing or have made mistakes on, and the system creates clear, logically consistent, error-free questions that help learners discover concepts, strategies, and patterns.

## Core Features

- **Problem Upload**: Students submit math problems they struggle with
- **Conceptual Analysis**: System identifies the underlying mathematical concepts
- **Problem Generation**: Creates similar problems that target the same concepts
- **Learning Support**: Generated problems help students discover patterns and strategies
- **Quality Assurance**: All problems are mathematically correct and pedagogically effective

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
├── specs/                       # Feature specifications (created per feature)
│   └── [###-feature-name]/
│       ├── spec.md             # Feature specification
│       ├── plan.md             # Implementation plan
│       ├── research.md         # Research findings
│       ├── data-model.md       # Data models
│       ├── quickstart.md       # Getting started guide
│       ├── contracts/          # API contracts
│       └── tasks.md            # Implementation tasks
├── src/                        # Source code (to be created)
└── tests/                      # Test suites (to be created)
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

*This section will be populated once the first feature is implemented.*

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
