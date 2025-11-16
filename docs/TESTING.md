># AgenticMath Testing Guide

Comprehensive testing guide for AgenticMath project.

## Test Structure

```
tests/
├── unit/                       # Unit tests (fast, isolated)
│   ├── agents/                 # Agent unit tests
│   │   └── test_llm_client.py
│   ├── test_solver_parser.py   # Solver parser tests
│   ├── test_settings.py        # Configuration tests
│   ├── test_problem_creator.py
│   ├── test_image_uploader.py
│   ├── test_diagram_processor.py
│   └── ...
├── integration/                # Integration tests (slower, real components)
│   ├── test_solution_generation.py
│   ├── test_ocr_pipeline.py
│   ├── test_full_rephrase_pipeline.py
│   └── test_crewai_pipeline.py
├── contract/                   # Contract validation tests
│   ├── test_solver_contract.py
│   ├── test_rephrase_contract.py
│   ├── test_review_contract.py
│   └── test_revise_contract.py
├── e2e/                        # End-to-end tests
│   └── test_ocr_to_problem.py
└── fixtures/                   # Test data and helpers
    ├── create_test_images.py
    └── create_diagram_test_images.py
```

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (optional for unit tests with mocks)
cp .env.example .env
# Edit .env if running integration tests
```

### Run All Tests

```bash
# Run all tests
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test Suites

```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Contract validation tests
pytest tests/contract/

# End-to-end tests
pytest tests/e2e/
```

### Run Specific Test Files

```bash
# Solver parser tests
pytest tests/unit/test_solver_parser.py

# Configuration tests
pytest tests/unit/test_settings.py

# Solution generation integration
pytest tests/integration/test_solution_generation.py

# Solver contract validation
pytest tests/contract/test_solver_contract.py
```

### Run Specific Test Cases

```bash
# Single test function
pytest tests/unit/test_solver_parser.py::TestSolverParser::test_parse_valid_output

# Single test class
pytest tests/unit/test_solver_parser.py::TestSolverParser

# Tests matching pattern
pytest tests/ -k "solver"
pytest tests/ -k "parse"
```

## Test Categories

### 1. Unit Tests (Fast, No External Dependencies)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Use mocks for external dependencies
- No database or API calls
- Fast execution (< 1 second each)
- High coverage of edge cases

**Examples**:
```bash
pytest tests/unit/test_solver_parser.py
pytest tests/unit/test_settings.py
```

**Coverage Target**: ≥80% code coverage

### 2. Integration Tests (Slower, Real Components)

**Purpose**: Test component interactions

**Characteristics**:
- Use in-memory database
- May use mocked LLM (for cost/speed)
- Test data flow between components
- Moderate speed (1-10 seconds each)

**Examples**:
```bash
pytest tests/integration/test_solution_generation.py
pytest tests/integration/test_ocr_pipeline.py
```

### 3. Contract Validation Tests

**Purpose**: Ensure agents follow their contracts

**Characteristics**:
- Validate input/output formats
- Check against specs
- Test contract examples
- Verify functional requirements

**Examples**:
```bash
pytest tests/contract/test_solver_contract.py
pytest tests/contract/test_rephrase_contract.py
```

### 4. End-to-End Tests (Slowest, Real APIs)

**Purpose**: Test complete workflows

**Characteristics**:
- Use real APIs (requires API keys)
- Full database integration
- Expensive (uses tokens)
- Slow (10+ seconds each)

**Examples**:
```bash
# Requires OPENAI_API_KEY
pytest tests/e2e/test_ocr_to_problem.py
```

## Writing Tests

### Test Naming Conventions

```python
# Test classes: TestComponentName
class TestSolverParser:
    pass

# Test methods: test_what_it_does
def test_parse_valid_output(self):
    pass

# Contract tests: test_contract_requirement
def test_contract_output_has_final_answer(self):
    pass
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = Mock()
    client.chat_completion = Mock(return_value={
        "content": "###thought###\nReasoning\n###answer###\n4"
    })
    return client

def test_something(mock_llm_client):
    # Use fixture
    agent = SolverAgent(llm_client=mock_llm_client)
    result = agent.solve("Question")
    assert result.final_answer == "4"
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

# Mock LLM client
mock_client = Mock()
mock_client.chat_completion = Mock(return_value={"content": "..."})

# Mock database
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

### Testing Exceptions

```python
# Test that exception is raised
with pytest.raises(ValueError, match="error message"):
    function_that_should_fail()

# Test specific error message
with pytest.raises(SolverParseError, match="Could not find"):
    SolverParser.parse("invalid")
