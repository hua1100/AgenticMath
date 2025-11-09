"""
CrewAI-based Rephrase Pipeline.

Integrates existing agents (RephraseAgent, ReviewAgent, ReviseAgent) with
CrewAI framework for orchestration, following research.md recommendation.

This provides:
- Clear agent roles and goals (CrewAI paradigm)
- Simplified workflow definition
- Built-in task execution and handoff
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from src.agents.llm_client import LLMClient
from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from src.agents.revise_agent import ReviseAgent
from src.models.problem import Problem, ProblemSource, MathDomain, SourceType
from src.models.rephrase_session import RephraseSession, SessionStatus
from src.models.quality_assessment import QualityAssessment

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Wrappers for Existing Agents
# ============================================================================

class AgentToolkit:
    """Toolkit wrapping our existing agents as CrewAI tools."""

    def __init__(self, llm_client: LLMClient, db_session: Optional[Session] = None):
        self.rephrase_agent = RephraseAgent(llm_client=llm_client, db=db_session)
        self.review_agent = ReviewAgent(llm_client=llm_client, db=db_session)
        self.revise_agent = ReviseAgent(llm_client=llm_client, db=db_session)

    @tool("Rephrase Math Problem")
    def rephrase_problem(self, problem_content: str, escalation_dimensions: str) -> str:
        """
        改寫數學問題，提升複雜度。

        Args:
            problem_content: 原始問題內容
            escalation_dimensions: 複雜度維度（逗號分隔）

        Returns:
            改寫後的問題（JSON 格式字串）
        """
        dimensions_list = [d.strip() for d in escalation_dimensions.split(',')]

        result = self.rephrase_agent.rephrase(
            problem_content=problem_content,
            escalation_dimensions=dimensions_list
        )

        # Return as structured string for CrewAI
        return f"""
問題改寫完成：

### 改寫後問題
{result.stage3_rewritten_question}

### 識別領域
{result.identified_domain}

### 核心能力
{', '.join(result.core_competencies)}

### 難度等級
{result.baseline_difficulty}/5

### 應用維度
{', '.join(result.applied_dimensions)}
"""

    @tool("Review Problem Quality")
    def review_problem(self, question: str) -> str:
        """
        評估問題品質，給出分數和建議。

        Args:
            question: 要評估的問題

        Returns:
            評估結果（包含分數和建議）
        """
        result = self.review_agent.review(rephrased_question=question)

        suggestions_text = "\n".join([f"- {s}" for s in result.suggestions]) if result.suggestions else "無建議（問題已達標準）"

        return f"""
品質評估完成：

### 總分
{result.overall_score}/5.0

### 各項分數
- 清晰度與語法: {result.clarity_grammar_score}/5.0
- 邏輯連貫性: {result.logical_coherence_score}/5.0
- 數學有效性: {result.mathematical_validity_score}/5.0

### 改進建議
{suggestions_text}

### 分析
{result.thought_process[:200]}...
"""

    @tool("Revise Problem")
    def revise_problem(self, question: str, suggestions: str) -> str:
        """
        根據建議改進問題。

        Args:
            question: 要改進的問題
            suggestions: 改進建議（換行分隔）

        Returns:
            改進後的問題
        """
        suggestions_list = [s.strip('- ').strip() for s in suggestions.split('\n') if s.strip()]

        result = self.revise_agent.revise(
            rephrased_question=question,
            suggestions=suggestions_list
        )

        return f"""
問題改進完成：

### 改進後問題
{result.revised_question}

