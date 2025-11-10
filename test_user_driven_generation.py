#!/usr/bin/env python3
"""
测试用户需求驱动的题目生成

演示：
1. 用户指定难度和题数
2. 系统超额生成多个变体
3. 批量评分和筛选
4. 输出多个高质量题目
"""

import os
import sys
from pathlib import Path

# 加入專案根目錄
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 检查 API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ 錯誤：請先設置 OPENAI_API_KEY 環境變數")
    sys.exit(1)

print("=" * 80)
print("🧪 用户需求驱动的题目生成 - 测试")
print("=" * 80)

# 导入模块
from src.agents.llm_client import LLMClient, LLMConfig
from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from src.orchestration.user_driven_generator import (
    ProblemGenerator,
    UserRequest
)

# 初始化 LLM Client
print("\n🤖 初始化 LLM Client...")
llm_client = LLMClient(LLMConfig(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3
))

# 初始化 Agents
print("🔧 初始化 Agents...")
rephrase_agent = RephraseAgent(llm_client=llm_client)
review_agent = ReviewAgent(llm_client=llm_client)

# 创建生成器
print("🏗️  创建题目生成器...")
generator = ProblemGenerator(
    rephrase_agent=rephrase_agent,
    review_agent=review_agent
)

print("\n" + "=" * 80)
print("📝 测试案例")
print("=" * 80)

# 测试案例
test_cases = [
    {
        "name": "中等难度，3 题",
        "problem": "在直角三角形ABC中，角C为直角，AB = 10公分，BC = 6公分，求 sin A 的值。",
        "difficulty": 3,
        "num_questions": 3,
    },
    {
        "name": "简单难度，2 题",
        "problem": "求 sin 75° 的精确值（提示：75° = 45° + 30°）。",
        "difficulty": 2,
        "num_questions": 2,
    },
]

for idx, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 80}")
    print(f"🧪 测试 {idx}/{len(test_cases)}: {test['name']}")
    print("=" * 80)

    print(f"\n原始问题：{test['problem']}")
    print(f"用户需求：难度 {test['difficulty']}/5，需要 {test['num_questions']} 题")

    # 创建用户请求
    request = UserRequest(
        original_problem=test['problem'],
        target_difficulty=test['difficulty'],
        num_questions=test['num_questions'],
        min_quality_score=4.5
    )

    # 生成题目
    try:
        result = generator.generate(request)

        print(f"\n" + "=" * 80)
        print("📊 生成结果")
        print("=" * 80)

        print(f"\n总计生成: {result.total_generated} 个候选")
        print(f"达到标准: {result.passed_quality} 个")
        print(f"最终选出: {result.selected} 个")

        print(f"\n" + "=" * 80)
        print("✅ 输出题目")
        print("=" * 80)

        for i, question in enumerate(result.questions, 1):
            print(f"\n【题目 {i}】{question['variant_type']}")
            print(f"难度: {question['difficulty']}/5")
            print(f"质量: {question['quality_score']:.1f}/5")
            print(f"核心概念: {question['core_concept']}")
            print(f"\n内容:")
            # 格式化输出
            content = question['content']
            words = content.split()
            line = "   "
            for word in words:
                if len(line) + len(word) + 1 > 76:
                    print(line)
                    line = "   " + word
                else:
                    line += (" " if len(line) > 3 else "") + word
            if line.strip():
                print(line)

        # 成本统计
        print(f"\n" + "=" * 80)
        print("💰 成本统计")
        print("=" * 80)
        print(f"总 Tokens: {llm_client.total_tokens_used:,}")
        print(f"总成本: ${llm_client.total_cost_usd:.4f}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("🎉 测试完成！")
print("=" * 80)

print(f"\n📝 注意:")
print(f"   这是 MVP 实现，当前每个变体独立生成。")
print(f"   未来优化：批量生成（一次 LLM 调用生成多个变体）")
print(f"   查看 docs/USER_DRIVEN_GENERATION.md 了解完整设计")
