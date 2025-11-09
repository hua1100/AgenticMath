# AgenticMath - 快速開始指南

**版本**: 1.0
**語言**: 繁體中文

---

## 🚀 5 分鐘快速開始

### 1. 環境準備

```bash
# 安裝依賴
pip install -r requirements.txt

# 設置 OpenAI API Key
export OPENAI_API_KEY='sk-your-api-key-here'

# 設置資料庫（開發環境）
export DATABASE_URL='sqlite:///agenticmath.db'
```

### 2. 運行測試

```bash
# 快速測試單一問題
python test_single_trigonometry.py

# 批次測試 5 個問題
python test_trigonometry_pipeline.py

# E2E 完整測試
python scripts/test_rephrase_pipeline_e2e.py
```

### 3. 查看結果

測試完成後，你會看到：
- ✅ 成功/失敗狀態
- 📊 品質評分（1.0-5.0）
- 🔄 迭代次數
- 💰 API 使用成本

---

## 📝 基本使用範例

### 範例 1: 使用 CrewAI Pipeline

```python
from src.orchestration.crewai_pipeline import CrewAIPipeline
from src.llm.llm_client import LLMClient
from src.models.problem import Problem, MathDomain, ProblemSource, SourceType
from uuid import uuid4

# 1. 初始化
llm_client = LLMClient(model="gpt-4o", temperature=0.7)
pipeline = CrewAIPipeline(db_session, llm_client)

# 2. 創建原始問題
original_problem = Problem(
    id=uuid4(),
    content="求解方程式 x² + 5x + 6 = 0",
    domain=MathDomain.ALGEBRA,
    competencies=["quadratic_equations"],
    baseline_difficulty=2,
    source=ProblemSource.ORIGINAL,
    source_type=SourceType.MANUAL_TEXT,
)
db_session.add(original_problem)
db_session.commit()

# 3. 執行 Pipeline
result = pipeline.process(
    original_problem=original_problem,
    escalation_dimensions=[
        "Multi-stage Transformation",
        "Real-world Parameterization",
        "Conditional Branching"
    ],
    quality_threshold=4.5,
    max_iterations=3
)

# 4. 檢查結果
if result["status"] == "success":
    print(f"✅ 成功！")
    print(f"最終問題: {result['final_problem'].content}")
    print(f"品質評分: {result['quality_score']:.2f}/5.0")
    print(f"迭代次數: {result['iteration_count']}")
else:
    print(f"❌ 失敗: {result['status']}")
```

### 範例 2: 單獨使用各個 Agent

```python
from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from src.agents.revise_agent import ReviseAgent

# 初始化 Agents
rephrase_agent = RephraseAgent(db_session, llm_client)
review_agent = ReviewAgent(db_session, llm_client)
revise_agent = ReviseAgent(db_session, llm_client)

# 改寫問題
rephrase_output = rephrase_agent.rephrase(
    original_problem=problem,
    escalation_dimensions=["Multi-stage Transformation"]
)

# 評審問題
review_output = review_agent.review(
    rephrased_problem=rephrase_output.rephrased_problem,
    original_problem=problem,
    escalation_dimensions=["Multi-stage Transformation"]
)

# 如果評分不足，修訂問題
if review_output.overall_score < 4.5:
    revise_output = revise_agent.revise(
        rephrased_problem=rephrase_output.rephrased_problem,
        review_feedback=review_output
    )
```

---

## 🎯 複雜度提升維度說明

### 可用的維度清單

| 維度 | 英文名稱 | 說明 | 適用領域 |
|-----|---------|------|---------|
| **多階段轉換** | Multi-stage Transformation | 將單步驟問題擴展為多步驟計算 | 所有領域 |
| **真實世界參數化** | Real-world Parameterization | 引入實際情境參數（距離、時間、成本等） | 幾何、代數 |
| **條件分支** | Conditional Branching | 添加條件判斷（如果...則...） | 所有領域 |
| **跨領域整合** | Cross-domain Integration | 結合多個數學領域（幾何+代數） | 進階問題 |
| **反向問題設計** | Inverse Problem Design | 將求解改為證明或推導 | 數論、幾何 |
| **最佳化延伸** | Optimization Extension | 添加最大值/最小值問題 | 微積分、幾何 |
| **證明要求** | Proof Requirement | 要求嚴格的數學證明 | 進階問題 |

### 維度選擇建議

