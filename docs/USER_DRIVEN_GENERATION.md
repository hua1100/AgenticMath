# 用户需求驱动的多题目生成系统

## 核心理念（修正版）

**目标**：根据用户需求（难度+题数），生成多个高质量、不同角度的题目

**策略**：超额生成 + 严格筛选 = 保证质量

---

## 用户流程

```python
# 第一步：用户指定需求
request = UserRequest(
    original_problem="求 sin 75° 的精确值",
    target_difficulty=3,        # 难度 1-5
    num_questions=3,            # 需要 3 题
    difficulty_tolerance=0.5,   # 难度容差 ±0.5
    min_quality_score=4.5       # 最低质量门槛
)

# 第二步：系统生成题目
generator = ProblemGenerator()
result = generator.generate(request)

# 第三步：用户获得结果
for i, problem in enumerate(result.questions, 1):
    print(f"题目 {i}:")
    print(f"  内容: {problem.content}")
    print(f"  难度: {problem.difficulty}/5")
    print(f"  质量: {problem.score}/5")
    print(f"  类型: {problem.variant_type}")
```

---

## 系统处理流程

```
用户需求：难度 3，数量 3 题
    ↓
【阶段 1】超额生成（生成 N × 1.5-2 倍）
    生成 6-8 个不同变体：
    ├─ 实际应用版（难度 2-3）
    ├─ 标准多步版（难度 3）
    ├─ 逆向设计版（难度 3-4）
    ├─ 跨领域版（难度 4）
    ├─ 条件分支版（难度 3）
    └─ ... 更多变体
    ↓
【阶段 2】质量检查（Review Agent 批量评分）
    变体 1: 难度 2.5, 质量 4.3 ❌ (低于 4.5)
    变体 2: 难度 3.0, 质量 4.7 ✅
    变体 3: 难度 3.5, 质量 4.6 ✅
    变体 4: 难度 4.0, 质量 4.8 ❌ (难度不匹配)
    变体 5: 难度 3.2, 质量 4.5 ✅
    变体 6: 难度 3.0, 质量 4.9 ✅
    ...
    ↓
【阶段 3】筛选过滤
    条件 1: 质量 >= 4.5 → 剩余 5 个
    条件 2: 难度 3 ± 0.5 (2.5-3.5) → 剩余 4 个
    ↓
【阶段 4】多样性选择
    从 4 个合格题目中选 3 个，确保：
    ✓ 类型不重复（实际/多步/逆向各选一个）
    ✓ 叙述方式有差异（避免相似度 > 70%）
    ✓ 优先选择高分题目
    ↓
【阶段 5】不足处理（如果合格题目 < 需求数量）
    对低分或不匹配的题目进入迭代：
    Review → Revise → Review
    直到达标或最大迭代次数
    ↓
【输出】3 个高质量、多样化的题目
```

---

## 核心组件设计

### 1. UserRequest（用户需求）

```python
class UserRequest(BaseModel):
    """用户请求"""
    original_problem: str
    target_difficulty: int = Field(ge=1, le=5)
    num_questions: int = Field(ge=1, le=5)
    difficulty_tolerance: float = 0.5
    min_quality_score: float = 4.5
    variant_types: Optional[List[str]] = None  # 指定变体类型
```

### 2. ProblemGenerator（题目生成器）

```python
class ProblemGenerator:
    def generate(self, request: UserRequest) -> GenerationResult:
        """
        根据用户需求生成题目

        流程：
        1. 计算生成数量 = request.num_questions × 2
        2. 调用 RephraseAgent 批量生成
        3. 调用 ReviewAgent 批量评分
        4. 筛选符合条件的题目
        5. 多样性选择
        6. 不足则迭代改进
        """

        # 1. 超额生成
        num_to_generate = request.num_questions * 2
        variants = self.rephrase_agent.generate_variants(
            problem=request.original_problem,
            num_variants=num_to_generate,
            target_difficulty=request.target_difficulty
        )

        # 2. 批量评分
        reviews = self.review_agent.batch_review(variants)

        # 3. 筛选
        qualified = self._filter_qualified(
            variants,
            reviews,
            request
        )

        # 4. 多样性选择
        if len(qualified) >= request.num_questions:
            selected = self._select_diverse(
                qualified,
                request.num_questions
            )
        else:
            # 5. 不足则迭代改进
            selected = self._improve_until_enough(
                qualified,
                request
            )

        return GenerationResult(
            questions=selected,
            total_generated=len(variants),
            passed_quality=len(qualified),
            selected=len(selected)
        )
```

### 3. 筛选器（Filter）

```python
def _filter_qualified(
    self,
    variants: List[ProblemVariant],
    reviews: List[ReviewOutput],
    request: UserRequest
) -> List[QualifiedProblem]:
    """筛选合格题目"""

    qualified = []

    for variant, review in zip(variants, reviews):
        # 条件 1: 质量门槛
        if review.overall_score < request.min_quality_score:
            continue

        # 条件 2: 难度匹配
        diff_lower = request.target_difficulty - request.difficulty_tolerance
        diff_upper = request.target_difficulty + request.difficulty_tolerance
        if not (diff_lower <= variant.difficulty <= diff_upper):
            continue

        # 通过所有条件
        qualified.append(QualifiedProblem(
            variant=variant,
            review=review,
            score=review.overall_score,
            difficulty=variant.difficulty
        ))

    # 按质量分数排序
    qualified.sort(key=lambda x: x.score, reverse=True)

    return qualified
```

