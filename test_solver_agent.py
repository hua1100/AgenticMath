#!/usr/bin/env python3
"""
测试 Solver Agent - 生成数学题目的详细解答

演示：
1. 初始化 Solver Agent
2. 为简单题目生成解答
3. 为复杂题目生成解答
4. 验证 CoT (Chain-of-Thought) 推理过程
"""

import os
import sys
from pathlib import Path

# 加入项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 检查 API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ 错误：请先设置 OPENAI_API_KEY 环境变量")
    sys.exit(1)

print("=" * 80)
print("🧪 Solver Agent 测试")
print("=" * 80)

# 导入模块
from src.agents.llm_client import LLMClient, LLMConfig
from src.agents.solver_agent import SolverAgent

# 初始化 LLM Client
print("\n🤖 初始化 LLM Client...")
llm_client = LLMClient(LLMConfig(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3
))

# 初始化 Solver Agent
print("🔧 初始化 Solver Agent...")
solver_agent = SolverAgent(llm_client=llm_client)

print("\n" + "=" * 80)
print("📝 测试案例")
print("=" * 80)

# 测试案例
test_cases = [
    {
        "name": "简单代数问题",
        "question": "Solve for x: 2x + 3 = 11",
        "expected_answer": "4",
    },
    {
        "name": "几何问题（直角三角形）",
        "question": "在直角三角形ABC中，角C为直角，AB = 10公分，BC = 6公分，求 AC 的长度。",
        "expected_answer": "8",
    },
    {
        "name": "应用问题",
        "question": "A rectangular garden has a length that is 3 meters more than twice its width. If the perimeter of the garden is 22 meters, find the width of the garden. Express your answer as a decimal rounded to two decimal places.",
        "expected_answer": "2.67",
    },
    {
        "name": "三角函数问题",
        "question": "求 sin 75° 的精确值（提示：75° = 45° + 30°）。",
        "expected_answer": "(√6 + √2)/4",
    },
]

results = []

for idx, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 80}")
    print(f"🧪 测试 {idx}/{len(test_cases)}: {test['name']}")
    print("=" * 80)

    print(f"\n问题：{test['question']}")
    print(f"预期答案：{test['expected_answer']}")

    # 生成解答
    try:
        print("\n⏳ 生成解答中...")
        output = solver_agent.solve(question=test['question'])

        print(f"\n" + "=" * 80)
        print("📊 生成结果")
        print("=" * 80)

        print(f"\n✅ 最终答案：{output.final_answer}")

        print(f"\n💭 推理过程：")
        print("-" * 80)
        # 只显示前 500 字符的推理过程
        thought = output.thought_process
        if len(thought) > 500:
            print(thought[:500] + "...")
            print(f"\n[完整推理过程共 {len(thought)} 字符]")
        else:
            print(thought)

        if output.intermediate_steps:
            print(f"\n📋 中间步骤 ({len(output.intermediate_steps)} 步)：")
            for i, step in enumerate(output.intermediate_steps[:5], 1):  # 只显示前5步
                print(f"  {i}. {step[:100]}{'...' if len(step) > 100 else ''}")
            if len(output.intermediate_steps) > 5:
                print(f"  ... (还有 {len(output.intermediate_steps) - 5} 步)")

        results.append({
            "test": test['name'],
            "success": True,
            "answer": output.final_answer,
        })

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        results.append({
            "test": test['name'],
            "success": False,
            "error": str(e),
        })

# 总结
print("\n" + "=" * 80)
print("📊 测试总结")
print("=" * 80)

successful = sum(1 for r in results if r['success'])
print(f"\n成功: {successful}/{len(test_cases)}")

for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"{status} {r['test']}", end="")
    if r['success']:
        print(f" - 答案: {r['answer']}")
    else:
        print(f" - 错误: {r.get('error', 'Unknown')}")

# 成本统计
print(f"\n" + "=" * 80)
print("💰 成本统计")
print("=" * 80)
print(f"总 Tokens: {llm_client.total_tokens_used:,}")
print(f"总成本: ${llm_client.total_cost_usd:.4f}")

print("\n" + "=" * 80)
print("🎉 测试完成！")
print("=" * 80)
