# 多版本 Rephrase 实现计划

## 快速实现路径（最小改动）

### 方案 1：修改 Rephrase Prompt（最简单）⭐

**不需要改代码**，只需修改 prompt 让它一次生成 3 个版本：

```python
# src/prompts/rephrase_prompt.py

REPHRASE_PROMPT_TEMPLATE = """
请为以下数学问题生成 **3 个不同版本**，每个版本应该：
- 检验相同的数学核心概念
- 使用不同的叙述方式和考法
- 提供不同的难度等级

原始问题：{problem_content}

要求应用的复杂度维度：{escalation_dimensions}

请按以下格式输出 3 个版本：

---VERSION 1: 实际应用场景（难度 2-3/5）---
<将问题转化为真实世界场景>

---VERSION 2: 多步骤推理（难度 3-4/5）---
<需要多个步骤才能解答>

---VERSION 3: 跨领域整合（难度 4/5）---
<结合其他数学知识>

每个版本后面请说明：
- 难度等级：X/5
- 核心概念：<与原题检验的相同概念>
- 差异点：<与原题的主要差异>
"""
```

**然后修改 Parser 解析 3 个版本**

---

### 方案 2：快速原型（2小时实现）

创建新文件 `src/orchestration/multi_variant_pipeline.py`：

```python
class MultiVariantPipeline:
    \"\"\"生成并评估多个问题变体\"\"\"

    def generate_variants(
        self,
        original_problem: Problem,
        num_variants: int = 3
    ) -> List[ProblemVariant]:
        \"\"\"
        一次生成多个变体

        Returns:
            [
                ProblemVariant(content="...", difficulty=2, type="实际应用"),
                ProblemVariant(content="...", difficulty=3, type="多步骤"),
                ProblemVariant(content="...", difficulty=4, type="跨领域"),
            ]
        \"\"\"

    def review_and_rank(
        self,
        variants: List[ProblemVariant]
    ) -> List[Tuple[ProblemVariant, float]]:
        \"\"\"
        评分并排序

        Returns:
            [(variant1, score1), (variant2, score2), ...]
            按分数从高到低排序
        \"\"\"

    def select_best(
        self,
        ranked_variants: List[Tuple[ProblemVariant, float]],
        target_difficulty: int,
        num_select: int = 1
    ) -> List[ProblemVariant]:
        \"\"\"根据难度需求选择最佳版本\"\"\"
```

---

## 推荐实现顺序

### 第一步：Prompt 改进（今天完成）

修改 `src/prompts/rephrase_prompt.py`：

```python
def create_multi_variant_prompt(
    problem_content: str,
    num_variants: int = 3
) -> str:
    \"\"\"
    生成多变体 prompt

    变体类型：
    1. 简化实用版（难度 ↓）
    2. 标准多步版（难度 →）
    3. 挑战整合版（难度 ↑）
    \"\"\"
    return f\"\"\"
你是数学教育专家。请为以下问题生成 {num_variants} 个**不同版本**。

核心要求：
✓ 所有版本检验**相同的数学概念**
✓ 使用**不同的叙述方式**
✓ 提供**不同的难度梯度**
✓ 每个版本都必须数学上有效且可解

原始问题：
{problem_content}

请生成以下版本：

【版本 1：实际应用版】（目标难度：2-3/5）
- 转化为真实世界场景
- 降低抽象程度
- 学生更容易理解

【版本 2：标准进阶版】（目标难度：3/5）
- 需要2-3个推理步骤
- 保持适度挑战
- 适合课堂练习

【版本 3：挑战整合版】（目标难度：4/5）
- 结合多个数学概念
- 需要深入思考
- 适合进阶学习

输出格式：
===VERSION 1===
<问题内容>
难度：X/5
核心概念：<概念描述>

===VERSION 2===
<问题内容>
难度：X/5
核心概念：<概念描述>

===VERSION 3===
<问题内容>
难度：X/5
核心概念：<概念描述>
\"\"\"
```

### 第二步：Parser 适配（30分钟）

修改 `src/parsers/rephrase_parser.py`：

