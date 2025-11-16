"""
Unit tests for Solver Parser.

Tests parsing of Solver Agent's structured output format.
"""

import pytest
from src.parsers.solver_parser import (
    SolverParser,
    SolverAgentOutput,
    SolverParseError,
    parse_solver_output,
)


class TestSolverParser:
    """Test suite for SolverParser."""

    def test_parse_valid_output(self):
        """Test parsing valid solver output."""
        raw_response = """###thought###
Step 1: Define variables
Let x = unknown value

Step 2: Set up equation
2x + 3 = 11

Step 3: Solve for x
2x = 11 - 3
2x = 8
x = 4

###answer###
4
"""
        output = SolverParser.parse(raw_response)

        assert isinstance(output, SolverAgentOutput)
        assert "Step 1" in output.thought_process
        assert "Step 2" in output.thought_process
        assert "Step 3" in output.thought_process
        assert output.final_answer == "4"
        assert output.intermediate_steps is not None
        assert len(output.intermediate_steps) >= 3

    def test_parse_complex_mathematical_output(self):
        """Test parsing complex mathematical solution."""
        raw_response = """###thought###
To solve this problem, we use the Pythagorean theorem.

Step 1: Identify given information
- Right triangle ABC with right angle at C
- AB (hypotenuse) = 10
- BC (one leg) = 6
- AC (other leg) = ?

Step 2: Apply Pythagorean theorem
a² + b² = c²
AC² + BC² = AB²
AC² + 6² = 10²

Step 3: Solve for AC
AC² + 36 = 100
AC² = 64
AC = 8

Step 4: Verification
8² + 6² = 64 + 36 = 100 = 10² ✓

###answer###
8
"""
        output = SolverParser.parse(raw_response)

        assert "Pythagorean theorem" in output.thought_process
        assert output.final_answer == "8"
        assert output.intermediate_steps is not None
        assert len(output.intermediate_steps) == 4

    def test_parse_chinese_output(self):
        """Test parsing Chinese language output."""
        raw_response = """###thought###
步驟 1: 定義變量
設 x 為未知數

步驟 2: 建立方程式
2x + 3 = 11

步驟 3: 求解
2x = 8
x = 4

###answer###
4
"""
        output = SolverParser.parse(raw_response)

        assert "步驟" in output.thought_process
        assert output.final_answer == "4"

    def test_parse_with_fractional_answer(self):
        """Test parsing answer as fraction."""
        raw_response = """###thought###
Solving the equation:
3x = 8
x = 8/3

###answer###
8/3
"""
        output = SolverParser.parse(raw_response)

        assert output.final_answer == "8/3"

    def test_parse_with_decimal_answer(self):
        """Test parsing decimal answer."""
        raw_response = """###thought###
Converting to decimal:
x = 8/3 ≈ 2.67

###answer###
2.67
"""
        output = SolverParser.parse(raw_response)

        assert output.final_answer == "2.67"

    def test_parse_missing_thought_section(self):
        """Test error when thought section is missing."""
        raw_response = """###answer###
4
"""
        with pytest.raises(SolverParseError, match="Could not find ###thought### section"):
            SolverParser.parse(raw_response)

    def test_parse_missing_answer_section(self):
        """Test error when answer section is missing."""
        raw_response = """###thought###
Some reasoning here
"""
        with pytest.raises(SolverParseError, match="Could not find ###answer### section"):
            SolverParser.parse(raw_response)

    def test_parse_empty_thought_section(self):
        """Test error when thought section is empty."""
        raw_response = """###thought###

###answer###
4
"""
        with pytest.raises(SolverParseError, match="###thought### section is empty"):
            SolverParser.parse(raw_response)

    def test_parse_empty_answer_section(self):
        """Test error when answer section is empty."""
        raw_response = """###thought###
Some reasoning

###answer###

"""
        with pytest.raises(SolverParseError, match="###answer### section is empty"):
            SolverParser.parse(raw_response)

    def test_parse_case_insensitive_markers(self):
        """Test parsing with different case markers."""
        raw_response = """###THOUGHT###
Reasoning here

###ANSWER###
4
"""
        output = SolverParser.parse(raw_response)
        assert output.final_answer == "4"

    def test_extract_numbered_steps(self):
        """Test extraction of numbered steps."""
        thought = """
Step 1: First step here
Step 2: Second step here
Step 3: Third step here
"""
        steps = SolverParser._extract_intermediate_steps(thought)

        assert steps is not None
        assert len(steps) == 3
        assert "Step 1" in steps[0]
        assert "Step 2" in steps[1]
        assert "Step 3" in steps[2]

    def test_extract_bulleted_steps(self):
        """Test extraction of bulleted steps."""
        thought = """
- First step here
- Second step here
- Third step here
"""
        steps = SolverParser._extract_intermediate_steps(thought)

        assert steps is not None
        assert len(steps) == 3

    def test_extract_numbered_list_steps(self):
        """Test extraction of numbered list (1., 2., 3.)."""
        thought = """
1. First step here
2. Second step here
3. Third step here
"""
        steps = SolverParser._extract_intermediate_steps(thought)

        assert steps is not None
        assert len(steps) == 3
        assert "1." in steps[0]

    def test_extract_no_clear_steps(self):
        """Test when there are no clear steps."""
        thought = """
This is just a paragraph of reasoning without clear steps.
It flows as continuous text.
"""
        steps = SolverParser._extract_intermediate_steps(thought)

        assert steps is None

    def test_convenience_function(self):
        """Test convenience parse function."""
        raw_response = """###thought###
Reasoning

###answer###
4
"""
        output = parse_solver_output(raw_response)

        assert isinstance(output, SolverAgentOutput)
        assert output.final_answer == "4"

    def test_validation_short_thought_process(self):
        """Test validation rejects very short thought process."""
        with pytest.raises(ValueError, match="thought_process must be"):
            SolverAgentOutput(
                thought_process="Too short",
                final_answer="4"
            )

    def test_validation_empty_answer(self):
        """Test validation rejects empty answer."""
        with pytest.raises(ValueError, match="final_answer cannot be empty"):
            SolverAgentOutput(
                thought_process="This is a sufficiently long thought process",
                final_answer=""
            )

    def test_parse_multiline_answer(self):
        """Test parsing when answer spans multiple lines."""
        raw_response = """###thought###
Solving the system of equations

###answer###
x = 2
y = 3
"""
        output = SolverParser.parse(raw_response)

        # Should capture all lines
        assert "x = 2" in output.final_answer or "y = 3" in output.final_answer
