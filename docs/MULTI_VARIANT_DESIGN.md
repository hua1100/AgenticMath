"""
多版本 Rephrase Pipeline 设计文档

基于用户洞察：改写的目标是多元化，而非单纯提高难度。

## 核心理念

1. **多样性优先**：一次生成多个不同版本
2. **用户选择**：根据需求筛选合适版本
3. **概念一致**：所有版本检验同一数学概念

## 新架构流程

```
原始问题
    ↓
RephraseAgent (批量生成模式)
    ├─ 变体 1：实际应用场景化
    ├─ 变体 2：逆向问题设计
    ├─ 变体 3：多步骤推理
    ├─ 变体 4：跨领域整合
    └─ 变体 5：条件分支
    ↓
ReviewAgent (批量评分)
    评估每个变体的：
    - 清晰度
    - 数学有效性
    - 难度等级（客观评估）
    - 多样性得分（与其他版本的差异度）
    ↓
筛选器（根据需求）
    用户指定：
    - 目标难度范围（如 2-3/5）
    - 最低清晰度（如 >= 4.0）
    - 最低数学有效性（如 >= 4.5）
    - 需要的版本数量（如 3个）
    ↓
（可选）迭代改进
    对筛选出的版本进行 Review-Revise 循环
    ↓
输出：多个优质版本
```

## 数据结构变化

### 当前：
```python
Problem
├─ id: UUID
├─ content: str (单一版本)
├─ difficulty: int
└─ parent_id: UUID (单链)
```

### 新设计：
```python
Problem
├─ id: UUID
├─ content: str
├─ difficulty: int
├─ parent_id: UUID
└─ variant_group_id: UUID (新增！关联同一组变体)

VariantGroup
├─ id: UUID
├─ original_problem_id: UUID
├─ generation_strategy: str
└─ created_at: datetime

ProblemVariant (关联表)
├─ variant_group_id: UUID
├─ problem_id: UUID
├─ variant_type: str (实际应用/逆向/多步骤/跨领域/条件)
├─ diversity_score: float (与其他变体的差异度)
└─ rank: int (质量排名)
```

## RephraseAgent 接口变化

### 当前：
```python
def rephrase(
    problem_content: str,
    escalation_dimensions: List[str]
) -> RephraseAgentOutput:
    # 返回单一版本
```

### 新接口：
```python
def rephrase_variants(
    problem_content: str,
    escalation_dimensions: List[str],
    num_variants: int = 5,
    diversity_weight: float = 0.3  # 多样性权重
) -> List[RephraseVariantOutput]:
    # 返回多个版本

class RephraseVariantOutput:
    variant_question: str
    variant_type: str  # "实际应用"/"逆向"/"多步骤"等
    applied_dimensions: List[str]
    estimated_difficulty: int  # 1-5
    core_concept: str  # 检验的核心概念
    differences_from_original: str  # 与原题的差异说明
```

## Prompt 变化

### 当前 Prompt：
```
请将以下问题改写得更复杂...
应用这些维度：Multi-stage, Cross-domain, Real-world
```

### 新 Prompt：
```
请为以下问题生成 5 个不同的变体，每个变体应该：

1. 检验相同的数学核心概念
2. 使用不同的叙述方式和考法
3. 提供不同的难度等级（2-4/5）

变体类型要求：
- 变体 1：实际应用场景化（难度 2/5）
  将抽象问题转化为真实世界场景

- 变体 2：逆向问题设计（难度 3/5）
  已知结果，求初始条件或过程

- 变体 3：多步骤推理（难度 3-4/5）
  需要多个中间步骤才能得出答案

- 变体 4：跨领域整合（难度 4/5）
  结合其他数学领域的知识

- 变体 5：条件分支（难度 3/5）
  根据不同条件有不同的解法

每个变体必须：
✓ 数学上有效且可解
✓ 与其他变体有明显差异
✓ 保持数学概念一致
✓ 清晰且无歧义
```

## ReviewAgent 接口变化

### 当前：
```python
def review(question: str) -> ReviewAgentOutput:
    # 单一评分
```

### 新接口：
```python
def review_variants(
    variants: List[str],
    original_question: str
) -> List[VariantReviewOutput]:
    # 批量评分

class VariantReviewOutput:
    variant_index: int
    clarity_score: float
    mathematical_validity_score: float
    estimated_difficulty: int  # 客观评估
    diversity_score: float  # 与原题的差异度
    concept_consistency_score: float  # 概念一致性
    overall_score: float
    strengths: List[str]  # 优点
    concerns: List[str]  # 问题点
```

## 筛选器设计

```python
class VariantSelector:
    def select(
        self,
        variants: List[Problem],
        reviews: List[VariantReviewOutput],
        criteria: SelectionCriteria
    ) -> List[Problem]:
        \"\"\"
        根据标准筛选变体

        Args:
            variants: 所有变体
            reviews: 对应的评分
            criteria: 筛选标准

        Returns:
            筛选后的变体列表（按质量排序）
        \"\"\"

class SelectionCriteria:
    target_difficulty_range: Tuple[int, int] = (2, 4)
    min_clarity: float = 4.0
    min_math_validity: float = 4.5
    min_diversity: float = 0.3  # 与原题至少30%不同
    max_variants: int = 3
    prefer_variant_types: List[str] = []  # 优先的变体类型
```

## 使用示例

```python
# 1. 生成多个变体
variants = rephrase_agent.rephrase_variants(
    problem_content="求 sin 75° 的精确值",
    escalation_dimensions=["Multi-stage", "Real-world", "Inverse"],
    num_variants=5
)

# 2. 批量评分
reviews = review_agent.review_variants(
    variants=[v.variant_question for v in variants],
    original_question="求 sin 75° 的精确值"
)

# 3. 根据需求筛选
criteria = SelectionCriteria(
    target_difficulty_range=(2, 3),  # 中等难度
    min_clarity=4.0,
    max_variants=3
)
selected = selector.select(variants, reviews, criteria)

# 4. （可选）对选中版本迭代改进
for variant in selected:
    if variant.review_score < 4.5:
        improved = iteration_manager.iterate_until_quality(variant)

# 5. 输出多个优质版本
return selected  # 返回 3 个不同难度、不同考法的优质版本
```

## 优势分析

### 教育价值
- ✅ 学生可以从不同角度理解同一概念
- ✅ 教师可以根据学生水平选择合适难度
- ✅ 题库更加丰富多元

### 技术优势
- ✅ 一次 LLM 调用生成多个版本（成本更低）
- ✅ 通过比较选择最优（质量更高）
- ✅ 支持批量生成题库

### 产品优势
- ✅ 灵活性：用户可以选择
- ✅ 多样性：同一概念多种考法
- ✅ 可扩展：容易添加新的变体类型

## 实现优先级

### Phase 1: MVP（最小可行产品）
1. 修改 RephraseAgent 生成 3 个固定变体
   - 简单版（难度 2）
   - 中等版（难度 3）
   - 困难版（难度 4）
2. ReviewAgent 批量评分
3. 简单的筛选器（根据难度范围选择）

### Phase 2: 完整功能
1. 支持 5 种变体类型
2. 多样性评分算法
3. 高级筛选器（多维度标准）
4. 变体组管理（数据库）

### Phase 3: 优化
1. 用户偏好学习
2. 自动推荐最佳变体
3. 变体质量排名算法

## 注意事项

1. **概念一致性检查**
   - 必须确保所有变体检验同一数学概念
   - Review 时增加 "concept_consistency_score"

2. **多样性度量**
   - 使用文本相似度（如 cosine similarity）
   - 考虑问题结构的差异
   - 避免生成过于相似的变体

3. **性能优化**
   - 批量调用 LLM（减少网络开销）
   - 并行评分（加速处理）
   - 缓存相似问题的变体

## 总结

这个设计完全改变了"改写"的定义：

**从**："把问题改得更难"
**到**："为同一概念生成多元化的考法"

这更符合教育的本质：**用不同方式检验学生是否真正理解概念**。
"""