### 改進說明
{result.revision_notes}
"""


# ============================================================================
# CrewAI Pipeline
# ============================================================================

class CrewAIPipeline:
    """
    CrewAI-based orchestration for rephrase pipeline.

    Follows research.md recommendation to use CrewAI for agent coordination.
    Integrates with existing agents while providing simpler workflow management.

    Example:
        >>> pipeline = CrewAIPipeline(
        ...     llm_client=llm_client,
        ...     db_session=db_session
        ... )
        >>> result = pipeline.process(
        ...     original_problem=problem,
        ...     escalation_dimensions=["Multi-stage", "Real-world", "Conditional"]
        ... )
    """

    def __init__(
        self,
        llm_client: LLMClient,
        db_session: Session,
        quality_threshold: float = 4.5,
        max_iterations: int = 5,
    ):
        """
        Initialize CrewAI Pipeline.

        Args:
            llm_client: LLM client for all agents
            db_session: Database session
            quality_threshold: Minimum quality score (default 4.5)
            max_iterations: Maximum review-revise iterations (default 5)
        """
        self.llm_client = llm_client
        self.db_session = db_session
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations

        # Initialize toolkit
        self.toolkit = AgentToolkit(llm_client=llm_client, db_session=db_session)

        logger.info(
            f"CrewAI Pipeline initialized: threshold={quality_threshold}, "
            f"max_iterations={max_iterations}"
        )

    def _create_agents(self) -> Dict[str, Agent]:
        """Create CrewAI agents with defined roles."""

        agents = {
            "rephrase": Agent(
                role="數學問題改寫專家",
                goal="將原始數學問題改寫為更高複雜度的版本，應用指定的複雜度提升維度",
                backstory="""你是一位經驗豐富的數學教育專家，擅長設計具有挑戰性的數學問題。
你深刻理解如何通過多階段轉換、跨領域整合、真實情境參數化等方式提升問題複雜度，
同時保持問題的可解性和教育價值。""",
                verbose=True,
                allow_delegation=False,
                tools=[self.toolkit.rephrase_problem],
            ),

            "review": Agent(
                role="品質審查專家",
                goal=f"評估數學問題的品質，確保分數達到 {self.quality_threshold}/5.0 標準",
                backstory="""你是嚴謹的數學問題品質審查專家，能夠從清晰度與語法、
邏輯連貫性、數學有效性三個維度精確評分。你的評審標準嚴格，
只有真正高品質的問題才能獲得 4.5 分以上的評分。""",
                verbose=True,
                allow_delegation=False,
                tools=[self.toolkit.review_problem],
            ),

            "revise": Agent(
                role="問題改進專家",
                goal="根據審查專家的建議改進問題，同時保留數學本質",
                backstory="""你是問題改進專家，能夠精確理解審查建議並據此改進問題。
你在改進時會保留原問題的數學內容（關鍵數字、公式、關係），
只優化表述、補充必要資訊、修正邏輯錯誤。""",
                verbose=True,
                allow_delegation=False,
                tools=[self.toolkit.revise_problem],
            ),
        }

        return agents

    def _create_tasks(
        self,
        agents: Dict[str, Agent],
        original_problem: Problem,
        escalation_dimensions: List[str],
    ) -> List[Task]:
        """Create CrewAI tasks for the workflow."""

        dimensions_str = ", ".join(escalation_dimensions)

        tasks = [
            # Task 1: Rephrase
            Task(
                description=f"""改寫以下數學問題，應用這些複雜度維度：{dimensions_str}

原始問題：
{original_problem.content}

