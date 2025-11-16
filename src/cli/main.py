#!/usr/bin/env python3
"""
AgenticMath Command-Line Interface.

Provides commands for:
- Uploading and processing photos
- Generating problems from text
- Running full pipeline (OCR → Rephrase → Solution)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

from src.config import get_settings, override_settings
from src.agents import LLMClient, LLMConfig
from src.storage.database import get_db
from src.orchestration.photo_to_problems import (
    PhotoToProblemsOrchestrator,
    PhotoToProblemsRequest,
)

# Rich console for pretty output
console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Suppress verbose library logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to .env config file")
@click.pass_context
def cli(ctx, verbose: bool, config: Optional[str]):
    """
    AgenticMath - Intelligent Math Problem Generator.

    Generate high-quality practice problems from photos or text input.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config

    setup_logging(verbose)

    # Load settings
    if config:
        os.environ["ENV_FILE"] = config
    ctx.obj["settings"] = get_settings()


@cli.command()
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--difficulty", "-d", type=int, default=3, help="Target difficulty (1-5)")
@click.option("--num-questions", "-n", type=int, default=3, help="Number of questions to generate")
@click.option("--threshold", "-t", type=float, help="Quality threshold (3.0-5.0)")
@click.pass_context
def upload(ctx, image_path: str, difficulty: int, num_questions: int, threshold: Optional[float]):
    """
    Upload a photo and generate practice problems.

    IMAGE_PATH: Path to the image file (JPG/PNG)

    Example:
        agenticmath upload photo.jpg -d 3 -n 3
    """
    settings = ctx.obj["settings"]

    # Validate inputs
    if not (1 <= difficulty <= 5):
        console.print("[red]❌ Error: Difficulty must be between 1 and 5[/red]")
        sys.exit(1)

    if not (1 <= num_questions <= 10):
        console.print("[red]❌ Error: Number of questions must be between 1 and 10[/red]")
        sys.exit(1)

    if threshold and not (3.0 <= threshold <= 5.0):
        console.print("[red]❌ Error: Threshold must be between 3.0 and 5.0[/red]")
        sys.exit(1)

    # Override settings if threshold provided
    if threshold:
        override_settings(quality_threshold=threshold)
        settings = get_settings()

    # Display header
    console.print(Panel.fit(
        "[bold blue]📸 Photo Processing Pipeline[/bold blue]\n"
        f"Image: {image_path}\n"
        f"Difficulty: {difficulty}/5\n"
        f"Questions: {num_questions}\n"
        f"Quality Threshold: {threshold or settings.quality_control.quality_threshold}",
        title="AgenticMath",
        border_style="blue"
    ))

    try:
        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            console.print("[red]❌ Error: OPENAI_API_KEY not set[/red]")
            console.print("Please set your OpenAI API key in .env file or environment")
            sys.exit(1)

        # Initialize components
        console.print("\n[cyan]🤖 Initializing components...[/cyan]")
        db = next(get_db())
        llm_client = LLMClient(LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=settings.llm.model,
            temperature=settings.llm.temperature,
        ))

        orchestrator = PhotoToProblemsOrchestrator(
            llm_client=llm_client,
            db=db,
        )

        # Create request
        request = PhotoToProblemsRequest(
            image_path=Path(image_path),
            target_difficulty=difficulty,
            num_questions=num_questions,
            min_quality_score=threshold or settings.quality_control.quality_threshold,
        )

        # Process with progress indicators
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing...", total=None)

            # Run pipeline
            result = orchestrator.process(request)

            progress.update(task, completed=True)

        # Display results
        if not result.success:
            console.print(f"\n[red]❌ Error: {result.error_message}[/red]")
            sys.exit(1)

        # OCR Results
        console.print("\n[bold green]✅ OCR Processing Complete[/bold green]")
        console.print(f"Extracted Text: {result.extracted_text[:100]}...")
        console.print(f"Confidence: {result.ocr_result.get('confidence_score', 0):.2%}")

        # Generation Results
        gen_result = result.generation_result
        console.print(f"\n[bold green]✅ Generated {gen_result.selected} Questions[/bold green]")

        # Display questions in a table
        table = Table(title="Generated Questions", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Difficulty", justify="center", width=10)
        table.add_column("Quality", justify="center", width=10)
        table.add_column("Content", width=50)

        for i, q in enumerate(gen_result.questions, 1):
            table.add_row(
                str(i),
                q['variant_type'],
                f"{q['difficulty']}/5",
                f"{q['quality_score']:.1f}/5",
                q['content'][:47] + "..." if len(q['content']) > 50 else q['content']
            )

        console.print(table)

        # Cost summary
        console.print(f"\n[bold]💰 Cost Summary[/bold]")
        console.print(f"Total Tokens: {llm_client.total_tokens_used:,}")
        console.print(f"Total Cost: ${llm_client.total_cost_usd:.4f}")

        console.print("\n[bold green]🎉 Processing complete![/bold green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        if ctx.obj["verbose"]:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("problem_text")
@click.option("--difficulty", "-d", type=int, default=3, help="Target difficulty (1-5)")
@click.option("--num-questions", "-n", type=int, default=1, help="Number of questions to generate")
@click.option("--threshold", "-t", type=float, help="Quality threshold (3.0-5.0)")
@click.option("--with-solution", "-s", is_flag=True, help="Generate solution for problems")
@click.pass_context
def generate(
    ctx, problem_text: str, difficulty: int, num_questions: int, threshold: Optional[float],
    with_solution: bool
):
    """
    Generate practice problems from text input.

    PROBLEM_TEXT: The original problem text

    Example:
        agenticmath generate "Solve: 2x + 3 = 11" -d 3 -n 2 -s
    """
    settings = ctx.obj["settings"]

    # Validate inputs
    if not (1 <= difficulty <= 5):
        console.print("[red]❌ Error: Difficulty must be between 1 and 5[/red]")
        sys.exit(1)

    if not (1 <= num_questions <= 10):
        console.print("[red]❌ Error: Number of questions must be between 1 and 10[/red]")
        sys.exit(1)

    if threshold and not (3.0 <= threshold <= 5.0):
        console.print("[red]❌ Error: Threshold must be between 3.0 and 5.0[/red]")
        sys.exit(1)

    # Override settings if threshold provided
    if threshold:
        override_settings(quality_threshold=threshold)
        settings = get_settings()

    # Display header
    console.print(Panel.fit(
        "[bold blue]📝 Text-based Problem Generation[/bold blue]\n"
        f"Original: {problem_text[:50]}...\n"
        f"Difficulty: {difficulty}/5\n"
        f"Questions: {num_questions}\n"
        f"Quality Threshold: {threshold or settings.quality_control.quality_threshold}\n"
        f"Generate Solution: {with_solution}",
        title="AgenticMath",
        border_style="blue"
    ))

    try:
        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            console.print("[red]❌ Error: OPENAI_API_KEY not set[/red]")
            console.print("Please set your OpenAI API key in .env file or environment")
            sys.exit(1)

        # Initialize components
        console.print("\n[cyan]🤖 Initializing components...[/cyan]")
        from src.agents import RephraseAgent, ReviewAgent, SolverAgent
        from src.orchestration import IterationManager

        db = next(get_db())
        llm_client = LLMClient(LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=settings.llm.model,
            temperature=settings.llm.temperature,
        ))

        rephrase_agent = RephraseAgent(llm_client=llm_client, db=db)
        review_agent = ReviewAgent(llm_client=llm_client, db=db)
        iteration_manager = IterationManager(
            review_agent=review_agent,
            revise_agent=None,  # Will use internal revision
            threshold=threshold or settings.quality_control.quality_threshold,
            max_iterations=settings.quality_control.max_revise_iterations,
        )

        # Process with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Rephrase
            task = progress.add_task("[cyan]Rephrasing problem...", total=None)
            rephrased = rephrase_agent.rephrase(
                problem_content=problem_text,
                escalation_dimensions=settings.escalation.default_escalation_dimensions[:3],
            )
            progress.update(task, completed=True)

            # Review and iterate
            task = progress.add_task("[cyan]Reviewing quality...", total=None)
            iteration_result = iteration_manager.iterate_until_quality(
                initial_question=rephrased.stage3_rewritten_question
            )
            progress.update(task, completed=True)

            # Generate solution if requested
            if with_solution:
                task = progress.add_task("[cyan]Generating solution...", total=None)
                solver_agent = SolverAgent(llm_client=llm_client, db=db)
                solution = solver_agent.solve(iteration_result.final_question)
                progress.update(task, completed=True)

        # Display results
        console.print("\n[bold green]✅ Generation Complete[/bold green]")
        console.print(f"\nOriginal Problem:\n  {problem_text}")
        console.print(f"\nGenerated Problem (Quality: {iteration_result.final_score:.1f}/5):")
        console.print(Panel(iteration_result.final_question, border_style="green"))

        if with_solution:
            console.print(f"\n[bold]Solution:[/bold]")
            console.print(f"Answer: {solution.final_answer}")
            console.print(f"\nReasoning Process:")
            console.print(Panel(solution.thought_process[:500] + "...", border_style="cyan"))

        # Cost summary
        console.print(f"\n[bold]💰 Cost Summary[/bold]")
        console.print(f"Total Tokens: {llm_client.total_tokens_used:,}")
        console.print(f"Total Cost: ${llm_client.total_cost_usd:.4f}")

        console.print("\n[bold green]🎉 Generation complete![/bold green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        if ctx.obj["verbose"]:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
def version():
    """Display version information."""
    console.print("[bold blue]AgenticMath[/bold blue] version 0.1.0")
    console.print("Intelligent Math Problem Generator")


@cli.command()
@click.pass_context
def config(ctx):
    """Display current configuration."""
    settings = ctx.obj["settings"]

    table = Table(title="Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", width=30)
    table.add_column("Value", style="green", width=50)

    table.add_row("Environment", settings.environment)
    table.add_row("LLM Model", settings.llm.model)
    table.add_row("LLM Temperature", str(settings.llm.temperature))
    table.add_row("Quality Threshold", str(settings.quality_control.quality_threshold))
    table.add_row("Max Iterations", str(settings.quality_control.max_revise_iterations))
    table.add_row("OCR Language", settings.ocr.language)
    table.add_row("Database URL", settings.database.url)
    table.add_row("Upload Directory", str(settings.file_upload.upload_dir))

    console.print(table)


if __name__ == "__main__":
    cli(obj={})
