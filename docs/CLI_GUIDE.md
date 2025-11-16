# AgenticMath CLI User Guide

Complete guide for using the AgenticMath command-line interface.

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Make CLI executable** (optional):
   ```bash
   chmod +x agenticmath
   ```

## Quick Start

### Basic Usage

```bash
# Display help
./agenticmath --help

# Display version
./agenticmath version

# View current configuration
./agenticmath config
```

### Upload Photo and Generate Problems

Upload a math problem photo and generate practice problems:

```bash
./agenticmath upload photo.jpg -d 3 -n 3
```

**Options:**
- `-d, --difficulty`: Target difficulty level (1-5, default: 3)
- `-n, --num-questions`: Number of questions to generate (1-10, default: 3)
- `-t, --threshold`: Quality threshold (3.0-5.0, default: 4.5)

**Examples:**

```bash
# Basic upload with default settings
./agenticmath upload triangle_problem.jpg

# Generate 5 difficult questions with custom threshold
./agenticmath upload algebra.png -d 5 -n 5 -t 4.8

# Easy questions with lower quality threshold
./agenticmath upload simple_problem.jpg -d 2 -n 2 -t 4.0
```

### Generate Problems from Text

Generate practice problems from text input:

```bash
./agenticmath generate "Solve: 2x + 3 = 11" -d 3 -n 2
```

**Options:**
- `-d, --difficulty`: Target difficulty level (1-5, default: 3)
- `-n, --num-questions`: Number of questions to generate (1-10, default: 1)
- `-t, --threshold`: Quality threshold (3.0-5.0, default: 4.5)
- `-s, --with-solution`: Generate solution for problems

**Examples:**

```bash
# Generate one similar problem
./agenticmath generate "What is sin(45°)?"

# Generate 3 problems with solutions
./agenticmath generate "在直角三角形ABC中，AB=10，BC=6，求AC" -d 3 -n 3 -s

# Generate difficult problem with high quality requirement
./agenticmath generate "Solve the quadratic equation: x² + 5x + 6 = 0" -d 5 -t 4.8 -s
```

## Global Options

Available for all commands:

- `-v, --verbose`: Enable verbose logging (shows detailed debug information)
- `-c, --config`: Path to custom .env config file

**Examples:**

```bash
# Verbose mode for debugging
./agenticmath upload photo.jpg -v

# Use custom config file
./agenticmath generate "Problem text" -c /path/to/custom.env
```

## Command Reference

### `upload`

Upload and process a photo of a math problem.

**Syntax:**
```bash
agenticmath upload IMAGE_PATH [OPTIONS]
```

**Arguments:**
- `IMAGE_PATH`: Path to image file (JPG/PNG)

**Options:**
- `-d, --difficulty INTEGER`: Target difficulty (1-5) [default: 3]
- `-n, --num-questions INTEGER`: Number of questions (1-10) [default: 3]
- `-t, --threshold FLOAT`: Quality threshold (3.0-5.0) [default: 4.5]

**Output:**
- OCR extraction results
- Generated questions in a table format
- Cost summary (tokens and USD)

### `generate`

Generate practice problems from text input.

**Syntax:**
```bash
agenticmath generate PROBLEM_TEXT [OPTIONS]
```

**Arguments:**
- `PROBLEM_TEXT`: The original problem text

**Options:**
- `-d, --difficulty INTEGER`: Target difficulty (1-5) [default: 3]
- `-n, --num-questions INTEGER`: Number of questions (1-10) [default: 1]
- `-t, --threshold FLOAT`: Quality threshold (3.0-5.0) [default: 4.5]
- `-s, --with-solution`: Generate solution for problems

**Output:**
- Original problem
- Generated problem with quality score
- Solution (if `-s` flag is used)
- Cost summary

### `version`

Display version information.

**Syntax:**
```bash
agenticmath version
```

### `config`

Display current configuration settings.

**Syntax:**
```bash
agenticmath config
```

**Output:**
Shows all active configuration values:
- Environment
- LLM settings
- Quality control settings
- OCR settings
- Database settings

## Configuration

### Environment Variables

All configuration is managed through environment variables (`.env` file).

**Key Settings:**

```env
# LLM Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

# Quality Control
QUALITY_THRESHOLD=4.5
MAX_REVISE_ITERATIONS=5

# OCR Settings
OCR_LANGUAGE=chinese_cht
OCR_USE_GPU=false

# Database
DATABASE_URL=sqlite:///./agenticmath.db
```

### Runtime Configuration Override

You can override quality threshold at runtime:

```bash
# Use lower quality threshold for this run
./agenticmath upload photo.jpg -t 4.0

# Use higher quality threshold
./agenticmath generate "Problem" -t 4.8
```

## Output Format

### Upload Command Output

