#!/usr/bin/env python3
"""
重新初始化 test_results.db 数据库

删除旧的数据库文件并创建所有需要的表。
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 加入專案根目錄
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入模型
from src.models.problem import Problem
from src.models.rephrase_session import RephraseSession
from src.models.quality_assessment import QualityAssessment
from src.models.agent_execution import AgentExecution

print("=" * 60)
print("🗄️  重新初始化测试数据库")
print("=" * 60)

db_path = project_root / "test_results.db"

# 删除旧数据库
if db_path.exists():
    print(f"\n⚠️  发现旧数据库：{db_path}")
    print("   正在删除...")
    db_path.unlink()
    print("   ✅ 已删除")
else:
    print(f"\n✓ 数据库文件不存在，将创建新的")

# 创建新数据库
print(f"\n💾 创建新数据库：{db_path}")
engine = create_engine(f"sqlite:///{db_path}")

# 创建所有表
print("\n📋 创建表...")
tables_created = []

try:
    Problem.__table__.create(engine, checkfirst=True)
    tables_created.append("problems")
    print("   ✅ problems")
except Exception as e:
    print(f"   ❌ problems: {e}")

try:
    RephraseSession.__table__.create(engine, checkfirst=True)
    tables_created.append("rephrase_sessions")
    print("   ✅ rephrase_sessions")
except Exception as e:
    print(f"   ❌ rephrase_sessions: {e}")

try:
    QualityAssessment.__table__.create(engine, checkfirst=True)
    tables_created.append("quality_assessments")
    print("   ✅ quality_assessments")
except Exception as e:
    print(f"   ❌ quality_assessments: {e}")

try:
    AgentExecution.__table__.create(engine, checkfirst=True)
    tables_created.append("agent_executions")
    print("   ✅ agent_executions")
except Exception as e:
    print(f"   ❌ agent_executions: {e}")

# 验证表是否创建成功
print("\n🔍 验证表创建...")
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"\n✅ 成功创建 {len(tables)} 个表：")
for table in tables:
    print(f"   - {table}")

if len(tables) == len(tables_created):
    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n现在可以运行测试：")
    print("   python test_trigonometry_pipeline.py")
    print("\n然后查询记录：")
    print("   python query_agent_logs.py")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("⚠️  警告：部分表创建失败")
    print("=" * 60)
