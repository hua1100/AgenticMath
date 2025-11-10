#!/usr/bin/env python3
"""
测试 Rephrase Parser 的中英文支持

验证 Parser 能否正确提取繁体中文格式的领域和核心能力。
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.parsers.rephrase_parser import RephraseParser

print("=" * 70)
print("🧪 测试 Rephrase Parser 中英文支持")
print("=" * 70)

# 模拟 LLM 的繁体中文输出
test_response = """
Stage 1 #Problem Deconstruction#:
- 領域識別：幾何
- 核心能力：三角函數、直角三角形、勾股定理
- 基準難度：2

Stage 2 #Escalation Protocol#:
1. Multi-stage Transformation（多階段轉換）：設計需要多個步驟的計算
2. Real-world Parameterization（實際情境參數化）：嵌入真實世界場景
3. Conditional Branching（條件分支）：引入條件判斷

Stage 3 #Finally Rewritten question#:
在一個建築工地中，工人需要搭建一個支撐架。已知支撐架的斜邊長度為10公分，
一條直角邊長度為6公分。請計算另一條直角邊的長度，並求出斜邊與該直角邊的夾角的正弦值。
"""

print("\n📝 测试输入（模拟 LLM 输出）:")
print(test_response[:200] + "...")

parser = RephraseParser()

try:
    result = parser.parse(test_response)

    print("\n✅ 解析成功！")
    print("\n📊 解析结果:")
    print(f"   领域识别: {result.identified_domain}")
    print(f"   核心能力: {result.core_competencies}")
    print(f"   基准难度: {result.baseline_difficulty}/5")
    print(f"   应用维度: {len(result.applied_dimensions)} 个")

    # 验证
    print("\n🔍 验证:")

    if result.identified_domain == "幾何":
        print("   ✅ 领域识别正确（幾何）")
    elif result.identified_domain == "Unknown":
        print("   ❌ 领域识别失败（返回 Unknown）")
    else:
        print(f"   ⚠️  领域识别结果: {result.identified_domain}")

    if "三角函數" in result.core_competencies:
        print("   ✅ 核心能力提取正确（包含三角函數）")
    else:
        print(f"   ⚠️  核心能力: {result.core_competencies}")

    if result.baseline_difficulty == 2:
        print("   ✅ 难度提取正确（2/5）")
    else:
        print(f"   ⚠️  难度: {result.baseline_difficulty}")

    if len(result.applied_dimensions) >= 3:
        print(f"   ✅ 应用维度提取正确（{len(result.applied_dimensions)} 个）")
    else:
        print(f"   ⚠️  应用维度: {result.applied_dimensions}")

except Exception as e:
    print(f"\n❌ 解析失败: {e}")
    import traceback
    traceback.print_exc()

# 测试英文格式
print("\n" + "=" * 70)
print("🧪 测试英文格式（向后兼容）")
print("=" * 70)

english_response = """
Stage 1 #Problem Deconstruction#:
- Domain Identification: Geometry
- Core Competencies: trigonometry, right triangle, Pythagorean theorem
- Baseline Difficulty: 2

Stage 2 #Escalation Protocol#:
1. Multi-stage Transformation: Design multi-step calculations
2. Real-world Parameterization: Embed real-world scenarios
3. Conditional Branching: Introduce conditional logic

Stage 3 #Finally Rewritten question#:
In a construction site, workers need to build a support frame...
"""

try:
    result2 = parser.parse(english_response)

    print("\n✅ 英文格式解析成功！")
    print(f"   领域识别: {result2.identified_domain}")
    print(f"   核心能力: {result2.core_competencies}")

    if result2.identified_domain == "Geometry":
        print("   ✅ 向后兼容性正常")

except Exception as e:
    print(f"\n❌ 英文格式解析失败: {e}")

print("\n" + "=" * 70)
print("✅ 测试完成！")
print("=" * 70)
