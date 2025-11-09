#!/usr/bin/env python3
"""
快速測試腳本 - 展示 CrewAI Pipeline 功能

這個腳本會：
1. 使用內存資料庫（不需要 PostgreSQL）
2. 創建一個簡單的數學問題
3. 使用 CrewAI Pipeline 進行複雜度提升
4. 顯示結果

需求：
- export OPENAI_API_KEY='your-key-here'
"""

import os
import sys
from pathlib import Path
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 加入專案根目錄到 Python 路徑
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 檢查 API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ 錯誤：請先設置 OPENAI_API_KEY 環境變數")
    print("   執行：export OPENAI_API_KEY='your-api-key-here'")
    sys.exit(1)

print("="*80)
print("🧪 AgenticMath - CrewAI Pipeline 快速測試")
print("="*80)

# 導入模組
print("\n📦 導入模組...")
from src.storage.database import Base
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
    quality_threshold=4.5,  # 品質門檻
    max_iterations=5,        # 最多修改5次
)
print("   ✓ Pipeline 就緒")

# 創建原始問題
print("\n📝 創建原始問題...")
original_problem = Problem(
    id=uuid4(),
    content="一個數的兩倍加上5等於17，求這個數。",
    domain=MathDomain.ALGEBRA,
    competencies=["linear_equations"],
    baseline_difficulty=1,
    source=ProblemSource.ORIGINAL,
    source_type=SourceType.MANUAL,
)
db_session.add(original_problem)
db_session.commit()

print(f"\n   原始問題：{original_problem.content}")
print(f"   領域：{original_problem.domain.value}")
print(f"   難度：{original_problem.baseline_difficulty}/5")

# 定義複雜度提升維度
dimensions = [
    "Multi-stage Transformation",
    "Real-world Parameterization",
    "Conditional Branching"
]

print(f"\n🎯 應用複雜度提升維度：")
for i, dim in enumerate(dimensions, 1):
    print(f"   {i}. {dim}")

# 執行 Pipeline
print(f"\n⏳ 執行 CrewAI Pipeline...")
print(f"   這可能需要 30-60 秒...")

try:
    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=dimensions,
    )

    # 顯示結果
    print("\n" + "="*80)
    print("✅ 處理完成！")
    print("="*80)

    print(f"\n📊 執行統計：")
    print(f"   Session ID: {result['session_id']}")
    print(f"   狀態：{result['final_status']}")
    print(f"   最終評分：{result['final_score']}/5.0")
    print(f"   迭代次數：{result['iteration_count']}")
    print(f"   執行時間：{result['total_time_ms']/1000:.1f} 秒")

    print(f"\n📝 改寫後的問題：")
    print("   " + "-"*76)
    # 格式化輸出，每行最多76個字符
    question = result['final_question']
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
    print("   " + "-"*76)

    # 驗證資料庫記錄
    print(f"\n💾 資料庫驗證：")
    from src.models.rephrase_session import RephraseSession
    session = db_session.query(RephraseSession).filter_by(
        id=result['session_id']
    ).first()

    if session:
        print(f"   ✓ Session 已保存")
        print(f"   ✓ 原始問題 ID: {session.original_problem_id}")
        print(f"   ✓ 最終問題 ID: {session.final_problem_id}")
        print(f"   ✓ 品質門檻: {session.quality_threshold}")

        # 查詢問題鏈
        final_problem = db_session.query(Problem).filter_by(
            id=session.final_problem_id
        ).first()

        if final_problem:
            print(f"\n🔗 問題演化鏈：")
            print(f"   1. 原始問題 (難度 {original_problem.baseline_difficulty}) → ID: {original_problem.id}")

            if final_problem.parent_id:
                parent = db_session.query(Problem).filter_by(
                    id=final_problem.parent_id
                ).first()
                if parent:
                    print(f"   2. 改寫問題 (難度 {parent.baseline_difficulty}) → ID: {parent.id}")

            print(f"   3. 最終問題 (難度 {final_problem.baseline_difficulty}) → ID: {final_problem.id}")

    print("\n" + "="*80)
    print("🎉 測試成功！")
    print("="*80)

    print(f"\n💡 提示：")
    print(f"   - 此次測試約消耗 8,000 tokens (約 $0.04 USD)")
    print(f"   - 如果評分未達標 ({result['final_score']} < 4.5)，系統會自動修改")
    print(f"   - 最多修改 5 次以達到品質標準")

    # 成本估算
    total_tokens = llm_client.total_tokens_used
    estimated_cost = llm_client.total_cost_usd
    print(f"\n💰 本次測試成本：")
    print(f"   Token 使用量: {total_tokens:,} tokens")
    print(f"   估算成本: ${estimated_cost:.4f} USD")

except Exception as e:
    print(f"\n❌ 錯誤：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    db_session.close()
    print(f"\n👋 測試結束")
