# 照片生成题目 - 使用指南

## 功能概述

完整的端到端流程：**上传题目照片 → OCR 文字提取 → 生成多个不同角度的题目**

## 快速开始

### 1. 准备题目照片

支持格式：JPG, JPEG, PNG

示例照片内容：
```
在直角三角形ABC中，∠C=90°，AC=3cm，BC=4cm。
求：
(1) AB的长度
(2) sinA, cosA, tanA的值
```

### 2. 运行完整流程

```bash
python test_full_pipeline.py [照片路径] [难度] [题数]
```

**参数说明：**
- `照片路径`: 题目照片的文件路径
- `难度`: 1-5（1=简单，5=困难）
- `题数`: 1-5（生成的题目数量）

**示例：**

```bash
# 从照片生成 3 题，难度为 3
python test_full_pipeline.py my_math_problem.jpg 3 3

# 从照片生成 2 题，难度为 4
python test_full_pipeline.py triangle_question.png 4 2

# 从照片生成 5 题，难度为 2
python test_full_pipeline.py algebra_problem.jpg 2 5
```

### 3. 查看结果

程序会显示：

1. **OCR 提取结果**
   - 提取的文字内容
   - 信心分数
   - 是否包含图表
   - 处理时间

2. **生成统计**
   - 总生成题数
   - 通过质检题数
   - 最终选择题数

3. **生成的题目**
   - 每题的类型、难度、质量分数
   - 核心概念
   - 题目内容（数学符号已格式化）
   - 评审反馈

4. **输出文件**
   - 结果自动保存到 `output_questions.txt`

## 完整示例

```bash
$ python test_full_pipeline.py test_images/triangle.jpg 3 3

================================================================================
  🚀 完整流程测试：照片 → OCR → 生成题目
================================================================================

📋 配置信息:
   照片路径: test_images/triangle.jpg
   目标难度: 3/5
   题目数量: 3
   最低质量分数: 4.5/5

🔧 初始化系统...
✅ 系统初始化完成

================================================================================
  ⚙️  开始处理
================================================================================

📸 步骤 1/3: OCR 文字提取...
✅ OCR 成功！提取文字長度: 156 字符
   信心分数: 0.95
   包含图表: 否

🤖 步骤 2/3: 生成 3 题（难度 3/5）...
✅ 生成完成！
   总生成: 6 题
   通过质检: 5 题
   最终选择: 3 题

✨ 步骤 3/3: 整理结果...

================================================================================
  📊 结果总览
================================================================================

📸 OCR 提取结果:
   提取文字: 在直角三角形ABC中，∠C=90°，AC=3cm，BC=4cm...
   完整文字长度: 156 字符
   信心分数: 0.95
   包含图表: 否
   处理时间: 1250 ms

🤖 生成统计:
   总生成: 6 题
   通过质检: 5 题
   最终选择: 3 题

================================================================================
  📝 生成的题目
================================================================================

【题目 1】标准多步
难度: 3/5
质量: 4.8/5
核心概念: 幾何

在直角三角形DEF中，∠F=90°，DE=10cm，DF=6cm。
求：
(1) EF的长度
(2) sin D, cos D, tan D的值
(3) 角D的度数（精确到0.1°）

   💬 评审反馈:
      清晰度: 4.8/5
      连贯性: 4.9/5
      有效性: 4.7/5
      建议: 问题清晰，步骤合理，增加了角度计算...

--------------------------------------------------------------------------------

【题目 2】实际应用
难度: 3/5
质量: 4.9/5
核心概念: 幾何

一架梯子斜靠在墙上，梯子长5米，梯子底端距离墙面3米。
求：
(1) 梯子顶端距离地面的高度
(2) 梯子与地面的夹角
(3) 如果要让梯子与地面成60°角，梯子底端应距离墙面多远？

   💬 评审反馈:
      清晰度: 5.0/5
      连贯性: 4.9/5
      有效性: 4.8/5
      建议: 实际应用场景，多步骤推理...

--------------------------------------------------------------------------------

【题目 3】参数变化
难度: 3/5
质量: 4.7/5
核心概念: 幾何

在直角三角形中，一个锐角为α，斜边长为c。
(1) 用α和c表示两条直角边的长度
(2) 若α=30°，c=8cm，求两条直角边的长度
(3) 若一条直角边长度是另一条的2倍，求α的值

   💬 评审反馈:
      清晰度: 4.5/5
      连贯性: 4.8/5
      有效性: 4.8/5
      建议: 参数化表达，从特殊到一般...

--------------------------------------------------------------------------------

💾 结果已保存到: output_questions.txt

================================================================================
  ✨ 测试完成
================================================================================
```