```python
# 基礎問題（難度 1-2）：建議 3 個維度
dimensions = [
    "Multi-stage Transformation",
    "Real-world Parameterization",
    "Conditional Branching"
]

# 中級問題（難度 3-4）：建議 3-4 個維度
dimensions = [
    "Multi-stage Transformation",
    "Cross-domain Integration",
    "Conditional Branching",
    "Optimization Extension"
]

# 進階問題（難度 5）：建議 4-5 個維度
dimensions = [
    "Multi-stage Transformation",
    "Cross-domain Integration",
    "Inverse Problem Design",
    "Proof Requirement",
    "Optimization Extension"
]
```

---

## ⚙️ 配置選項

### Pipeline 參數

```python
result = pipeline.process(
    original_problem=problem,
    escalation_dimensions=dimensions,

    # 品質門檻（預設 4.5）
    quality_threshold=4.5,  # 範圍: 1.0-5.0

    # 最大迭代次數（預設 3）
    max_iterations=3  # 建議: 2-5
)
```

### LLM Client 參數

```python
llm_client = LLMClient(
    model="gpt-4o",           # 模型名稱
    temperature=0.7,          # 創造性（0.0-1.0）
    max_retries=3,            # API 重試次數
    timeout=30                # 請求超時（秒）
)
```

### 資料庫配置

```python
# PostgreSQL（生產環境）
DATABASE_URL = "postgresql://user:password@localhost:5432/agenticmath"

# SQLite（測試環境）
DATABASE_URL = "sqlite:///agenticmath.db"

# SQLite 內存（測試腳本）
DATABASE_URL = "sqlite:///:memory:"
```

---

## 📊 測試結果解讀

### 成功案例

```
✅ 處理完成！

📊 結果：
   狀態：success
   最終評分：5.0/5.0
   迭代次數：1
   執行時間：10.2 秒

📝 改寫後的問題：
   [改寫後的問題內容...]

💰 本次成本：
   Tokens: 2,242
   成本: $0.0188
```

**解讀**:
- ✅ `status: success` - 問題品質達標（≥ 4.5）
- 🎯 `最終評分: 5.0` - 完美評分
- 🔄 `迭代次數: 1` - 第一次改寫就達標
- ⏱️ `執行時間: 10.2 秒` - 正常速度
- 💰 `成本: $0.0188` - 約 2 美分

### 失敗案例

```
❌ 處理完成！

📊 結果：
   狀態：max_iterations_exceeded
   最終評分：4.0/5.0
   迭代次數：1
   執行時間：12.3 秒
```

**解讀**:
- ❌ `status: max_iterations_exceeded` - 未達品質門檻
- ⚠️ `最終評分: 4.0` - 低於 4.5 門檻
- 🔄 `迭代次數: 1` - 可能因為沒有改進建議而提前結束

**可能原因**:
1. Review Agent 未提供改進建議（日誌顯示 "No suggestions provided"）
2. 品質門檻設置過高
3. 改寫維度與問題不匹配

---

## 🐛 常見問題與解決方案

### 問題 1: AttributeError: 'LLMClient' object has no attribute 'estimated_cost'

**錯誤訊息**:
```
AttributeError: 'LLMClient' object has no attribute 'estimated_cost'
```

**原因**: 屬性名稱錯誤
**解決方案**:
```python
# ❌ 錯誤
print(llm_client.estimated_cost)

# ✅ 正確
print(llm_client.total_cost_usd)
```

---

### 問題 2: Compiler can't render element of type UUID

**錯誤訊息**:
```
sqlalchemy.exc.CompileError: Compiler can't render element of type UUID
```

**原因**: SQLite 不支援 PostgreSQL UUID 類型
**解決方案**: 已修復！使用 `GUID` 類型（`src/models/types.py`）

---

### 問題 3: No suggestions provided, but score below threshold

**警告訊息**:
```
No suggestions provided at iteration 1, but score below threshold
```

**原因**: Review Agent 給低分但沒提供改進建議
**影響**: 迭代提前結束，狀態為 `max_iterations_exceeded`

**解決方案**:
1. **檢查 Review Agent 輸出**:
   ```sql
   SELECT raw_llm_response
   FROM agent_executions
   WHERE agent_type = 'REVIEW'
   ORDER BY created_at DESC
   LIMIT 1;
   ```

2. **調整提示詞**: 修改 `src/prompts/review_prompt.py`，強調必須提供建議

3. **降低品質門檻**:
   ```python
   result = pipeline.process(
       ...,
       quality_threshold=4.0  # 從 4.5 降到 4.0
   )
   ```

---

### 問題 4: ModuleNotFoundError: No module named 'src'

**錯誤訊息**:
```
ModuleNotFoundError: No module named 'src'
```