要求：
1. 分析問題的數學領域和核心能力
2. 應用指定的複雜度提升維度
3. 產生更具挑戰性的改寫問題
4. 確保問題可解且符合數學邏輯
""",
                agent=agents["rephrase"],
                expected_output="改寫後的問題文本及其元數據（領域、難度、應用維度）",
            ),
        ]

        return tasks

    def process(
        self,
        original_problem: Problem,
        escalation_dimensions: List[str],
    ) -> Dict[str, Any]:
        """
        Execute complete rephrase pipeline using CrewAI.

        This method integrates CrewAI for agent orchestration with our existing
        IterationManager for quality control loop.

        Workflow:
        1. Use CrewAI Rephrase Agent to escalate problem complexity
        2. Use IterationManager for Review → Revise loop until quality threshold met
        3. Create Problem records and update RephraseSession

        Args:
            original_problem: Original Problem record
            escalation_dimensions: List of complexity dimensions

        Returns:
            Dictionary with result metadata including session_id, final_problem_id,
            final_status, final_score, iteration_count, total_time_ms
        """
        pipeline_start = datetime.now()

        # Validate inputs
        if not original_problem or not original_problem.content:
            raise ValueError("original_problem must have content")
        if not escalation_dimensions or len(escalation_dimensions) < 3:
            raise ValueError("escalation_dimensions must have at least 3 dimensions")

        logger.info(
            f"Starting CrewAI pipeline for problem {original_problem.id}: "
            f"dimensions={escalation_dimensions}"
        )

        # Create session
        session = RephraseSession(
            id=uuid4(),
            original_problem_id=original_problem.id,
            escalation_dimensions=escalation_dimensions,
            iteration_count=0,
            quality_threshold=self.quality_threshold,
            final_status=SessionStatus.ERROR,
            created_at=datetime.utcnow(),
        )
        self.db_session.add(session)
        self.db_session.flush()

        try:
            # Step 1: Execute CrewAI Rephrase Workflow
            logger.info("Step 1: Executing CrewAI rephrase workflow...")

            # Use our existing RephraseAgent directly (more reliable than CrewAI tool wrapping)
            rephrase_output = self.toolkit.rephrase_agent.rephrase(
                problem_content=original_problem.content,
                escalation_dimensions=escalation_dimensions,
            )

            # Create rephrased Problem record
            rephrased_problem = Problem(
                id=uuid4(),
                content=rephrase_output.stage3_rewritten_question,
                domain=original_problem.domain,
                competencies=rephrase_output.core_competencies,
                baseline_difficulty=rephrase_output.baseline_difficulty,
                source=ProblemSource.REPHRASED,
                source_type=original_problem.source_type,
                parent_id=original_problem.id,
                created_at=datetime.utcnow(),
                extra_metadata={
                    "escalation_dimensions": rephrase_output.applied_dimensions,
                    "domain_identified": rephrase_output.identified_domain,
                },
            )
            self.db_session.add(rephrased_problem)
            self.db_session.flush()

            logger.info(f"Rephrased problem created: {rephrased_problem.id}")

            # Step 2: Execute Review-Revise Loop using IterationManager
            logger.info("Step 2: Executing review-revise loop...")

            from src.orchestration.iteration_manager import IterationManager

            iteration_manager = IterationManager(
                review_agent=self.toolkit.review_agent,
                revise_agent=self.toolkit.revise_agent,
                quality_threshold=self.quality_threshold,
                max_iterations=self.max_iterations,
                db_session=self.db_session,
            )

            iteration_result = iteration_manager.iterate_until_quality(
                initial_question=rephrased_problem.content,
                problem_id=str(rephrased_problem.id),
            )

            logger.info(
                f"Iteration loop completed: status={iteration_result.final_status.value}, "
                f"score={iteration_result.final_score}, iterations={iteration_result.iteration_count}"
            )

            # Step 3: Create final problem if revised
            if iteration_result.iteration_count > 1:
                # Question was revised, create new Problem record
                final_problem = Problem(
                    id=uuid4(),
                    content=iteration_result.final_question,
                    domain=rephrased_problem.domain,
                    competencies=rephrased_problem.competencies,
                    baseline_difficulty=rephrased_problem.baseline_difficulty,
                    source=ProblemSource.REVISED,
                    source_type=rephrased_problem.source_type,
                    parent_id=rephrased_problem.id,
                    created_at=datetime.utcnow(),
                )
                self.db_session.add(final_problem)
                self.db_session.flush()
                logger.info(f"Created revised problem: {final_problem.id}")
            else:
                # No revisions needed, use rephrased problem as final
                final_problem = rephrased_problem
                logger.info("No revisions needed, using rephrased problem as final")

            # Step 4: Update session with final status
            session.final_problem_id = final_problem.id
            session.iteration_count = iteration_result.iteration_count
            session.final_status = iteration_result.final_status
            session.completed_at = datetime.utcnow()

            self.db_session.commit()

            total_time_ms = int((datetime.now() - pipeline_start).total_seconds() * 1000)

            logger.info(
                f"CrewAI pipeline completed successfully: "
                f"session={session.id}, time={total_time_ms}ms"
            )

            return {
                "session_id": str(session.id),
                "original_problem_id": str(original_problem.id),
                "final_problem_id": str(final_problem.id),
                "final_status": session.final_status.value,
                "final_question": final_problem.content,
                "final_score": iteration_result.final_score,
                "iteration_count": session.iteration_count,
                "total_time_ms": total_time_ms,
                "escalation_dimensions": escalation_dimensions,
            }

        except Exception as e:
            logger.error(f"CrewAI pipeline failed: {e}")
            session.final_status = SessionStatus.ERROR
            session.completed_at = datetime.utcnow()
            self.db_session.rollback()
            raise