### 4. 多样性选择器

```python
def _select_diverse(
    self,
    qualified: List[QualifiedProblem],
    num_select: int
) -> List[QualifiedProblem]:
    """
    从合格题目中选择多样化的题目

    策略：
    1. 优先选择不同类型的题目
    2. 避免内容相似度过高（> 70%）
    3. 在满足多样性的前提下选择高分题目
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

    # 第二轮：如果还不够，选择内容差异大的
    if len(selected) < num_select:
        for problem in qualified:
            if problem in selected:
                continue

            # 检查与已选题目的相似度
            if self._is_diverse_enough(problem, selected):
                selected.append(problem)

                if len(selected) >= num_select:
                    break

    return selected[:num_select]

def _is_diverse_enough(
    self,
    candidate: QualifiedProblem,
    selected: List[QualifiedProblem],
    similarity_threshold: float = 0.7
) -> bool:
    """检查候选题目是否与已选题目足够不同"""

    for existing in selected:
        similarity = self._calculate_similarity(
            candidate.variant.content,
            existing.variant.content
        )

        if similarity > similarity_threshold:
            return False  # 太相似

    return True  # 足够不同
```

### 5. 迭代改进（不足时）

```python
def _improve_until_enough(
    self,
    qualified: List[QualifiedProblem],
    request: UserRequest
) -> List[QualifiedProblem]:
    """
    当合格题目不足时，对低分题目迭代改进

    策略：
    1. 从未达标的题目中选择最接近目标的
    2. 进入 Review-Revise 循环
    3. 直到达标或达到最大迭代次数
    """

    selected = qualified.copy()
    need_more = request.num_questions - len(qualified)

    # 获取所有未达标的题目
    all_variants = self.all_generated_variants
    unqualified = [
        v for v in all_variants
        if v not in [q.variant for q in qualified]
    ]

    # 按"接近度"排序（难度最接近 + 分数最高）
    unqualified.sort(
        key=lambda v: (
            abs(v.difficulty - request.target_difficulty),  # 难度接近度
            -v.review_score  # 分数（降序）
        )
    )

    # 对最有潜力的题目迭代改进
    for variant in unqualified[:need_more * 2]:  # 尝试 2 倍数量
        improved = self.iteration_manager.iterate_until_quality(
            variant.content,
            target_score=request.min_quality_score,
            max_iterations=3
        )

        if improved.final_score >= request.min_quality_score:
            selected.append(QualifiedProblem(
                variant=improved,
                score=improved.final_score
            ))

            if len(selected) >= request.num_questions:
                break

    return selected[:request.num_questions]
```

---

## 数据结构

```python
class ProblemVariant(BaseModel):
    """单个变体"""
    content: str
    difficulty: int
    variant_type: str  # "实际应用"/"多步骤"/"逆向"等
    core_concept: str
    review_score: float = 0.0

class QualifiedProblem(BaseModel):
    """合格的题目"""
    variant: ProblemVariant
    review: ReviewOutput
    score: float
    difficulty: int

class GenerationResult(BaseModel):
    """生成结果"""
    questions: List[QualifiedProblem]
    total_generated: int
    passed_quality: int
    selected: int
    metadata: Dict[str, Any] = {}
```

---

## 使用示例

```python
# 创建生成器
generator = ProblemGenerator(
    rephrase_agent=rephrase_agent,
    review_agent=review_agent,
    iteration_manager=iteration_manager
)

# 用户请求
request = UserRequest(
    original_problem="在直角三角形ABC中，角C为直角，AB=10，BC=6，求sinA",
    target_difficulty=3,        # 中等难度
    num_questions=3,            # 需要 3 题
    min_quality_score=4.5       # 质量门槛
)

# 生成题目
result = generator.generate(request)

# 显示结果
print(f"✅ 生成了 {result.total_generated} 个候选题目")
print(f"✅ {result.passed_quality} 个达到质量标准")
print(f"✅ 选出 {result.selected} 个最优题目：\n")

for i, problem in enumerate(result.questions, 1):
    print(f"【题目 {i}】{problem.variant.variant_type}")
    print(f"难度: {problem.difficulty}/5")
    print(f"质量: {problem.score:.1f}/5")
    print(f"内容: {problem.variant.content}")
    print()
```

---

## 输出示例

```
✅ 生成了 6 个候选题目
✅ 4 个达到质量标准
✅ 选出 3 个最优题目：

【题目 1】实际应用
难度: 3/5
质量: 4.7/5
内容: 在一个建筑工地中，工人需要搭建一个支撑架...

【题目 2】多步骤推理
难度: 3/5
质量: 4.9/5
内容: 已知直角三角形的斜边长度为10公分，一条直角边长度为6公分...

【题目 3】逆向设计
难度: 3/5
质量: 4.6/5
内容: 若 sinA = 0.8，且 A 为直角三角形的一个锐角...
```

---

## 关键优势

1. **用户驱动**：完全根据用户需求（难度+题数）
2. **质量保证**：所有输出题目 >= 最低质量标准
3. **多样性**：不同角度考察同一概念
4. **灵活性**：1-5 题可选
5. **高效性**：超额生成+筛选，比迭代改进快

---

## 下一步实现

优先级：
1. **Phase 1**（本周）：基础生成 + 筛选
2. **Phase 2**（下周）：多样性选择 + 迭代补足
3. **Phase 3**（未来）：用户偏好学习 + 智能推荐
"""
