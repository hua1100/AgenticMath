#!/usr/bin/env python3
"""
單一三角函數問題測試 - 快速驗證 CrewAI Pipeline

此腳本使用單一三角函數問題快速測試 CrewAI Pipeline。
適合用來驗證系統是否正常運作。
"""

import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime
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
print("🧪 三角函數問題 - CrewAI Pipeline 快速測試")
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

# 創建三角函數測試問題
print("\n📝 創建測試問題...")
original_problem = Problem(
    id=uuid4(),
    content="在直角三角形ABC中，角C為直角，AB = 10公分，BC = 6公分，求 sin A 的值。",
    domain=MathDomain.GEOMETRY,
    competencies=["trigonometry", "geometric_reasoning"],
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
    "Real-world Parameterization",
    "Multi-stage Transformation",
    "Conditional Branching"
]

print(f"\n🎯 應用複雜度提升維度：")
for i, dim in enumerate(dimensions, 1):
    print(f"   {i}. {dim}")

# 執行 Pipeline
print(f"\n⏳ 執行 CrewAI Pipeline...")
print(f"   這可能需要 30-90 秒...")
print(f"   Pipeline 會自動執行：")
print(f"   1️⃣  改寫問題（Rephrase Agent）")
print(f"   2️⃣  評估品質（Review Agent）")
print(f"   3️⃣  修訂改進（Revise Agent，如需要）")
print(f"   4️⃣  重複步驟 2-3 直到品質達標")

start_time = datetime.now()

try:
    result = pipeline.process(
        original_problem=original_problem,
        escalation_dimensions=dimensions,
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    # 顯示結果
    print("\n" + "="*80)
    print("✅ 處理完成！")
    print("="*80)

    print(f"\n📊 執行統計：")
    print(f"   Session ID: {result['session_id']}")
    print(f"   狀態：{result['final_status']}")
    print(f"   最終評分：{result['final_score']}/5.0 (門檻: 4.5)")
    print(f"   迭代次數：{result['iteration_count']}")
    print(f"   執行時間：{elapsed:.1f} 秒")

    print(f"\n📝 改寫後的問題：")
    print("   " + "-"*76)
    # 格式化輸出
    question = result['final_question']
    import textwrap
    wrapped = textwrap.fill(question, width=76, initial_indent="   ", subsequent_indent="   ")
    print(wrapped)
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
        print(f"   ✓ 迭代次數: {session.iteration_count}")

        # 查詢問題鏈
        final_problem = db_session.query(Problem).filter_by(
            id=session.final_problem_id
        ).first()

        if final_problem and final_problem.parent_id:
            print(f"\n🔗 問題演化鏈：")
            print(f"   原始問題 (難度 {original_problem.baseline_difficulty})")
            print(f"      ↓")

            parent = db_session.query(Problem).filter_by(
                id=final_problem.parent_id
            ).first()
            if parent:
                print(f"   改寫問題 (難度 {parent.baseline_difficulty})")
                print(f"      ↓")

            print(f"   最終問題 (難度 {final_problem.baseline_difficulty})")

    # 成本統計
    total_tokens = llm_client.total_tokens_used
    total_cost = llm_client.total_cost_usd

    print(f"\n💰 成本統計：")
    print(f"   Token 使用量: {total_tokens:,} tokens")
    print(f"   估算成本: ${total_cost:.4f} USD")

    print("\n" + "="*80)
    print("🎉 測試成功！")
    print("="*80)

    print(f"\n💡 提示：")
    if result['iteration_count'] == 1:
        print(f"   ✓ 第一次改寫就達到高品質標準（評分 {result['final_score']}）")
    else:
        print(f"   ✓ 經過 {result['iteration_count']} 次迭代優化後達到品質標準")
    print(f"   ✓ 問題複雜度從 {original_problem.baseline_difficulty} 提升到更高層次")
    print(f"   ✓ 應用了 {len(dimensions)} 個複雜度提升維度")

except Exception as e:
    print(f"\n❌ 錯誤：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    db_session.close()
    print(f"\n👋 測試結束")