```

## Coverage Reports

### Generate HTML Coverage Report

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### View Coverage in Terminal

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Coverage Targets by Module

| Module | Target | Current Status |
|--------|--------|----------------|
| `src/agents/` | ≥80% | ✅ Achieved |
| `src/parsers/` | ≥90% | ✅ Achieved |
| `src/orchestration/` | ≥70% | ⚠️ In Progress |
| `src/config/` | ≥85% | ✅ Achieved |
| `src/ocr/` | ≥75% | ✅ Achieved |
| `src/models/` | ≥90% | ✅ Achieved |

## Test Data

### Creating Test Fixtures

```bash
# Create test images
python tests/fixtures/create_test_images.py

# Create diagram test images
python tests/fixtures/create_diagram_test_images.py
```

### Using Test Data

```python
import pytest
from pathlib import Path

@pytest.fixture
def test_image():
    """Get path to test image."""
    return Path(__file__).parent / "fixtures" / "test_triangle.jpg"

def test_with_image(test_image):
    result = process_image(test_image)
    assert result["success"]
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=src
```

## Common Issues and Solutions

### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're in project root
cd /path/to/AgenticMath

# Install in development mode
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH=/path/to/AgenticMath:$PYTHONPATH
```

### 2. Database Errors

**Problem**: Database schema mismatch

**Solution**:
```bash
# Reset test database
rm agenticmath.db
alembic upgrade head
```

### 3. API Key Errors

**Problem**: Tests fail with missing API key

**Solution**:
- Unit tests: Use mocks (no API key needed)
- Integration tests: Set `OPENAI_API_KEY` in `.env`
- E2E tests: Requires real API key

### 4. Slow Tests

**Problem**: Tests take too long

**Solution**:
```bash
# Run only fast tests
pytest tests/unit/

# Skip slow tests
pytest tests/ -m "not slow"

# Parallel execution
pytest tests/ -n auto
```

## Best Practices

### 1. Test Isolation

Each test should be independent:

```python
# Good: Use fixtures for fresh state
@pytest.fixture
def fresh_db():
    # Create new database for each test
    ...

# Bad: Shared state between tests
global_db = create_database()  # Don't do this
```

### 2. Clear Test Names

```python
# Good: Describes what is being tested
def test_solver_parser_handles_missing_answer_section():
    ...

# Bad: Vague name
def test_parser():
    ...
```

### 3. Arrange-Act-Assert Pattern

```python
def test_something():
    # Arrange: Set up test data
    input_data = "test"

    # Act: Execute the function
    result = function_under_test(input_data)

    # Assert: Verify result
    assert result == expected_value
```

### 4. Test One Thing

```python
# Good: Tests one behavior
def test_parse_extracts_answer():
    output = parse("###thought###\nX\n###answer###\n4")
    assert output.final_answer == "4"

# Bad: Tests multiple behaviors
def test_parse_everything():
    output = parse("...")
    assert output.final_answer == "4"
    assert output.thought_process is not None
    assert len(output.intermediate_steps) > 0
    # Too many assertions
```

### 5. Use Mocks for External Services

```python
# Good: Mock LLM calls
@patch('src.agents.llm_client.LLMClient')
def test_with_mock(mock_llm):
    ...

# Bad: Call real API in unit tests
def test_with_real_api():
    client = LLMClient(api_key=os.getenv("OPENAI_API_KEY"))
    # Expensive and slow
```

## Test Metrics

### Current Status

- **Total Tests**: 150+
- **Unit Tests**: 80+
- **Integration Tests**: 40+
- **Contract Tests**: 30+
- **Code Coverage**: 85%+

### Coverage by Phase

| Phase | Component | Coverage |
|-------|-----------|----------|
| P0 | OCR Pipeline | 94% ✅ |
| P1 | Rephrase Pipeline | 87% ✅ |
| P1 | Review/Revise Loop | 85% ✅ |
| P2 | Solver Agent | 92% ✅ |
| P2 | Solution Pipeline | 88% ✅ |
| P3 | Configuration | 91% ✅ |
| P3 | CLI | 65% ⚠️ |

## Next Steps

1. **Increase CLI Test Coverage** (target: 80%)
2. **Add Performance Tests** (measure latency, throughput)
3. **Add Load Tests** (stress test with many requests)
4. **Improve E2E Tests** (full user workflows)
5. **Add Visual Regression Tests** (for CLI output)

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Plugin](https://pytest-cov.readthedocs.io/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Support

For testing issues or questions:
- Review test examples in `tests/` directory
- Check CI logs in GitHub Actions
- Consult project specifications in `specs/`
