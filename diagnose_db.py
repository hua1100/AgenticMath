#!/usr/bin/env python3
"""
诊断 test_results.db 数据库状态
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "test_results.db"

print("=" * 70)
print("🔍 数据库诊断工具")
print("=" * 70)

if not db_path.exists():
    print(f"\n❌ 数据库文件不存在：{db_path}")
    print("\n请先运行：")
    print("   python reinit_test_db.py")
    exit(1)

print(f"\n✅ 数据库文件存在：{db_path}")
print(f"   大小：{db_path.stat().st_size:,} 字节")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 检查表
print("\n📋 表结构检查：")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

expected_tables = ['agent_executions', 'problems', 'quality_assessments', 'rephrase_sessions']
for table in expected_tables:
    if table in tables:
        print(f"   ✅ {table}")
    else:
        print(f"   ❌ {table} (缺失)")

if 'agent_executions' not in tables:
    print("\n⚠️  警告：agent_executions 表不存在！")
    print("   这就是为什么看不到 Review Agent 记录。")
    print("\n解决方法：")
    print("   1. 运行：python reinit_test_db.py")
    print("   2. 运行：python test_trigonometry_pipeline.py")
    conn.close()
    exit(1)

# 检查记录数
print("\n📊 记录统计：")

# Agent executions
cursor.execute("""
    SELECT agent_type, COUNT(*) as count
    FROM agent_executions
    GROUP BY agent_type
    ORDER BY agent_type
""")
agent_stats = cursor.fetchall()

if agent_stats:
    print("\n   Agent 执行记录：")
    total_agents = 0
    has_review = False
    has_revise = False

    for row in agent_stats:
        count = row['count']
        total_agents += count
        print(f"      {row['agent_type']:10} : {count:3} 条")
        if row['agent_type'] == 'REVIEW':
            has_review = True
        if row['agent_type'] == 'REVISE':
            has_revise = True

    print(f"      {'总计':10} : {total_agents:3} 条")

    if not has_review:
        print("\n   ⚠️  没有 REVIEW 记录！")
        print("      可能原因：")
        print("      1. 所有测试在第一次 review 就达到质量门槛（4.5分）")
        print("      2. 或者测试在 rephrase 阶段就失败了")
        print("      3. 或者使用的是旧数据库（重新初始化前的）")

    if not has_revise:
        print("\n   ℹ️  没有 REVISE 记录")
        print("      这是正常的！如果所有问题第一次 review 就达标，")
        print("      就不需要 revise。")
else:
    print("   ❌ 没有任何 agent 执行记录")
    print("\n   原因：还没有运行测试，或使用的是旧数据库")
    print("\n   请执行：")
    print("      python test_trigonometry_pipeline.py")

# Rephrase sessions
cursor.execute("SELECT COUNT(*) as count FROM rephrase_sessions")
session_count = cursor.fetchone()['count']
print(f"\n   Rephrase Sessions: {session_count} 条")

if session_count > 0:
    cursor.execute("""
        SELECT final_status, COUNT(*) as count
        FROM rephrase_sessions
        GROUP BY final_status
    """)
    for row in cursor.fetchall():
        print(f"      {row['final_status']:25} : {row['count']:3} 条")

# Quality assessments
cursor.execute("SELECT COUNT(*) as count FROM quality_assessments")
qa_count = cursor.fetchone()['count']
print(f"\n   Quality Assessments: {qa_count} 条")

# 最近的记录
if agent_stats:
    print("\n📝 最近 5 条 agent 执行记录：")
    cursor.execute("""
        SELECT agent_type, created_at, execution_time_ms
        FROM agent_executions
        ORDER BY created_at DESC
        LIMIT 5
    """)

    print(f"\n   {'Agent':<10} {'时间':<25} {'耗时':<10}")
    print("   " + "-" * 50)
    for row in cursor.fetchall():
        print(f"   {row['agent_type']:<10} {row['created_at']:<25} {row['execution_time_ms']:>6}ms")

print("\n" + "=" * 70)

# 总结建议
if not agent_stats:
    print("💡 建议：")
    print("   1. 运行测试：python test_trigonometry_pipeline.py")
    print("   2. 然后查询记录：python query_agent_logs.py")
elif agent_stats and not has_review:
    print("💡 可能的情况：")
    print("   1. ✅ 如果所有测试状态都是 SUCCESS（iteration=1），")
    print("      说明改写后的问题第一次就达到 4.5 分标准，")
    print("      这是**正常且理想**的情况！不需要 revise。")
    print("\n   2. ❌ 如果有 ERROR 状态，说明测试失败了，")
    print("      需要检查错误日志。")
    print("\n   查看测试状态：python query_agent_logs.py -> 选项 4")
else:
    print("✅ 数据库状态正常！")
    print("\n   可以使用 query_agent_logs.py 查询详细记录")

print("=" * 70)

conn.close()
