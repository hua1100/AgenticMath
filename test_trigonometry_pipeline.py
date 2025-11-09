#!/usr/bin/env python3
"""
三角函數問題 - CrewAI Pipeline 完整測試

此腳本使用多個三角函數問題測試 CrewAI Pipeline 的完整工作流程。
包含不同難度的題目，從基礎到進階。
"""

import os
import sys
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 檢查 API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ 錯誤：請先設置 OPENAI_API_KEY 環境變數")
    print("   執行：export OPENAI_API_KEY='your-api-key-here'")
    sys.exit(1)

print("="*80)
print("🧪 三角函數問題 - CrewAI Pipeline 測試")
print("="*80)

# 導入模組
print("\n📦 導入模組...")
from src.models.base import Base
from src.models.problem import Problem, ProblemSource, MathDomain, SourceType
from src.agents.llm_client import LLMClient, LLMConfig
from src.orchestration.crewai_pipeline import CrewAIPipeline

# 設置內存資料庫
print("💾 設置內存資料庫...")
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()
print("   ✓ 資料庫就緒")

# 初始化 LLM Client
print("\n🤖 初始化 LLM Client (GPT-4o)...")
config = LLMConfig(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3
)
llm_client = LLMClient(config)
print("   ✓ LLM Client 就緒")

# 初始化 CrewAI Pipeline
print("\n🚀 初始化 CrewAI Pipeline...")
pipeline = CrewAIPipeline(
    llm_client=llm_client,
    db_session=db_session,
    quality_threshold=4.5,
    max_iterations=5,
)
print("   ✓ Pipeline 就緒")

# 定義三角函數測試題目
test_problems = [
    {
        "name": "基礎：三角函數值",
        "content": "在直角三角形ABC中，角C為直角，AB = 10公分，BC = 6公分，求 sin A 的值。",
        "difficulty": 1,
        "dimensions": [
            "Real-world Parameterization",
            "Multi-stage Transformation",
            "Conditional Branching"
        ]
    },
    {
        "name": "中級：三角恆等式",
        "content": "已知 sin θ = 3/5，且 θ 在第一象限，求 cos θ 和 tan θ 的值。",
        "difficulty": 2,
        "dimensions": [
            "Multi-stage Transformation",
            "Conditional Branching",
            "Real-world Parameterization"
        ]
    },
    {
        "name": "中級：正弦定理應用",
        "content": "在三角形ABC中，a = 8，b = 10，角A = 30度，求角B的大小。",
        "difficulty": 2,
        "dimensions": [
            "Multi-stage Transformation",
            "Conditional Branching",
            "Cross-domain Integration"
        ]
    },
    {
        "name": "進階：複合角公式",
        "content": "求 sin 75° 的精確值（提示：75° = 45° + 30°）。",
        "difficulty": 3,
        "dimensions": [
            "Multi-stage Transformation",
            "Inverse Problem Design",
            "Cross-domain Integration"
        ]
    },
    {
        "name": "進階：三角方程式",
        "content": "解方程式：2sin²x + 3cos x - 3 = 0，其中 0° ≤ x ≤ 360°。",
        "difficulty": 4,
        "dimensions": [
            "Multi-stage Transformation",
            "Conditional Branching",
            "Optimization Extension"
        ]
    }
]

print(f"\n📚 準備測試 {len(test_problems)} 個三角函數問題")
print("="*80)

# 測試每個問題
results = []
total_tokens = 0
total_cost = 0.0

for idx, prob_data in enumerate(test_problems, 1):
    print(f"\n{'='*80}")
    print(f"📝 測試 {idx}/{len(test_problems)}: {prob_data['name']}")
    print(f"{'='*80}")

    # 創建原始問題
    original_problem = Problem(
        id=uuid4(),
        content=prob_data["content"],
        domain=MathDomain.GEOMETRY,  # 三角函數歸類為幾何
        competencies=["trigonometry", "geometric_reasoning"],
        baseline_difficulty=prob_data["difficulty"],
        source=ProblemSource.ORIGINAL,
        source_type=SourceType.MANUAL,
    )
    db_session.add(original_problem)
    db_session.commit()

    print(f"\n   原始問題：{original_problem.content}")
    print(f"   難度：{original_problem.baseline_difficulty}/5")

    print(f"\n🎯 應用複雜度提升維度：")
    for i, dim in enumerate(prob_data["dimensions"], 1):
        print(f"   {i}. {dim}")

    print(f"\n⏳ 執行 CrewAI Pipeline...")

    try:
        # 記錄開始前的 token 使用量
        tokens_before = llm_client.total_tokens_used
        cost_before = llm_client.total_cost_usd

        # 執行 pipeline
        result = pipeline.process(
            original_problem=original_problem,
            escalation_dimensions=prob_data["dimensions"],
        )

        # 計算本次使用量
        tokens_used = llm_client.total_tokens_used - tokens_before
        cost_used = llm_client.total_cost_usd - cost_before

        # 顯示結果
        print(f"\n✅ 處理完成！")
        print(f"\n📊 結果：")
        print(f"   狀態：{result['final_status']}")
        print(f"   最終評分：{result['final_score']}/5.0")
        print(f"   迭代次數：{result['iteration_count']}")
        print(f"   執行時間：{result['total_time_ms']/1000:.1f} 秒")

        print(f"\n📝 改寫後的問題：")
        question = result['final_question']
        # 格式化輸出，每行最多76個字符
        words = question.split()
        line = "   "
        for word in words:
            if len(line) + len(word) + 1 > 80:
                print(line)
                line = "   " + word
            else:
                line += (" " if len(line) > 3 else "") + word
        if line.strip():
            print(line)

        print(f"\n💰 本次成本：")
        print(f"   Tokens: {tokens_used:,}")
        print(f"   成本: ${cost_used:.4f}")

        # 記錄結果
        results.append({
            "name": prob_data["name"],
            "status": result['final_status'],
            "score": result['final_score'],
            "iterations": result['iteration_count'],
            "tokens": tokens_used,
            "cost": cost_used,
            "success": result['final_status'] == 'success'
        })

        total_tokens += tokens_used
        total_cost += cost_used

    except Exception as e:
        print(f"\n❌ 錯誤：{e}")
        import traceback
        traceback.print_exc()
        results.append({
            "name": prob_data["name"],
            "status": "error",
            "score": 0.0,
            "iterations": 0,
            "tokens": 0,
            "cost": 0.0,
            "success": False
        })

print("\n" + "="*80)
print("📊 測試摘要")
print("="*80)

# 統計
successful = sum(1 for r in results if r["success"])
failed = len(results) - successful

print(f"\n✅ 成功: {successful}/{len(results)}")
print(f"❌ 失敗: {failed}/{len(results)}")

print(f"\n📋 詳細結果：")
print(f"{'題目':<30} {'狀態':<10} {'評分':<8} {'迭代':<6} {'Tokens':<10} {'成本':<10}")
print("-" * 80)
for r in results:
    status_icon = "✅" if r["success"] else "❌"
    print(f"{r['name']:<30} {status_icon} {r['status']:<8} {r['score']:<8.1f} {r['iterations']:<6} {r['tokens']:<10,} ${r['cost']:<9.4f}")

print("\n" + "="*80)
print("💰 總計成本")
print("="*80)
print(f"   總 Tokens: {total_tokens:,}")
print(f"   總成本: ${total_cost:.4f}")
print(f"   平均每題: ${total_cost/len(results):.4f}")

print("\n" + "="*80)
print("🎉 測試完成！")
print("="*80)

db_session.close()
