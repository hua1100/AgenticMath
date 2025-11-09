#!/usr/bin/env python3
"""
查詢 Agent 執行記錄 - 診斷工具

此腳本提供便捷的查詢功能，用於分析 agent 的執行記錄。
特別適合診斷測試失敗的原因。
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 資料庫路徑
db_path = Path(__file__).parent / "test_results.db"

if not db_path.exists():
    print(f"❌ 錯誤：資料庫檔案不存在: {db_path}")
    print("   請先執行測試腳本以產生測試資料")
    sys.exit(1)

# 連接資料庫
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def print_separator(char="=", length=80):
    """列印分隔線"""
    print(char * length)

def print_section(title):
    """列印區塊標題"""
    print_separator()
    print(f"📊 {title}")
    print_separator()

def query_agent_summary():
    """查詢 Agent 執行摘要"""
    print_section("Agent 執行摘要")

    cursor.execute("""
        SELECT
            agent_type,
            COUNT(*) as execution_count,
            AVG(execution_time_ms) as avg_time_ms,
            MIN(execution_time_ms) as min_time_ms,
            MAX(execution_time_ms) as max_time_ms
        FROM agent_executions
        GROUP BY agent_type
        ORDER BY agent_type
    """)

    results = cursor.fetchall()

    if not results:
        print("❌ 沒有找到任何執行記錄")
        return

    print(f"\n{'Agent 類型':<15} {'執行次數':<10} {'平均時間':<12} {'最小時間':<12} {'最大時間':<12}")
    print("-" * 80)

    for row in results:
        print(f"{row['agent_type']:<15} {row['execution_count']:<10} "
              f"{row['avg_time_ms']:>10.1f}ms {row['min_time_ms']:>10}ms {row['max_time_ms']:>10}ms")

def query_review_no_suggestions():
    """查詢 Review Agent 沒有提供建議的記錄"""
    print_section("Review Agent - 沒有改進建議的記錄")

    cursor.execute("""
        SELECT
            id,
            input_data,
            output_data,
            raw_llm_response,
            execution_time_ms,
            created_at
        FROM agent_executions
        WHERE agent_type = 'review'
        ORDER BY created_at DESC
    """)

    results = cursor.fetchall()

    if not results:
        print("❌ 沒有找到 Review Agent 執行記錄")
        return

    no_suggestions_count = 0

    for row in results:
        output_data = json.loads(row['output_data'])
        suggestions = output_data.get('suggestions', [])
        overall_score = output_data.get('overall_score', 0)

        # 檢查是否沒有建議但分數低於 4.5
        if len(suggestions) == 0 and overall_score < 4.5:
            no_suggestions_count += 1

            print(f"\n🔍 執行記錄 #{no_suggestions_count}")
            print(f"   ID: {row['id']}")
            print(f"   時間: {row['created_at']}")
            print(f"   整體評分: {overall_score:.1f}/5.0")
            print(f"   改進建議數: {len(suggestions)}")
            print(f"   執行時間: {row['execution_time_ms']}ms")

            # 顯示評分詳細
            print(f"\n   詳細評分:")
            print(f"   - 文法與清晰度: {output_data.get('clarity_grammar_score', 'N/A')}")
            print(f"   - 邏輯連貫性: {output_data.get('logical_coherence_score', 'N/A')}")
            print(f"   - 數學有效性: {output_data.get('mathematical_validity_score', 'N/A')}")

            # 顯示思考過程（截取前 200 字元）
            thought_process = output_data.get('thought_process', '')
            if thought_process:
                print(f"\n   思考過程（前200字）:")
                print(f"   {thought_process[:200]}...")

            # 顯示原始 LLM 回應（截取前 500 字元）
            print(f"\n   原始 LLM 回應（前500字）:")
            if row['raw_llm_response']:
                print(f"   {row['raw_llm_response'][:500]}...")
            else:
                print("   （無）")

    if no_suggestions_count == 0:
        print("\n✅ 所有 Review Agent 執行都有提供改進建議，或評分 >= 4.5")
    else:
        print(f"\n⚠️  發現 {no_suggestions_count} 個沒有改進建議但評分 < 4.5 的記錄")

def query_recent_executions(limit=10):
    """查詢最近的執行記錄"""
    print_section(f"最近 {limit} 次 Agent 執行")

    cursor.execute("""
        SELECT
            id,
            agent_type,
            execution_time_ms,
            llm_model,
            created_at
        FROM agent_executions
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()

    if not results:
        print("❌ 沒有找到任何執行記錄")
        return

    print(f"\n{'#':<4} {'Agent 類型':<15} {'執行時間':<12} {'模型':<15} {'時間':<25}")
    print("-" * 80)

    for idx, row in enumerate(results, 1):
        print(f"{idx:<4} {row['agent_type']:<15} {row['execution_time_ms']:>10}ms "
              f"{row['llm_model']:<15} {row['created_at']:<25}")

