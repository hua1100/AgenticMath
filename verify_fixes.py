#!/usr/bin/env python3
"""
验证所有修复是否已正确应用
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("🔍 验证修复状态")
print("=" * 60)

# 测试 1: 检查 rephrase_agent.py 是否使用正确的属性名
print("\n1️⃣  检查 RephraseAgent 属性名...")
with open(project_root / "src/agents/rephrase_agent.py", "r") as f:
    content = f.read()

if "expected_difficulty" in content:
    print("   ❌ 仍然使用 expected_difficulty（需要拉取最新代码）")
    has_error = True
elif "baseline_difficulty" in content:
    print("   ✅ 正确使用 baseline_difficulty")
    has_error = False
else:
    print("   ⚠️  无法确定状态")
    has_error = True

if "stage1_reasoning" in content and "stage1_problem_deconstruction" not in content:
    print("   ❌ 仍然使用 stage1_reasoning（需要拉取最新代码）")
    has_error = True
elif "stage1_problem_deconstruction" in content:
    print("   ✅ 正确使用 stage1_problem_deconstruction")

# 测试 2: 检查 AgentToolkit 是否接受 db_session
print("\n2️⃣  检查 AgentToolkit db_session 传递...")
with open(project_root / "src/orchestration/crewai_pipeline.py", "r") as f:
    content = f.read()

if "def __init__(self, llm_client: LLMClient, db_session:" in content:
    print("   ✅ AgentToolkit 正确接受 db_session 参数")
elif "def __init__(self, llm_client: LLMClient):" in content:
    print("   ❌ AgentToolkit 没有 db_session 参数（需要拉取最新代码）")
    has_error = True
else:
    print("   ⚠️  无法确定状态")
    has_error = True

# 测试 3: 检查 LaTeX 格式化工具是否存在
print("\n3️⃣  检查 LaTeX 格式化工具...")
latex_formatter = project_root / "src/utils/latex_formatter.py"
if latex_formatter.exists():
    print("   ✅ LaTeX 格式化工具已创建")
else:
    print("   ❌ LaTeX 格式化工具不存在（需要拉取最新代码）")
    has_error = True

print("\n" + "=" * 60)
if has_error:
    print("❌ 发现问题 - 请执行以下命令拉取最新代码：")
    print("   git pull origin claude/math-problem-generator-agent-011CUrcqu5t8KWnXNxxCMis6")
else:
    print("✅ 所有修复已正确应用！")
    print("\n现在可以运行测试：")
    print("   python test_trigonometry_pipeline.py")
print("=" * 60)