## 工作原理

### 架构流程

```
用户上传照片
    ↓
OCR Pipeline
    ├─ 图片预处理（旋转矫正、降噪、增强对比度）
    ├─ PaddleOCR 文字提取
    └─ GPT-4 Vision 图表分析（如果有图表）
    ↓
提取的题目文字
    ↓
Problem Generator
    ├─ 超额生成变体（N × 2）
    ├─ 批量评审打分
    ├─ 过滤符合条件的题目
    └─ 多样性选择
    ↓
返回 N 个高质量题目
```

### 核心组件

1. **OCRPipeline** (`src/ocr/ocr_pipeline.py`)
   - 图片预处理
   - 文字提取
   - 图表分析

2. **ProblemGenerator** (`src/orchestration/user_driven_generator.py`)
   - 多变体生成
   - 质量评审
   - 智能选择

3. **PhotoToProblemsOrchestrator** (`src/orchestration/photo_to_problems.py`)
   - 整合 OCR 和生成系统
   - 端到端编排

## 高级用法

### 编程方式调用

```python
from src.orchestration.photo_to_problems import process_photo_to_problems

# 简单调用
result = process_photo_to_problems(
    image_path="my_problem.jpg",
    target_difficulty=3,
    num_questions=3
)

if result.success:
    for question in result.questions:
        print(f"难度: {question['difficulty']}/5")
        print(f"质量: {question['score']:.1f}/5")
        print(question['content'])
        print()
```

### 自定义配置

```python
from src.orchestration.photo_to_problems import (
    PhotoToProblemsOrchestrator,
    PhotoToProblemsRequest
)
from src.ocr.ocr_pipeline import OCRPipelineConfig
from src.storage.database import get_db

# 自定义 OCR 配置
ocr_config = OCRPipelineConfig(
    enable_diagram_analysis=True,
    save_to_database=True
)

# 创建编排器
db = next(get_db())
orchestrator = PhotoToProblemsOrchestrator(
    ocr_config=ocr_config,
    db_session=db
)

# 创建请求
request = PhotoToProblemsRequest(
    image_path="problem.jpg",
    target_difficulty=4,
    num_questions=2,
    min_quality_score=4.7,
    difficulty_tolerance=0.3
)

# 执行
result = orchestrator.process(request)
```

## 故障排查

### OCR 提取失败

**问题**: `OCR 未提取到任何文字`

**解决方案**:
1. 检查照片是否清晰
2. 确保文字足够大
3. 避免过度倾斜或旋转
4. 检查 PaddleOCR 是否正确安装

### 生成题目质量不足

**问题**: `通过质检: 0 题`

**解决方案**:
1. 降低 `min_quality_score`（默认 4.5）
2. 增加 `difficulty_tolerance`（默认 0.5）
3. 检查提取的文字是否完整
4. 确保 OPENAI_API_KEY 已配置

### API 调用超时

**问题**: 生成过程中断或超时

**解决方案**:
1. 减少生成题数
2. 检查网络连接
3. 确认 OpenAI API 状态

## 注意事项

1. **照片质量**: 照片越清晰，OCR 提取效果越好
2. **数学符号**: 系统支持 LaTeX 数学符号的识别和格式化
3. **处理时间**: 完整流程可能需要 30-60 秒（取决于题数和网络）
4. **API 成本**: 生成题目会调用 OpenAI API，注意控制调用次数

## 后续优化

- [ ] 支持批量处理多张照片
- [ ] 添加图表识别的深度分析
- [ ] 支持手写题目识别
- [ ] 优化生成速度（批量 LLM 调用）
- [ ] 添加题目库存储和管理