def query_rephrase_sessions():
    """查詢 Rephrase Sessions"""
    print_section("Rephrase Sessions 摘要")

    cursor.execute("""
        SELECT
            id,
            final_status,
            iteration_count,
            quality_threshold,
            created_at,
            completed_at
        FROM rephrase_sessions
        ORDER BY created_at DESC
    """)

    results = cursor.fetchall()

    if not results:
        print("❌ 沒有找到任何 Rephrase Session")
        return

    print(f"\n{'#':<4} {'狀態':<30} {'迭代':<6} {'門檻':<6} {'開始時間':<20}")
    print("-" * 80)

    for idx, row in enumerate(results, 1):
        status_emoji = {
            'success': '✅',
            'max_iterations_exceeded': '⚠️ ',
            'error': '❌'
        }.get(row['final_status'], '❓')

        status_display = f"{status_emoji} {row['final_status']}"

        print(f"{idx:<4} {status_display:<30} {row['iteration_count']:<6} "
              f"{row['quality_threshold']:<6} {row['created_at']:<20}")

def query_quality_assessments():
    """查詢品質評估分數分布"""
    print_section("品質評估分數分布")

    cursor.execute("""
        SELECT
            overall_score,
            COUNT(*) as count
        FROM quality_assessments
        GROUP BY overall_score
        ORDER BY overall_score DESC
    """)

    results = cursor.fetchall()

    if not results:
        print("❌ 沒有找到任何品質評估記錄")
        return

    print(f"\n{'評分':<10} {'次數':<10} {'視覺化':<40}")
    print("-" * 80)

    max_count = max(row['count'] for row in results)

    for row in results:
        score = row['overall_score']
        count = row['count']
        bar_length = int((count / max_count) * 40)
        bar = '█' * bar_length

        emoji = '✅' if score >= 4.5 else '⚠️ ' if score >= 4.0 else '❌'

        print(f"{emoji} {score:<7.1f} {count:<10} {bar}")

def export_full_review_output(execution_id):
    """匯出完整的 Review Agent 輸出"""
    print_section(f"完整 Review Agent 輸出 - {execution_id}")

    cursor.execute("""
        SELECT
            input_data,
            output_data,
            raw_llm_response,
            prompt_template
        FROM agent_executions
        WHERE id = ? AND agent_type = 'review'
    """, (execution_id,))

    result = cursor.fetchone()

    if not result:
        print(f"❌ 找不到 ID 為 {execution_id} 的 Review Agent 執行記錄")
        return

    print("\n📝 輸入資料:")
    print(json.dumps(json.loads(result['input_data']), indent=2, ensure_ascii=False))

    print("\n📊 輸出資料:")
    print(json.dumps(json.loads(result['output_data']), indent=2, ensure_ascii=False))

    print("\n💬 原始 LLM 回應:")
    print(result['raw_llm_response'])

    print("\n📋 提示詞模板（前 500 字元）:")
    print(result['prompt_template'][:500])

# 主選單
def main():
    print_separator("=")
    print("🔍 Agent 執行記錄查詢工具")
    print_separator("=")
    print(f"\n資料庫: {db_path}")
    print()

    while True:
        print("\n請選擇查詢:")
        print("  1. Agent 執行摘要")
        print("  2. Review Agent - 沒有改進建議的記錄")
        print("  3. 最近 10 次執行")
        print("  4. Rephrase Sessions 摘要")
        print("  5. 品質評估分數分布")
        print("  6. 匯出完整 Review 輸出 (需要 ID)")
        print("  0. 離開")

        choice = input("\n輸入選項: ").strip()

        if choice == "1":
            query_agent_summary()
        elif choice == "2":
            query_review_no_suggestions()
        elif choice == "3":
            query_recent_executions()
        elif choice == "4":
            query_rephrase_sessions()
        elif choice == "5":
            query_quality_assessments()
        elif choice == "6":
            exec_id = input("請輸入執行記錄 ID: ").strip()
            export_full_review_output(exec_id)
        elif choice == "0":
            print("\n👋 再見！")
            break
        else:
            print("❌ 無效的選項，請重新選擇")

    conn.close()

if __name__ == "__main__":
    main()
