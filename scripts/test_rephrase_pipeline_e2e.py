#!/usr/bin/env python3
"""
End-to-End Test for Rephrase Pipeline with Real LLM API.

This script tests the complete pipeline with actual OpenAI API calls:
1. Rephrase Agent: escalate problem complexity
2. Review Agent: assess quality
3. Revise Agent: improve based on suggestions (if needed)
4. Iteration Manager: orchestrate review-revise loop
5. CrewAI Pipeline: complete workflow with CrewAI orchestration
6. Full Pipeline: complete workflow (custom implementation)

Requirements:
- OpenAI API key set in OPENAI_API_KEY environment variable
- Database connection (optional, can test without DB)

Usage:
    # Test individual agents
    python scripts/test_rephrase_pipeline_e2e.py --test-agent rephrase
    python scripts/test_rephrase_pipeline_e2e.py --test-agent review
    python scripts/test_rephrase_pipeline_e2e.py --test-agent revise

    # Test iteration manager
    python scripts/test_rephrase_pipeline_e2e.py --test-iteration

    # Test CrewAI pipeline (recommended - uses in-memory database)
    python scripts/test_rephrase_pipeline_e2e.py --test-crewai

    # Test full pipeline (requires database)
    python scripts/test_rephrase_pipeline_e2e.py --test-pipeline

    # Test all
    python scripts/test_rephrase_pipeline_e2e.py --test-all
"""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.llm_client import LLMClient, LLMConfig
from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from src.agents.revise_agent import ReviseAgent
from src.orchestration.iteration_manager import IterationManager