**原因**: Python 找不到 `src` 模組
**解決方案**: 在腳本開頭添加：
```python
import sys
from pathlib import Path

project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

---

### 問題 5: OpenAI API Rate Limit

**錯誤訊息**:
```
openai.error.RateLimitError: Rate limit exceeded
```

**原因**: API 請求過於頻繁
**解決方案**: LLM Client 已內建重試機制（指數退避），無需手動處理

如果仍然失敗，可以：
1. 增加重試次數: `LLMClient(max_retries=5)`
2. 降低並發測試數量
3. 升級 OpenAI API 方案

---

## 📁 檔案結構說明

```
AgenticMath/
├── src/
│   ├── orchestration/
│   │   ├── crewai_pipeline.py      # CrewAI Pipeline 主實作
│   │   └── iteration_manager.py     # 迭代控制邏輯
│   ├── agents/
│   │   ├── rephrase_agent.py       # Rephrase Agent
│   │   ├── review_agent.py         # Review Agent
│   │   └── revise_agent.py         # Revise Agent
│   ├── prompts/
│   │   ├── rephrase_prompt.py      # 改寫提示詞（繁體中文）
│   │   ├── review_prompt.py        # 評審提示詞（繁體中文）
│   │   └── revise_prompt.py        # 修訂提示詞（繁體中文）
│   ├── parsers/
│   │   ├── rephrase_parser.py      # 改寫輸出解析器
│   │   ├── review_parser.py        # 評審輸出解析器
│   │   └── revise_parser.py        # 修訂輸出解析器
│   ├── models/
│   │   ├── types.py                # GUID 類型定義
│   │   ├── problem.py              # Problem 模型
│   │   ├── rephrase_session.py     # RephraseSession 模型
│   │   ├── quality_assessment.py   # QualityAssessment 模型
│   │   └── agent_execution.py      # AgentExecution 模型
│   └── llm/
│       └── llm_client.py           # LLM API 封裝
├── tests/
│   └── integration/
│       └── test_crewai_pipeline.py  # CrewAI 整合測試
├── scripts/
│   └── test_rephrase_pipeline_e2e.py # E2E 測試腳本
├── docs/
│   ├── AGENT_WORKFLOW_ZH.md        # 詳細工作流程說明
│   ├── WORKFLOW_DIAGRAMS_ZH.md     # 視覺化流程圖
│   └── QUICK_START_ZH.md           # 快速開始指南（本文件）
├── test_single_trigonometry.py      # 單一問題測試
└── test_trigonometry_pipeline.py    # 批次測試腳本
```

---

## 💡 最佳實踐

### 1. 選擇合適的複雜度維度

- **DO**: 根據問題類型選擇相關維度
  ```python
  # 幾何問題
  dimensions = ["Multi-stage Transformation", "Real-world Parameterization"]

  # 代數問題
  dimensions = ["Conditional Branching", "Multi-stage Transformation"]
  ```

- **DON'T**: 強行套用不相關的維度
  ```python
  # ❌ 基礎算術問題不適合"證明要求"
  dimensions = ["Proof Requirement"]
  ```

### 2. 設置合理的品質門檻

- **DO**: 根據問題難度調整門檻
  ```python
  # 基礎問題：較高門檻
  quality_threshold=4.5

  # 複雜問題：適度降低
  quality_threshold=4.0
  ```

- **DON'T**: 設置過高或過低的門檻
  ```python
  quality_threshold=4.9  # ❌ 太高，很難達成
  quality_threshold=3.0  # ❌ 太低，品質無保證
  ```

### 3. 合理設置迭代次數

- **DO**: 根據重要性設置迭代次數
  ```python
  # 正式題庫：允許多次迭代
  max_iterations=5

  # 快速測試：減少迭代
  max_iterations=2
  ```

### 4. 監控 API 成本

```python
# 在批次處理前估算成本
estimated_problems = 100
avg_tokens_per_problem = 2000
estimated_cost = (estimated_problems * avg_tokens_per_problem) * 0.00001
print(f"預估成本: ${estimated_cost:.2f}")

# 設置成本上限
if llm_client.total_cost_usd > 10.0:
    print("⚠️ 成本超過上限，停止處理")
    break
```

### 5. 記錄與追蹤

```python
# 保存測試結果到 JSON
import json

results = {
    "timestamp": datetime.utcnow().isoformat(),
    "status": result["status"],
    "score": result["quality_score"],
    "iterations": result["iteration_count"],
    "cost": llm_client.total_cost_usd
}

with open("test_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## 📞 取得協助

遇到問題？請查閱：

1. **詳細文件**: `docs/AGENT_WORKFLOW_ZH.md`
2. **流程圖**: `docs/WORKFLOW_DIAGRAMS_ZH.md`
3. **測試範例**: `test_single_trigonometry.py`
4. **整合測試**: `tests/integration/test_crewai_pipeline.py`

---

**祝使用愉快！🎉**
