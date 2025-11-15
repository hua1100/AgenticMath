"""
照片到题目生成的完整工作流程

此模块整合了以下流程：
1. 照片上传
2. OCR 文字提取
3. 用户指定难度和题数
4. 生成多个高质量题目
5. 返回结果
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from dataclasses import dataclass
from sqlalchemy.orm import Session

from src.ocr.ocr_pipeline import OCRPipeline, OCRPipelineConfig
from src.orchestration.user_driven_generator import (
    ProblemGenerator,
    UserRequest,
    GenerationResult
)
from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from src.orchestration.iteration_manager import IterationManager
from src.agents.llm_client import LLMClient


@dataclass
class PhotoToProblemsRequest:
    """照片到题目生成的请求"""
    image_path: str | Path
    target_difficulty: int  # 1-5
    num_questions: int  # 1-5
    min_quality_score: float = 4.5
    difficulty_tolerance: float = 0.5
    image_id: Optional[str | UUID] = None


@dataclass
class PhotoToProblemsResult:
    """照片到题目生成的结果"""
    success: bool
    ocr_result: Dict[str, Any]
    generation_result: Optional[GenerationResult]
    error_message: Optional[str] = None

    @property
    def extracted_text(self) -> str:
        """获取提取的文字"""
        return self.ocr_result.get("extracted_text", "")

    @property
    def questions(self) -> List[Dict[str, Any]]:
        """获取生成的题目列表"""
        if self.generation_result:
            return self.generation_result.questions
        return []

    @property
    def metadata(self) -> Dict[str, Any]:
        """获取完整元数据"""
        return {
            "ocr": {
                "confidence_score": self.ocr_result.get("confidence_score", 0.0),
                "contains_diagram": self.ocr_result.get("contains_diagram", False),
                "processing_time_ms": self.ocr_result.get("processing_time_ms", 0)
            },
            "generation": self.generation_result.metadata if self.generation_result else {}
        }


class PhotoToProblemsOrchestrator:
    """
    照片到题目生成的编排器

    完整流程：
    1. 使用 OCR Pipeline 提取照片中的题目文字
    2. 使用 ProblemGenerator 生成多个不同角度的题目
    3. 返回符合用户要求的高质量题目
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        ocr_config: Optional[OCRPipelineConfig] = None,
        db_session: Optional[Session] = None
    ):
        """
        初始化编排器

        Args:
            llm_client: LLM 客户端（用于 Rephrase 和 Review Agent）
            ocr_config: OCR 配置
            db_session: 数据库会话（可选）
        """
        self.llm_client = llm_client or LLMClient()
        self.ocr_pipeline = OCRPipeline(config=ocr_config)
        self.db_session = db_session

        # 初始化 Agents
        self.rephrase_agent = RephraseAgent(
            llm_client=self.llm_client,
            db=db_session
        )
        self.review_agent = ReviewAgent(
            llm_client=self.llm_client,
            db=db_session
        )

        # 需要 ReviseAgent 來進行迭代改進
        from src.agents.revise_agent import ReviseAgent
        self.revise_agent = ReviseAgent(
            llm_client=self.llm_client,
            db=db_session
        )

        # 初始化 IterationManager（傳入必要的 agents）
        self.iteration_manager = IterationManager(
            review_agent=self.review_agent,
            revise_agent=self.revise_agent,
            quality_threshold=4.5,  # 默認質量門檻
            max_iterations=3,  # 最多迭代 3 次
            db_session=db_session
        )

        # 初始化生成器
        self.problem_generator = ProblemGenerator(
            rephrase_agent=self.rephrase_agent,
            review_agent=self.review_agent,
            iteration_manager=self.iteration_manager
        )

    def process(self, request: PhotoToProblemsRequest) -> PhotoToProblemsResult:
        """
        处理完整流程：照片 → OCR → 生成题目

        Args:
            request: 包含照片路径和生成参数的请求

        Returns:
            PhotoToProblemsResult: 包含 OCR 结果和生成的题目
        """
        # Step 1: OCR 提取文字
        print("📸 步骤 1/3: OCR 文字提取...")
        image_id = request.image_id or str(uuid4())

        ocr_result = self.ocr_pipeline.process(
            image_id=image_id,
            file_path=request.image_path,
            db=self.db_session
        )

        # 检查 OCR 是否成功
        if not ocr_result.get("success", False):
            return PhotoToProblemsResult(
                success=False,
                ocr_result=ocr_result,
                generation_result=None,
                error_message=f"OCR 失败: {ocr_result.get('error_message', 'Unknown error')}"
            )

        extracted_text = ocr_result.get("extracted_text", "")
        if not extracted_text.strip():
            return PhotoToProblemsResult(
                success=False,
                ocr_result=ocr_result,
                generation_result=None,
                error_message="OCR 未提取到任何文字"
            )

        print(f"✅ OCR 成功！提取文字長度: {len(extracted_text)} 字符")
        print(f"   信心分数: {ocr_result.get('confidence_score', 0):.2f}")
        print(f"   包含图表: {'是' if ocr_result.get('contains_diagram') else '否'}")

        # Step 2: 生成题目
        print(f"\n🤖 步骤 2/3: 生成 {request.num_questions} 题（难度 {request.target_difficulty}/5）...")

        user_request = UserRequest(
            original_problem=extracted_text,
            target_difficulty=request.target_difficulty,
            num_questions=request.num_questions,
            min_quality_score=request.min_quality_score,
            difficulty_tolerance=request.difficulty_tolerance
        )

        try:
            generation_result = self.problem_generator.generate(user_request)

            print(f"✅ 生成完成！")
            print(f"   总生成: {generation_result.total_generated} 题")
            print(f"   通过质检: {generation_result.passed_quality} 题")
            print(f"   最终选择: {generation_result.selected} 题")

            # Step 3: 返回结果
            print("\n✨ 步骤 3/3: 整理结果...")

            return PhotoToProblemsResult(
                success=True,
                ocr_result=ocr_result,
                generation_result=generation_result,
                error_message=None
            )

        except Exception as e:
            return PhotoToProblemsResult(
                success=False,
                ocr_result=ocr_result,
                generation_result=None,
                error_message=f"题目生成失败: {str(e)}"
            )


# 便捷函数
def process_photo_to_problems(
    image_path: str | Path,
    target_difficulty: int,
    num_questions: int,
    min_quality_score: float = 4.5,
    llm_client: Optional[LLMClient] = None,
    db_session: Optional[Session] = None
) -> PhotoToProblemsResult:
    """
    便捷函数：从照片生成题目

    Args:
        image_path: 照片路径
        target_difficulty: 目标难度 (1-5)
        num_questions: 题目数量 (1-5)
        min_quality_score: 最低质量分数 (默认 4.5)
        llm_client: LLM 客户端（可选）
        db_session: 数据库会话（可选）

    Returns:
        PhotoToProblemsResult: 包含提取的题目

    Example:
        >>> result = process_photo_to_problems(
        ...     image_path="test_images/triangle.jpg",
        ...     target_difficulty=3,
        ...     num_questions=3
        ... )
        >>> if result.success:
        ...     for q in result.questions:
        ...         print(q['content'])
    """
    orchestrator = PhotoToProblemsOrchestrator(
        llm_client=llm_client,
        db_session=db_session
    )

    request = PhotoToProblemsRequest(
        image_path=image_path,
        target_difficulty=target_difficulty,
        num_questions=num_questions,
        min_quality_score=min_quality_score
    )

    return orchestrator.process(request)
