# 本地測試指南

本指南説明如何在本地測試 Multi-Agent Math Problem Generator 的所有功能。

## 目錄

- [快速開始](#快速開始)
- [單元測試（Mock 測試）](#單元測試mock-測試)
- [E2E 測試（真實 LLM）](#e2e-測試真實-llm)
- [測試 CrewAI Pipeline](#測試-crewai-pipeline)
- [成本估算](#成本估算)
- [故障排除](#故障排除)

---

## 快速開始

### 1. 環境準備

```bash
# 確認在專案根目錄
cd /home/user/AgenticMath

# 安裝依賴（如果還沒安裝）
pip install -r requirements.txt

# 確認安裝成功
python -c "import crewai; print('CrewAI version:', crewai.__version__)"
```

### 2. 設置 OpenAI API Key（僅 E2E 測試需要）

```bash
# 臨時設置（當前 session 有效）
export OPENAI_API_KEY='your-api-key-here'

# 或者永久設置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# 驗證設置
echo $OPENAI_API_KEY
```

---

## 單元測試（Mock 測試）

**特點：**
- ✅ 不需要 API key
- ✅ 執行速度快（幾秒內完成）
- ✅ 不產生費用
- ❌ 使用 mock 數據，不測試真實 LLM 行為

### 運行所有測試

```bash
# 運行所有單元測試和集成測試
pytest

# 輸出詳細信息
pytest -v

# 顯示覆蓋率報告
pytest --cov=src --cov-report=term-missing
```

### 運行特定模塊測試

```bash
# 測試 LLM Client
pytest tests/unit/agents/test_llm_client.py -v

# 測試 Rephrase Agent
pytest tests/unit/agents/test_rephrase_agent.py -v

# 測試 Review Agent
pytest tests/unit/agents/test_review_agent.py -v

# 測試 Revise Agent
pytest tests/unit/agents/test_revise_agent.py -v

# 測試 Iteration Manager
pytest tests/integration/test_iteration_manager.py -v

# 測試 CrewAI Pipeline
pytest tests/integration/test_crewai_pipeline.py -v
```

### 預期結果

```
=============================== test session starts ===============================
platform linux -- Python 3.11.14, pytest-8.4.2, pluggy-1.6.0
collected 63 items

tests/unit/agents/test_llm_client.py ............           [ 19%]
tests/unit/agents/test_rephrase_agent.py .........          [ 33%]
tests/unit/agents/test_review_agent.py .........            [ 47%]
tests/unit/agents/test_revise_agent.py .........            [ 61%]
tests/integration/test_iteration_manager.py ..........      [ 77%]
tests/integration/test_crewai_pipeline.py .....             [ 85%]
tests/contract/test_*.py .........                          [100%]

============================== 63 passed in 3.45s =================================
```

---

## E2E 測試（真實 LLM）

**特點：**
- ✅ 測試真實 LLM 行為
- ✅ 驗證完整工作流程
- ❌ 需要 OpenAI API key
- ❌ 產生費用（約 $0.05 - $0.10 per test）
- ❌ 執行較慢（每個 agent 測試 ~10-30 秒）

### 測試單個 Agent

```bash
# 測試 Rephrase Agent（~15 秒）
python scripts/test_rephrase_pipeline_e2e.py --test-agent rephrase

# 測試 Review Agent（~10 秒）
python scripts/test_rephrase_pipeline_e2e.py --test-agent review

# 測試 Revise Agent（~10 秒）
python scripts/test_rephrase_pipeline_e2e.py --test-agent revise
```

### 測試 Iteration Manager

```bash
# 測試完整的 Review → Revise 循環（~30-60 秒）
python scripts/test_rephrase_pipeline_e2e.py --test-iteration
```

### 測試 CrewAI Pipeline

```bash
# 測試完整的 CrewAI 工作流程（~40-80 秒）
# 使用內存資料庫，不需要配置 PostgreSQL
python scripts/test_rephrase_pipeline_e2e.py --test-crewai
```

### 測試所有組件

```bash
# 運行所有 E2E 測試（~2-3 分鐘）
python scripts/test_rephrase_pipeline_e2e.py --test-all
```

### 預期輸出範例

```
🧪 Rephrase Pipeline E2E Tests
================================================================================

================================================================================
TEST 5: CrewAI Pipeline (Full Workflow)
================================================================================

✓ OpenAI API Key found
✓ In-memory database created

📝 Original Problem:
   一個長方形的長度比寬度多3公尺，周長為22公尺，求寬度。

🎯 Escalation Dimensions:
   - Multi-stage Transformation
   - Real-world Parameterization
   - Conditional Branching

⏳ Running CrewAI pipeline...

✅ Pipeline completed! (took 45.3s)

📊 Results:
   Session ID: 123e4567-e89b-12d3-a456-426614174000
   Status: success
   Final Score: 4.7/5.0
   Iterations: 1
   Total Time: 45234ms

📝 Final Question:
   某建築公司需要規劃一個多功能運動場...

✅ Database Verification:
   Session created: 2025-11-08 10:30:15
   Session completed: 2025-11-08 10:31:00
   Final problem ID: 234e5678-e89b-12d3-a456-426614174001

================================================================================
SUMMARY
================================================================================
✅ CrewAI Pipeline: PASSED
```

---

## 測試 CrewAI Pipeline

CrewAI Pipeline 是我們的**推薦實現**，整合了 CrewAI 框架和現有 agents。

### 快速測試（推薦）

```bash
# 1. 設置 API key
export OPENAI_API_KEY='your-key-here'

# 2. 運行 CrewAI E2E 測試
python scripts/test_rephrase_pipeline_e2e.py --test-crewai

# 預期：約 40-80 秒完成，顯示完整工作流程結果
```

### Python 腳本測試

創建測試腳本 `test_my_pipeline.py`:

```python
#!/usr/bin/env python3
import os
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.problem import Problem, ProblemSource, MathDomain, SourceType
from src.agents.llm_client import LLMClient, LLMConfig
from src.orchestration.crewai_pipeline import CrewAIPipeline

# 設置
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("請設置 OPENAI_API_KEY 環境變數")

# 內存資料庫
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()

# LLM Client
config = LLMConfig(api_key=api_key, model="gpt-4o", temperature=0.3)
llm_client = LLMClient(config)

# Pipeline
pipeline = CrewAIPipeline(
    llm_client=llm_client,
    db_session=db_session,
    quality_threshold=4.5,
    max_iterations=5,
)

# 創建原始問題
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

# 執行
print("🚀 開始處理問題...")
result = pipeline.process(
    original_problem=original_problem,
    escalation_dimensions=[
        "Multi-stage Transformation",
        "Real-world Parameterization",
        "Conditional Branching"
    ],
)

# 結果
print("\n" + "="*80)
print("✅ 處理完成！")
print("="*80)
print(f"Session ID: {result['session_id']}")
print(f"Status: {result['final_status']}")
print(f"Final Score: {result['final_score']}/5.0")
print(f"Iterations: {result['iteration_count']}")
print(f"\n改寫後的問題：")
print(result['final_question'])
print("="*80)

db_session.close()
```

運行：
```bash
python test_my_pipeline.py
```

---

## 成本估算

### E2E 測試成本（使用 GPT-4o）

| 測試項目 | Token 使用 | 約略成本 | 執行時間 |
|---------|-----------|---------|---------|
| Rephrase Agent | ~3,000 tokens | $0.015 | ~15s |
| Review Agent | ~1,500 tokens | $0.008 | ~10s |
| Revise Agent | ~2,000 tokens | $0.010 | ~10s |
| Iteration Manager | ~5,000 tokens | $0.025 | ~30-60s |
| CrewAI Pipeline | ~8,000 tokens | $0.040 | ~40-80s |
| **測試所有** | ~20,000 tokens | **$0.10** | **~2-3 分鐘** |

**價格計算：**
- GPT-4o: $5/1M input tokens, $15/1M output tokens
- 平均每次測試約 $0.05 - $0.10

### 節省成本建議

1. **使用 mock 測試進行開發**（免費）
   ```bash
   pytest  # 運行所有 mock 測試
   ```

2. **只在關鍵時刻使用 E2E**
   - 重大變更前後
   - 準備 commit/push 之前
   - 需要驗證實際 LLM 效果時

3. **測試單個組件而非全部**
   ```bash
   # 只測試你修改的部分
   python scripts/test_rephrase_pipeline_e2e.py --test-crewai
   ```

---

## 故障排除

### 問題 1: `OPENAI_API_KEY not set`

```bash
# 確認設置
export OPENAI_API_KEY='sk-...'
echo $OPENAI_API_KEY

# 或在 Python 中直接設置
import os
os.environ['OPENAI_API_KEY'] = 'sk-...'
```

### 問題 2: `ModuleNotFoundError: No module named 'crewai'`

```bash
# 安裝 CrewAI
pip install crewai>=0.1.55

# 驗證
python -c "import crewai; print('OK')"
```

### 問題 3: `RateLimitError`

OpenAI API 有速率限制：
- 稍等片刻（1-2 分鐘）
- 或降低並發測試

### 問題 4: 測試超時

E2E 測試可能需要較長時間：
```bash
# 增加超時設置
pytest --timeout=300  # 5 分鐘
```

### 問題 5: 資料庫連接錯誤

CrewAI Pipeline 測試使用內存資料庫，不需要 PostgreSQL：
```python
# 腳本中使用
engine = create_engine("sqlite:///:memory:")
```

---

## 推薦測試流程

### 日常開發

```bash
# 1. 快速驗證（免費，幾秒內完成）
pytest -v

# 2. 檢查覆蓋率
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### 提交前驗證

```bash
# 1. 所有 mock 測試
pytest -v

# 2. E2E 測試 CrewAI Pipeline（重點功能）
export OPENAI_API_KEY='your-key'
python scripts/test_rephrase_pipeline_e2e.py --test-crewai

# 3. 如果通過，提交代碼
git add .
git commit -m "..."
git push
```

### 完整驗證（發布前）

```bash
# 1. 所有 mock 測試
pytest -v --cov=src

# 2. 所有 E2E 測試
export OPENAI_API_KEY='your-key'
python scripts/test_rephrase_pipeline_e2e.py --test-all

# 3. 檢查結果
# 預期：所有測試通過，總成本 ~$0.10
```

---

## 總結

- **快速驗證**: `pytest` (免費，秒級)
- **功能測試**: `python scripts/test_rephrase_pipeline_e2e.py --test-crewai` (~$0.04，1分鐘)
- **完整測試**: `python scripts/test_rephrase_pipeline_e2e.py --test-all` (~$0.10，3分鐘)

建議從 `pytest` 開始，只在需要驗證真實 LLM 效果時才使用 E2E 測試。