```
┌─ AgenticMath ─────────────────────────────────────────┐
│ 📸 Photo Processing Pipeline                          │
│ Image: photo.jpg                                      │
│ Difficulty: 3/5                                       │
│ Questions: 3                                          │
│ Quality Threshold: 4.5                                │
└───────────────────────────────────────────────────────┘

🤖 Initializing components...
⣾ Processing...

✅ OCR Processing Complete
Extracted Text: 在直角三角形ABC中...
Confidence: 92.5%

✅ Generated 3 Questions

      Generated Questions
┌───┬────────────┬────────┬─────────┬────────┐
│ # │ Type       │ Diff   │ Quality │ Content│
├───┼────────────┼────────┼─────────┼────────┤
│ 1 │ Similar    │ 3/5    │ 4.6/5   │ ...    │
│ 2 │ Escalated  │ 4/5    │ 4.7/5   │ ...    │
│ 3 │ Variant    │ 3/5    │ 4.8/5   │ ...    │
└───┴────────────┴────────┴─────────┴────────┘

💰 Cost Summary
Total Tokens: 3,245
Total Cost: $0.0324

🎉 Processing complete!
```

### Generate Command Output

```
┌─ AgenticMath ─────────────────────────────────────────┐
│ 📝 Text-based Problem Generation                      │
│ Original: Solve: 2x + 3 = 11                          │
│ Difficulty: 3/5                                       │
│ Questions: 1                                          │
│ Quality Threshold: 4.5                                │
│ Generate Solution: True                               │
└───────────────────────────────────────────────────────┘

🤖 Initializing components...
⣾ Rephrasing problem...
⣾ Reviewing quality...
⣾ Generating solution...

✅ Generation Complete

Original Problem:
  Solve: 2x + 3 = 11

Generated Problem (Quality: 4.7/5):
┌─────────────────────────────────────────────────────┐
│ A rectangular garden has a length that is 3 meters │
│ more than twice its width. If the perimeter of the │
│ garden is 22 meters, find the width of the garden. │
└─────────────────────────────────────────────────────┘

Solution:
Answer: 2.67

Reasoning Process:
┌─────────────────────────────────────────────────────┐
│ Step 1: Define variables...                        │
│ Step 2: Set up equation...                         │
│ [Full reasoning shown]                             │
└─────────────────────────────────────────────────────┘

💰 Cost Summary
Total Tokens: 2,156
Total Cost: $0.0216

🎉 Generation complete!
```

## Error Handling

The CLI provides clear error messages for common issues:

### Missing API Key
```
❌ Error: OPENAI_API_KEY not set
Please set your OpenAI API key in .env file or environment
```

### Invalid File
```
❌ Error: Image file not found: nonexistent.jpg
```

### Invalid Parameters
```
❌ Error: Difficulty must be between 1 and 5
❌ Error: Threshold must be between 3.0 and 5.0
```

### Processing Errors
Use `-v` flag to see detailed error information:

```bash
./agenticmath upload photo.jpg -v
```

## Tips and Best Practices

### 1. **Start with Default Settings**
   ```bash
   ./agenticmath upload photo.jpg
   ```

### 2. **Adjust Difficulty Gradually**
   - Start at difficulty 3
   - Increase to 4-5 for more challenging problems
   - Use 1-2 for simpler practice

### 3. **Quality Threshold**
   - Default 4.5 provides high-quality output
   - Lower to 4.0 if generation is too slow
   - Raise to 4.8 for maximum quality

### 4. **Number of Questions**
   - 3 questions is a good balance
   - More questions = higher cost
   - Consider token usage for large batches

### 5. **Use Solution Generation Wisely**
   - Solution generation doubles cost
   - Use `-s` flag only when needed
   - Good for understanding reasoning

### 6. **Monitor Costs**
   - Check cost summary after each run
   - Typical cost: $0.02-$0.05 per run
   - Use verbose mode to track token usage

## Troubleshooting

### Command Not Found

If you get "command not found" error:

```bash
# Option 1: Use Python directly
python src/cli/main.py --help

# Option 2: Make script executable
chmod +x agenticmath
./agenticmath --help

# Option 3: Use Python module syntax
python -m src.cli.main --help
```

### Import Errors

Ensure you're in the project root directory:

```bash
cd /path/to/AgenticMath
./agenticmath --help
```

### Database Errors

Reset the database if needed:

```bash
rm agenticmath.db
alembic upgrade head
```

### OCR Issues

For OCR problems:
- Ensure image is clear and well-lit
- Supported formats: JPG, PNG
- Maximum size: 10MB (configurable)
- Check OCR logs with `-v` flag

## Examples Gallery

### Example 1: Basic Algebra

```bash
./agenticmath generate "Solve: 3x - 7 = 14" -s
```

### Example 2: Geometry with Photo

```bash
./agenticmath upload triangle.jpg -d 4 -n 3
```

### Example 3: Trigonometry

```bash
./agenticmath generate "求 cos 60° 的值" -d 3 -s
```

### Example 4: Batch Generation

```bash
# Generate multiple problems with high quality
./agenticmath generate "Factor: x² + 5x + 6" -d 4 -n 5 -t 4.8
```

## Support

For issues, questions, or contributions:
- GitHub Issues: [hua1100/AgenticMath](https://github.com/hua1100/AgenticMath/issues)
- Documentation: `docs/` directory
- Specifications: `specs/001-multi-agent-problem-generator/`

## License

MIT License - See LICENSE file for details.
