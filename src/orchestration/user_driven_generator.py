"""
用户需求驱动的题目生成器

根据用户指定的难度和题数，生成多个高质量、不同角度的题目。
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field

from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from src.orchestration.iteration_manager import IterationManager


@dataclass
class UserRequest:
    """用户请求"""
    original_problem: str
    target_difficulty: int  # 1-5
    num_questions: int  # 1-5
    difficulty_tolerance: float = 0.5
    min_quality_score: float = 4.5
    variant_types: List[str] = None  # 可选：指定变体类型


@dataclass
class ProblemVariant:
    """问题变体"""
    content: str
    difficulty: int
    variant_type: str
    core_concept: str
    review_score: float = 0.0


@dataclass
class QualifiedProblem:
    """合格的题目"""
    variant: ProblemVariant
    score: float
    difficulty: int
    review_details: Dict[str, Any]


class GenerationResult(BaseModel):
    """生成结果"""
    questions: List[Dict[str, Any]]
    total_generated: int
    passed_quality: int
    selected: int
    metadata: Dict[str, Any] = {}


class ProblemGenerator:
    """
    题目生成器

    功能：
    1. 根据用户需求超额生成变体（N × 1.5-2）
    2. 批量评分
    3. 筛选符合条件的题目
    4. 多样性选择
    5. 不足时迭代改进
    """

    def __init__(
        self,
        rephrase_agent: RephraseAgent,
        review_agent: ReviewAgent,
        iteration_manager: IterationManager = None
    ):
        self.rephrase_agent = rephrase_agent
        self.review_agent = review_agent
        self.iteration_manager = iteration_manager

    def generate(self, request: UserRequest) -> GenerationResult:
        """
        生成题目

        Args:
            request: 用户请求

        Returns:
            GenerationResult 包含选中的题目
        """

        # 第一阶段：超额生成
        num_to_generate = request.num_questions * 2
        print(f"\n🔄 生成 {num_to_generate} 个候选题目...")

        variants = self._generate_variants(
            request.original_problem,
            num_to_generate,
            request.target_difficulty
        )

        print(f"✅ 生成了 {len(variants)} 个变体")

        # 第二阶段：批量评分
        print(f"\n📊 批量评分...")
        variants_with_scores = self._batch_review(variants)

        # 第三阶段：筛选
        print(f"\n🔍 筛选合格题目...")
        qualified = self._filter_qualified(
            variants_with_scores,
            request
        )

        print(f"✅ {len(qualified)} 个题目达到标准")

        # 第四阶段：多样性选择
        if len(qualified) >= request.num_questions:
            print(f"\n🎯 从 {len(qualified)} 个合格题目中选择 {request.num_questions} 个...")
            selected = self._select_diverse(
                qualified,
                request.num_questions
            )
        else:
            # 第五阶段：不足则补充（迭代或警告）
            print(f"\n⚠️  合格题目不足（{len(qualified)}/{request.num_questions}）")
            selected = qualified

            if self.iteration_manager:
                print(f"🔄 尝试改进低分题目...")
                # TODO: 实现迭代改进逻辑
            else:
                print(f"ℹ️  返回所有合格题目")

        # 构建结果
        result = GenerationResult(
            questions=[self._to_dict(q) for q in selected],
            total_generated=len(variants),
            passed_quality=len(qualified),
            selected=len(selected),
            metadata={
                "request": {
                    "target_difficulty": request.target_difficulty,
                    "num_questions": request.num_questions,
                    "min_quality_score": request.min_quality_score
                }
            }
        )

        print(f"\n✅ 选出 {len(selected)} 个优质题目")

        return result

    def _generate_variants(
        self,
        problem: str,
        num_variants: int,
        target_difficulty: int
    ) -> List[ProblemVariant]:
        """
        生成多个变体

        当前简化实现：调用 RephraseAgent num_variants 次
        TODO: 修改为批量生成
        """
        variants = []

        # 定义变体类型
        variant_types = [
            ("实际应用", target_difficulty - 1),
            ("标准多步", target_difficulty),
            ("逆向设计", target_difficulty),
            ("跨领域", target_difficulty + 1),
            ("条件分支", target_difficulty),
        ]

        for i in range(num_variants):
            # 循环使用变体类型
            v_type, diff = variant_types[i % len(variant_types)]

            # 调用 RephraseAgent
            # TODO: 修改 prompt 让它生成特定类型的变体
            try:
                result = self.rephrase_agent.rephrase(
                    problem_content=problem,
                    escalation_dimensions=[
                        "Multi-stage Transformation",
                        "Real-world Parameterization",
                        "Conditional Branching"
                    ]
                )

                variants.append(ProblemVariant(
                    content=result.stage3_rewritten_question,
                    difficulty=diff if 1 <= diff <= 5 else target_difficulty,
                    variant_type=v_type,
                    core_concept=result.identified_domain
                ))
            except Exception as e:
                print(f"⚠️  生成变体 {i+1} 失败: {e}")
                continue

        return variants

    def _batch_review(
        self,
        variants: List[ProblemVariant]
    ) -> List[ProblemVariant]:
        """
        批量评分

        TODO: 优化为真正的批量调用
        """
        for variant in variants:
            try:
                review = self.review_agent.review(variant.content)
                variant.review_score = review.overall_score
            except Exception as e:
                print(f"⚠️  评分失败: {e}")
                variant.review_score = 0.0

        return variants

    def _filter_qualified(
        self,
        variants: List[ProblemVariant],
        request: UserRequest
    ) -> List[QualifiedProblem]:
        """筛选合格题目"""

        qualified = []

        diff_lower = request.target_difficulty - request.difficulty_tolerance
        diff_upper = request.target_difficulty + request.difficulty_tolerance

        for variant in variants:
            # 条件 1: 质量门槛
            if variant.review_score < request.min_quality_score:
                continue

            # 条件 2: 难度匹配
            if not (diff_lower <= variant.difficulty <= diff_upper):
                continue

            qualified.append(QualifiedProblem(
                variant=variant,
                score=variant.review_score,
                difficulty=variant.difficulty,
                review_details={}
            ))

        # 按分数排序
        qualified.sort(key=lambda x: x.score, reverse=True)

        return qualified

    def _select_diverse(
        self,
        qualified: List[QualifiedProblem],
        num_select: int
    ) -> List[QualifiedProblem]:
        """
        多样性选择

        策略：
        1. 优先选择不同类型
        2. 避免相似度过高
        3. 分数优先
        """

        selected = []
        used_types = set()

        # 第一轮：每种类型选一个最高分的
        for problem in qualified:
            if problem.variant.variant_type not in used_types:
                selected.append(problem)
                used_types.add(problem.variant.variant_type)

                if len(selected) >= num_select:
                    break

        # 第二轮：如果还不够，直接按分数选
        if len(selected) < num_select:
            for problem in qualified:
                if problem not in selected:
                    selected.append(problem)

                    if len(selected) >= num_select:
                        break

        return selected[:num_select]

    def _to_dict(self, problem: QualifiedProblem) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": problem.variant.content,
            "difficulty": problem.difficulty,
            "quality_score": problem.score,
            "variant_type": problem.variant.variant_type,
            "core_concept": problem.variant.core_concept
        }


# 使用示例
if __name__ == "__main__":
    """
    使用示例

    注意：这需要实际的 agent 实例，这里仅作演示
    """

    # 假设已有 agents
    # rephrase_agent = RephraseAgent(...)
    # review_agent = ReviewAgent(...)

    # 创建生成器
    # generator = ProblemGenerator(
    #     rephrase_agent=rephrase_agent,
    #     review_agent=review_agent
    # )

    # 用户请求
    # request = UserRequest(
    #     original_problem="求 sin 75° 的精确值",
    #     target_difficulty=3,
    #     num_questions=3,
    #     min_quality_score=4.5
    # )

    # 生成题目
    # result = generator.generate(request)

    # 显示结果
    # for i, q in enumerate(result.questions, 1):
    #     print(f"\n【题目 {i}】")
    #     print(f"类型: {q['variant_type']}")
    #     print(f"难度: {q['difficulty']}/5")
    #     print(f"质量: {q['quality_score']:.1f}/5")
    #     print(f"内容: {q['content'][:100]}...")

    print("请查看 docs/USER_DRIVEN_GENERATION.md 了解完整设计")