```python
class VariantOutput(BaseModel):
    \"\"\"单个变体\"\"\"
    content: str
    difficulty: int
    core_concept: str
    variant_type: str  # "实际应用"/"标准进阶"/"挑战整合"

class MultiVariantOutput(BaseModel):
    \"\"\"多变体输出\"\"\"
    variants: List[VariantOutput]

class RephraseParser:
    @staticmethod
    def parse_multi_variant(raw_response: str) -> MultiVariantOutput:
        \"\"\"解析多版本输出\"\"\"
        variants = []

        # 正则提取 VERSION 1, 2, 3
        pattern = r'===VERSION (\d+)===(.*?)(?===VERSION|$)'
        matches = re.findall(pattern, raw_response, re.DOTALL)

        for idx, content in matches:
            # 提取难度
            diff_match = re.search(r'难度[:：]\s*(\d)', content)
            difficulty = int(diff_match.group(1)) if diff_match else 3

            # 提取核心概念
            concept_match = re.search(r'核心概念[:：]\s*(.+)', content)
            core_concept = concept_match.group(1).strip() if concept_match else ""

            variants.append(VariantOutput(
                content=content.strip(),
                difficulty=difficulty,
                core_concept=core_concept,
                variant_type=f"版本{idx}"
            ))

        return MultiVariantOutput(variants=variants)
```

### 第三步：Pipeline 集成（1小时）

修改 `test_trigonometry_pipeline.py`：

```python
# 生成多个变体
variants_output = rephrase_agent.rephrase_multi_variant(
    problem_content=original_problem.content,
    num_variants=3
)

# 对每个变体评分
variant_reviews = []
for variant in variants_output.variants:
    review = review_agent.review(variant.content)
    variant_reviews.append((variant, review))

# 选择最佳变体（根据难度需求）
target_difficulty = 3  # 可配置
best_variant = select_variant_by_criteria(
    variant_reviews,
    target_difficulty=target_difficulty,
    min_score=4.0
)

# 如果需要，对选中版本迭代改进
if best_variant.review.overall_score < 4.5:
    improved = iteration_manager.iterate(best_variant)
else:
    final_variant = best_variant

# 保存所有变体（供后续选择）
for variant, review in variant_reviews:
    save_variant_to_db(variant, review)
```

---

## 数据库最小改动

只需在 `Problem` 表添加两个字段：

```python
class Problem(Base):
    # 现有字段...
    variant_group_id = Column(GUID(), nullable=True)  # 同组变体的标识
    variant_type = Column(String(50), nullable=True)   # "实际应用"/"标准进阶"/"挑战整合"
```

---

## 测试计划

```python
# test_multi_variant.py

# 1. 测试生成 3 个版本
variants = pipeline.generate_variants(problem)
assert len(variants) == 3
assert variants[0].difficulty < variants[1].difficulty < variants[2].difficulty

# 2. 测试评分
reviews = pipeline.review_variants(variants)
assert len(reviews) == 3

# 3. 测试筛选
selected = pipeline.select_best(
    variants,
    reviews,
    target_difficulty=3,
    min_score=4.0
)
assert selected.difficulty == 3
assert selected.review_score >= 4.0
```

---

## 时间估算

| 任务 | 时间 | 难度 |
|------|------|------|
| 修改 Rephrase Prompt | 30分钟 | 简单 |
| 修改 Parser | 30分钟 | 简单 |
| 数据库字段添加 | 15分钟 | 简单 |
| Pipeline 集成 | 1小时 | 中等 |
| 测试 | 1小时 | 中等 |
| **总计** | **3-4小时** | |

---

## 你想要的效果

```bash
$ python test_trigonometry_pipeline.py

📝 测试 1/5: 基础：三角函数值
================================================================================

⏳ 生成多个变体...

✅ 生成了 3 个变体：

【变体 1】实际应用版（难度 2/5）
   在一个建筑工地中，工人需要...
   评分：4.2/5.0

【变体 2】标准进阶版（难度 3/5）
   已知直角三角形的斜边和一条直角边，求...
   评分：4.6/5.0 ⭐

【变体 3】挑战整合版（难度 4/5）
   结合向量和三角函数，在坐标系中...
   评分：4.3/5.0

🎯 根据目标难度 (3/5)，选择：变体 2
   最终评分：4.6/5.0
   无需迭代改进

💾 所有 3 个变体已保存到数据库
```

---

## 下一步行动

1. **今天可以做**：修改 Prompt 和 Parser（1小时）
2. **本周可以做**：完整实现 MVP（3-4小时）
3. **下周优化**：增加更多变体类型、改进筛选算法

**我可以立即开始实现，你要我现在开始吗？** 🚀