def test_rephrase_agent():
    """Test Rephrase Agent with real LLM."""
    print("\n" + "="*80)
    print("TEST 1: Rephrase Agent")
    print("="*80)

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        print("   Please set: export OPENAI_API_KEY='your-key-here'")
        return False

    print(f"✓ OpenAI API Key found: {api_key[:8]}...")

    # Initialize
    config = LLMConfig(api_key=api_key, model="gpt-4o", temperature=0.3)
    llm_client = LLMClient(config)
    agent = RephraseAgent(llm_client=llm_client)

    # Test problem
    problem = "一個長方形的長度比寬度多3公尺，周長為22公尺，求寬度。"
    dimensions = [
        "Multi-stage Transformation",
        "Real-world Parameterization",
        "Conditional Branching"
    ]

    print(f"\n📝 Original Problem:")
    print(f"   {problem}")
    print(f"\n🎯 Escalation Dimensions:")
    for dim in dimensions:
        print(f"   - {dim}")

    print(f"\n⏳ Calling Rephrase Agent...")
    start = datetime.now()

    try:
        result = agent.rephrase(
            problem_content=problem,
            escalation_dimensions=dimensions
        )

        elapsed = (datetime.now() - start).total_seconds()

        print(f"\n✅ Success! (took {elapsed:.1f}s)")
        print(f"\n📊 Results:")
        print(f"   Domain: {result.identified_domain}")
        print(f"   Difficulty: {result.baseline_difficulty}/5")
        print(f"   Competencies: {', '.join(result.core_competencies[:3])}")
        print(f"\n📝 Rephrased Question:")
        print(f"   {result.stage3_rewritten_question}")
        print(f"\n💡 Applied Dimensions: {', '.join(result.applied_dimensions)}")

        # Show usage stats
        stats = agent.get_usage_stats()
        print(f"\n📈 Token Usage:")
        print(f"   Prompt: {stats['prompt_tokens']}")
        print(f"   Completion: {stats['completion_tokens']}")
        print(f"   Total: {stats['total_tokens']}")
        print(f"   Cost: ${stats['estimated_cost_usd']:.4f}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_review_agent():
    """Test Review Agent with real LLM."""
    print("\n" + "="*80)
    print("TEST 2: Review Agent")
    print("="*80)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        return False

    print(f"✓ OpenAI API Key found")

    config = LLMConfig(api_key=api_key, model="gpt-4o", temperature=0.3)
    llm_client = LLMClient(config)
    agent = ReviewAgent(llm_client=llm_client)

    # Test with a rephrased problem
    question = """一個長方形花園的長度是寬度的兩倍再加3公尺。如果花園的周長為22公尺，
請計算花園的寬度。此外，如果每平方公尺的草皮成本為150元，計算鋪設整個花園所需的總成本。
假設寬度必須為正數，且結果四捨五入至小數點後兩位。"""

    print(f"\n📝 Question to Review:")
    print(f"   {question}")

    print(f"\n⏳ Calling Review Agent...")
    start = datetime.now()

    try:
        result = agent.review(rephrased_question=question)

        elapsed = (datetime.now() - start).total_seconds()

        print(f"\n✅ Success! (took {elapsed:.1f}s)")
        print(f"\n📊 Quality Scores:")
        print(f"   Clarity & Grammar: {result.clarity_grammar_score}/5.0")
        print(f"   Logical Coherence: {result.logical_coherence_score}/5.0")
        print(f"   Mathematical Validity: {result.mathematical_validity_score}/5.0")
        print(f"   Overall: {result.overall_score}/5.0")

        print(f"\n💭 Thought Process:")
        print(f"   {result.thought_process[:200]}...")

        if result.suggestions:
            print(f"\n💡 Suggestions ({len(result.suggestions)}):")
            for i, suggestion in enumerate(result.suggestions[:3], 1):
                print(f"   {i}. {suggestion}")
        else:
            print(f"\n✨ No suggestions - problem is excellent!")

        stats = agent.get_usage_stats()
        print(f"\n📈 Cost: ${stats['estimated_cost_usd']:.4f}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_revise_agent():
    """Test Revise Agent with real LLM."""
    print("\n" + "="*80)
    print("TEST 3: Revise Agent")
    print("="*80)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        return False

    print(f"✓ OpenAI API Key found")

    config = LLMConfig(api_key=api_key, model="gpt-4o", temperature=0.3)
    llm_client = LLMClient(config)
    agent = ReviseAgent(llm_client=llm_client)

    question = "一個長方形花園的長度比寬度多3公尺。周長為22公尺。求寬度。"
    suggestions = [
        "明確說明答案格式：要求學生將答案表示為四捨五入到小數點後兩位的數值",
        "在最終答案中包含單位（公尺）的要求"
    ]

    print(f"\n📝 Question to Revise:")
    print(f"   {question}")
    print(f"\n💡 Suggestions:")
    for i, s in enumerate(suggestions, 1):
        print(f"   {i}. {s}")

    print(f"\n⏳ Calling Revise Agent...")
    start = datetime.now()

    try:
        result = agent.revise(
            rephrased_question=question,
            suggestions=suggestions
        )

        elapsed = (datetime.now() - start).total_seconds()

        print(f"\n✅ Success! (took {elapsed:.1f}s)")
        print(f"\n📝 Revised Question:")
        print(f"   {result.revised_question}")
        print(f"\n📋 Revision Notes:")
        print(f"   {result.revision_notes}")

        stats = agent.get_usage_stats()
        print(f"\n📈 Cost: ${stats['estimated_cost_usd']:.4f}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_iteration_manager():
    """Test Iteration Manager with real LLMs."""
    print("\n" + "="*80)
    print("TEST 4: Iteration Manager (Review-Revise Loop)")
    print("="*80)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        return False

    print(f"✓ OpenAI API Key found")

    config = LLMConfig(api_key=api_key, model="gpt-4o", temperature=0.3)
    llm_client = LLMClient(config)

    review_agent = ReviewAgent(llm_client=llm_client)
    revise_agent = ReviseAgent(llm_client=llm_client)

    manager = IterationManager(
        review_agent=review_agent,
        revise_agent=revise_agent,
        quality_threshold=4.5,
        max_iterations=3,  # Limit for testing
    )

    # Start with a problem that might need improvement
    initial_question = "長方形長度比寬度多3公尺，周長22公尺，求寬度。"

    print(f"\n📝 Initial Question:")
    print(f"   {initial_question}")
    print(f"\n🎯 Quality Threshold: 4.5")
    print(f"🔄 Max Iterations: 3")

    print(f"\n⏳ Starting iteration loop...")
    start = datetime.now()

    try:
        result = manager.iterate_until_quality(
            initial_question=initial_question
        )

        elapsed = (datetime.now() - start).total_seconds()

        print(f"\n✅ Loop completed! (took {elapsed:.1f}s)")
        print(f"\n📊 Results:")
        print(f"   Status: {result.final_status.value}")
        print(f"   Final Score: {result.final_score}/5.0")
        print(f"   Iterations: {result.iteration_count}")

        print(f"\n📝 Final Question:")
        print(f"   {result.final_question}")

        print(f"\n📈 Quality Progression:")
        for i, assessment in enumerate(result.quality_assessments, 1):
            print(f"   Iteration {i}: {assessment['overall_score']}/5.0 "
                  f"({len(assessment['suggestions'])} suggestions)")

        print(f"\n📚 Revision History ({len(result.revision_history)} versions):")
        for i, version in enumerate(result.revision_history[:3], 1):
            print(f"   v{i}: {version[:60]}...")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crewai_pipeline():
    """Test CrewAI Pipeline with real LLM and in-memory database."""
    print("\n" + "="*80)
    print("TEST 5: CrewAI Pipeline (Full Workflow)")
    print("="*80)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        return False

    print(f"✓ OpenAI API Key found")

    # Setup in-memory database for testing
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.models.base import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    print(f"✓ In-memory database created")

    # Initialize pipeline
    config = LLMConfig(api_key=api_key, model="gpt-4o", temperature=0.3)
    llm_client = LLMClient(config)

    from src.orchestration.crewai_pipeline import CrewAIPipeline
    from src.models.problem import Problem, ProblemSource, MathDomain, SourceType
    from uuid import uuid4

    pipeline = CrewAIPipeline(
        llm_client=llm_client,
        db_session=db_session,
        quality_threshold=4.5,
        max_iterations=3,  # Limit for testing
    )

    # Create original problem
    original_problem = Problem(
        id=uuid4(),
        content="一個長方形的長度比寬度多3公尺，周長為22公尺，求寬度。",
        domain=MathDomain.ALGEBRA,
        competencies=["linear_equations"],
        baseline_difficulty=2,
        source=ProblemSource.ORIGINAL,
        source_type=SourceType.OCR,
    )
    db_session.add(original_problem)
    db_session.commit()

    print(f"\n📝 Original Problem:")
    print(f"   {original_problem.content}")

    dimensions = [
        "Multi-stage Transformation",
        "Real-world Parameterization",
        "Conditional Branching"
    ]

    print(f"\n🎯 Escalation Dimensions:")
    for dim in dimensions:
        print(f"   - {dim}")

    print(f"\n⏳ Running CrewAI pipeline...")
    start = datetime.now()

    try:
        result = pipeline.process(
            original_problem=original_problem,
            escalation_dimensions=dimensions,
        )

        elapsed = (datetime.now() - start).total_seconds()

        print(f"\n✅ Pipeline completed! (took {elapsed:.1f}s)")
        print(f"\n📊 Results:")
        print(f"   Session ID: {result['session_id']}")
        print(f"   Status: {result['final_status']}")
        print(f"   Final Score: {result['final_score']}/5.0")
        print(f"   Iterations: {result['iteration_count']}")
        print(f"   Total Time: {result['total_time_ms']}ms")

        print(f"\n📝 Final Question:")
        print(f"   {result['final_question'][:200]}...")

        # Verify database records
        from src.models.rephrase_session import RephraseSession
        session = db_session.query(RephraseSession).filter_by(id=result['session_id']).first()

        if session:
            print(f"\n✅ Database Verification:")
            print(f"   Session created: {session.created_at}")
            print(f"   Session completed: {session.completed_at}")
            print(f"   Final problem ID: {session.final_problem_id}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db_session.close()


def main():
    parser = argparse.ArgumentParser(description="E2E test for Rephrase Pipeline")
    parser.add_argument("--test-agent", choices=["rephrase", "review", "revise"],
                       help="Test specific agent")
    parser.add_argument("--test-iteration", action="store_true",
                       help="Test iteration manager")
    parser.add_argument("--test-pipeline", action="store_true",
                       help="Test full pipeline (requires database)")
    parser.add_argument("--test-crewai", action="store_true",
                       help="Test CrewAI pipeline (uses in-memory database)")
    parser.add_argument("--test-all", action="store_true",
                       help="Run all tests")

    args = parser.parse_args()

    print("🧪 Rephrase Pipeline E2E Tests")
    print("="*80)

    results = {}

    if args.test_all or args.test_agent == "rephrase":
        results["rephrase"] = test_rephrase_agent()

    if args.test_all or args.test_agent == "review":
        results["review"] = test_review_agent()

    if args.test_all or args.test_agent == "revise":
        results["revise"] = test_revise_agent()

    if args.test_all or args.test_iteration:
        results["iteration"] = test_iteration_manager()

    if args.test_all or args.test_crewai:
        results["crewai"] = test_crewai_pipeline()

    if args.test_pipeline:
        print("\n⚠️  Full pipeline test requires database setup")
        print("   See README for database configuration")

    # Summary
    if results:
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name}")

        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
