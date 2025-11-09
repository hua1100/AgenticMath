# AgenticMath - Agent 運作流程說明

**版本**: 1.0
**最後更新**: 2025-11-09
**語言**: 繁體中文

---

## 📋 目錄

1. [系統架構概覽](#系統架構概覽)
2. [Agent 角色與職責](#agent-角色與職責)
3. [完整工作流程](#完整工作流程)
4. [資訊流動圖](#資訊流動圖)
5. [狀態機模型](#狀態機模型)
6. [CrewAI Pipeline 實作](#crewai-pipeline-實作)
7. [錯誤處理與重試機制](#錯誤處理與重試機制)

---

## 🏗️ 系統架構概覽

AgenticMath 使用 **CrewAI 框架**組織多 Agent 協作，實現數學問題的自動複雜度提升。

### 核心組件

```
┌─────────────────────────────────────────────────────────────┐
│                    CrewAI Pipeline                          │
│  (src/orchestration/crewai_pipeline.py)                     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Rephrase     │  │ Review       │  │ Revise       │
│ Agent        │  │ Agent        │  │ Agent        │
│ (改寫專家)    │  │ (品質評審)    │  │ (修訂專家)    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            ▼
                  ┌──────────────────┐
                  │ Iteration        │
                  │ Manager          │
                  │ (迭代控制器)      │
                  └──────────────────┘
```

### 技術棧

- **框架**: CrewAI 0.86.0
- **LLM**: OpenAI GPT-4o
- **資料庫**: PostgreSQL (生產) / SQLite (測試)
- **ORM**: SQLAlchemy
- **語言**: Python 3.11+

---

## 👥 Agent 角色與職責

### 1. Rephrase Agent (改寫專家)

**角色定位**: 專精於提升數學問題複雜度的教育專家

**核心職責**:
- 分析原始數學問題的結構與難度
- 根據指定的複雜度提升維度改寫問題
- 保持數學嚴謹性與可解性
- 輸出結構化的改寫結果

**輸入**:
```python
{
    "original_problem": "原始問題文字",
    "domain": "GEOMETRY",  # 數學領域
    "baseline_difficulty": 2,  # 基礎難度 1-5
    "escalation_dimensions": [  # 複雜度提升維度
        "Multi-stage Transformation",
        "Real-world Parameterization",
        "Conditional Branching"
    ]
}
```

**輸出**:
```python
{
    "rephrased_problem": "改寫後的問題",
    "reasoning": "改寫推理過程",
    "applied_dimensions": [
        "Multi-stage Transformation",
        "Real-world Parameterization"
    ],
    "expected_difficulty": 3.5
}
```

**提示詞模板**: `src/prompts/rephrase_prompt.py`
**實作檔案**: `src/agents/rephrase_agent.py`

---

### 2. Review Agent (品質評審)

**角色定位**: 數學問題品質檢查專家

**核心職責**:
- 評估改寫問題的品質（1.0-5.0 分）
- 檢查文法清晰度、邏輯連貫性、數學有效性
- 提供具體改進建議
- 決定問題是否達到品質門檻（預設 4.5 分）

**評分標準**:
| 維度 | 分數範圍 | 說明 |
|-----|---------|------|
| **文法與清晰度** | 1.0-5.0 | 語句是否通順、無歧義 |
| **邏輯連貫性** | 1.0-5.0 | 推理步驟是否合理 |
| **數學有效性** | 1.0-5.0 | 數學內容是否正確、可解 |
| **整體評分** | 1.0-5.0 | 加權平均分數 |

**輸入**:
```python
{
    "rephrased_problem": "改寫後的問題",
    "original_problem": "原始問題（用於對比）",
    "escalation_dimensions": ["維度清單"]
}
```

**輸出**:
```python
{
    "clarity_grammar_score": 4.5,
    "logical_coherence_score": 4.8,
    "mathematical_validity_score": 5.0,
    "overall_score": 4.7,
    "thought_process": "詳細評估推理",
    "suggestions": [
        "建議1：補充邊界條件說明",
        "建議2：簡化計算步驟表述"
    ]
}
```

**提示詞模板**: `src/prompts/review_prompt.py`
**實作檔案**: `src/agents/review_agent.py`

---

### 3. Revise Agent (修訂專家)

**角色定位**: 根據評審意見進行問題修訂的專家

**核心職責**:
- 接收 Review Agent 的改進建議
- 針對性修正問題中的不足
- 保持問題的核心意圖不變
- 確保每次修訂都有實質改進

**輸入**:
```python
{
    "rephrased_problem": "待修訂的問題",
    "review_feedback": {
        "overall_score": 4.2,
        "suggestions": ["建議清單"]
    }
}
```

**輸出**:
```python
{
    "revised_problem": "修訂後的問題",
    "revision_notes": "本次修訂重點說明"
}
```

**提示詞模板**: `src/prompts/revise_prompt.py`
**實作檔案**: `src/agents/revise_agent.py`

---

## 🔄 完整工作流程

### 階段 1: 問題改寫（Rephrase）

```mermaid
graph LR
    A[原始問題] --> B[Rephrase Agent]
    B --> C[改寫後問題]
    C --> D[解析與驗證]
    D --> E{格式正確?}
    E -->|是| F[繼續]
    E -->|否| G[拋出異常]
```

**詳細步驟**:
1. **接收輸入**: 原始問題 + 複雜度提升維度
2. **LLM 推理**: GPT-4o 根據提示詞生成改寫結果
3. **結果解析**: 使用正則表達式提取結構化數據
4. **格式驗證**:
   - 檢查問題是否以 `?` 或 `？` 結尾
   - 檢查是否包含中文疑問詞（求、計算、問等）
   - 驗證至少應用 3 個複雜度維度
5. **保存到資料庫**: 創建 `Problem` 記錄（source=REPHRASED）

**執行時間**: 約 3-5 秒
**成本**: 約 500-800 tokens

---

### 階段 2: 品質審查與迭代改進（Review-Revise Loop）

```mermaid
stateDiagram-v2
    [*] --> Reviewing
    Reviewing --> CheckScore: 評分完成
    CheckScore --> Success: 分數 ≥ 4.5
    CheckScore --> CheckIteration: 分數 < 4.5
    CheckIteration --> Revising: 迭代 < 3
    CheckIteration --> MaxIterations: 迭代 ≥ 3
    Revising --> Reviewing: 修訂完成
    Success --> [*]
    MaxIterations --> [*]
```

**迭代控制器**（`src/orchestration/iteration_manager.py`）:
- **品質門檻**: 4.5/5.0（可配置）
- **最大迭代次數**: 3 次（可配置）
- **退出條件**:
  - ✅ **成功**: 整體評分 ≥ 4.5
  - ❌ **超過次數**: 迭代次數達到 3 次仍未達標
  - ⚠️ **無改進建議**: Review Agent 未提供具體建議

**單次迭代流程**:
```
第 N 次迭代:
1. Review Agent 評估當前問題
   ├─ 輸出: overall_score, suggestions
   └─ 保存 QualityAssessment 到資料庫

2. 判斷分數
   ├─ score ≥ 4.5 → 返回成功
   └─ score < 4.5 → 繼續

3. 檢查建議
   ├─ suggestions 為空 → 記錄警告，繼續
   └─ suggestions 有內容 → 執行修訂

4. Revise Agent 修訂問題
   ├─ 輸入: 當前問題 + suggestions
   └─ 輸出: revised_problem

5. N = N + 1，返回步驟 1
```

**執行時間**: 每次迭代約 5-8 秒
**成本**: 每次迭代約 400-600 tokens

---

### 階段 3: 結果保存與會話完成

```python
# 創建最終問題記錄
final_problem = Problem(
    content=revised_problem,
    source=ProblemSource.REVISED,
    parent_id=original_problem.id,
    ...
)

# 更新 RephraseSession
session.final_problem_id = final_problem.id
session.final_status = SessionStatus.SUCCESS  # 或 MAX_ITERATIONS_EXCEEDED
session.iteration_count = N
session.completed_at = datetime.utcnow()
```

---

## 📊 資訊流動圖

### 完整資料流

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 輸入階段                                                       │
│                                                                   │
│  原始問題 (Problem)                                               │
│  ├─ content: "在直角三角形ABC中..."                               │
│  ├─ domain: GEOMETRY                                             │
│  ├─ baseline_difficulty: 1                                       │
│  └─ source: ORIGINAL                                             │
│                                                                   │
│  複雜度維度 (List[str])                                           │
│  ├─ "Multi-stage Transformation"                                │
│  ├─ "Real-world Parameterization"                               │
│  └─ "Conditional Branching"                                     │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Rephrase 階段                                                 │
│                                                                   │
│  CrewAI Task: rephrase_task                                      │
│  ├─ Agent: rephrase_agent                                       │
│  ├─ Input: original_problem + dimensions                        │
│  └─ Output: rephrased_output (RephraseOutput)                   │
│                                                                   │
│  創建記錄:                                                        │
│  ├─ Problem (source=REPHRASED)                                  │
│  └─ AgentExecution (agent_type=REPHRASE)                        │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Review-Revise 迭代階段                                        │
│                                                                   │
│  Iteration 1:                                                    │
│  ├─ Review Agent                                                │
│  │   ├─ Input: rephrased_problem                               │
│  │   ├─ Output: QualityAssessment (score=4.2)                  │
│  │   └─ 保存: quality_assessments 表                            │
│  │                                                              │
│  ├─ 判斷: 4.2 < 4.5 → 需要修訂                                  │
│  │                                                              │
│  └─ Revise Agent                                                │
│      ├─ Input: problem + suggestions                            │
│      ├─ Output: revised_problem                                 │
│      └─ 保存: Problem (source=REVISED)                          │
│                                                                   │
│  Iteration 2:                                                    │
│  ├─ Review Agent → QualityAssessment (score=4.8)                │
│  └─ 判斷: 4.8 ≥ 4.5 → 成功！                                    │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 輸出階段                                                       │
│                                                                   │
│  RephraseSession                                                 │
│  ├─ original_problem_id: uuid1                                  │
│  ├─ final_problem_id: uuid2                                     │
│  ├─ final_status: SUCCESS                                       │
│  ├─ iteration_count: 2                                          │
│  ├─ quality_threshold: 4.5                                      │
│  └─ completed_at: 2025-11-09 12:34:56                           │
│                                                                   │
│  返回結果 (Dict):                                                 │
│  ├─ "status": "success"                                         │
│  ├─ "final_problem": Problem object                             │
│  ├─ "quality_score": 4.8                                        │
│  ├─ "iteration_count": 2                                        │
│  └─ "session": RephraseSession object                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 狀態機模型

### RephraseSession 狀態轉移

```mermaid
stateDiagram-v2
    [*] --> INITIALIZED: 創建會話
    INITIALIZED --> REPHRASING: 開始改寫
    REPHRASING --> REVIEWING: 改寫完成

    REVIEWING --> QUALITY_CHECK: 評分完成

    QUALITY_CHECK --> SUCCESS: score ≥ 4.5
    QUALITY_CHECK --> REVISING: score < 4.5 且 iteration < 3
    QUALITY_CHECK --> MAX_ITERATIONS: iteration ≥ 3

    REVISING --> REVIEWING: 修訂完成

    SUCCESS --> COMPLETED: 保存結果
    MAX_ITERATIONS --> COMPLETED: 保存結果

    REPHRASING --> ERROR: 改寫失敗
    REVIEWING --> ERROR: 評審失敗
    REVISING --> ERROR: 修訂失敗

    ERROR --> [*]: 異常退出
    COMPLETED --> [*]: 正常結束
```

### SessionStatus 枚舉值

| 狀態 | 值 | 說明 |
|-----|---|------|
| **SUCCESS** | `"success"` | 問題品質達標（≥ 4.5） |
| **MAX_ITERATIONS_EXCEEDED** | `"max_iterations_exceeded"` | 達到最大迭代次數 |
| **ERROR** | `"error"` | 發生異常錯誤 |

---

## 🚀 CrewAI Pipeline 實作

### 核心類別: `CrewAIPipeline`

**檔案位置**: `src/orchestration/crewai_pipeline.py`

```python
class CrewAIPipeline:
    """CrewAI-based pipeline for math problem escalation workflow."""

    def __init__(self, db_session: Session, llm_client: LLMClient):
        self.db = db_session
        self.toolkit = AgentToolkit(db_session, llm_client)

    def process(
        self,
        original_problem: Problem,
        escalation_dimensions: List[str],
        quality_threshold: float = 4.5,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        執行完整的問題改寫與品質迭代流程。

        Returns:
            {
                "status": "success" | "max_iterations_exceeded" | "error",
                "final_problem": Problem,
                "quality_score": float,
                "iteration_count": int,
                "session": RephraseSession
            }
        """
```

### AgentToolkit: Agent 封裝工具集

```python
class AgentToolkit:
    """Wrapper toolkit to use existing agents with CrewAI."""

    def __init__(self, db_session: Session, llm_client: LLMClient):
        self.rephrase_agent = RephraseAgent(db_session, llm_client)
        self.review_agent = ReviewAgent(db_session, llm_client)
        self.revise_agent = ReviseAgent(db_session, llm_client)

    # 將現有 Agent 包裝成 CrewAI 可用的工具
```

### 執行範例

```python
from src.orchestration.crewai_pipeline import CrewAIPipeline

# 初始化
pipeline = CrewAIPipeline(db_session, llm_client)

# 執行處理
result = pipeline.process(
    original_problem=problem,
    escalation_dimensions=[
        "Multi-stage Transformation",
        "Real-world Parameterization",
        "Conditional Branching"
    ],
    quality_threshold=4.5,
    max_iterations=3
)

# 檢查結果
if result["status"] == "success":
    print(f"✅ 成功！最終評分: {result['quality_score']:.2f}")
    print(f"改寫後問題: {result['final_problem'].content}")
else:
    print(f"❌ 失敗：{result['status']}")
```

---

## ⚠️ 錯誤處理與重試機制

### LLM API 重試策略

**檔案**: `src/llm/llm_client.py`

```python
class LLMClient:
    def call_llm(self, messages: List[Dict], max_retries: int = 3) -> str:
        """
        呼叫 LLM API，包含自動重試機制。

        重試條件:
        - RateLimitError (429): 等待並重試
        - APIError (500, 503): 重試
        - Timeout: 重試

        退避策略: 指數退避 (2^n 秒)
        """
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(...)
                return response.choices[0].message.content
            except RateLimitError:
                sleep(2 ** attempt)
            except APIError:
                sleep(2 ** attempt)
```

### 解析錯誤處理

**檔案**: `src/parsers/*.py`

```python
class RephraseParser:
    def parse(self, raw_response: str) -> RephraseOutput:
        """
        解析 LLM 回應，包含多重回退策略。

        回退策略:
        1. 嘗試標準格式解析（編號列表）
        2. 嘗試無冒號格式
        3. 關鍵字匹配
        4. 返回預設值（空列表 + 警告）
        """
        try:
            # 嘗試解析...
        except Exception as e:
            logger.warning(f"解析失敗: {e}")
            # 返回降級結果
```

### 迭代異常處理

**檔案**: `src/orchestration/iteration_manager.py`

```python
class IterationManager:
    def iterate_until_quality(self, ...) -> IterationResult:
        """
        錯誤處理:
        1. Review Agent 失敗 → 拋出異常
        2. Revise Agent 失敗 → 拋出異常
        3. 無改進建議 → 記錄警告，繼續迭代
        4. 達到最大次數 → 返回當前最佳結果
        """
```

---

## 📈 效能指標

### 典型執行時間

| 階段 | 時間範圍 | 說明 |
|-----|---------|------|
| Rephrase | 3-5 秒 | 取決於問題長度 |
| Review | 2-3 秒 | 評估較快 |
| Revise | 3-4 秒 | 需要修改問題 |
| **總計（1 次迭代）** | 8-12 秒 | 不含 LLM 隊列等待 |
| **總計（3 次迭代）** | 20-30 秒 | 最壞情況 |

### 成本估算（GPT-4o）

| 操作 | Tokens | 成本（美元） |
|-----|--------|------------|
| Rephrase | 500-800 | $0.005-$0.008 |
| Review | 300-500 | $0.003-$0.005 |
| Revise | 400-600 | $0.004-$0.006 |
| **完整流程（1 次迭代）** | 1200-1900 | $0.012-$0.019 |
| **完整流程（3 次迭代）** | 2400-3800 | $0.024-$0.038 |

*成本基於 GPT-4o 定價（2025 年）：輸入 $0.01/1K tokens，輸出 $0.03/1K tokens*

---

## 🗄️ 資料庫結構

### 核心資料表

#### 1. `problems` 表

儲存所有階段的問題（原始/改寫/修訂）

```sql
CREATE TABLE problems (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    domain VARCHAR(50) NOT NULL,  -- GEOMETRY, ALGEBRA, etc.
    competencies JSON NOT NULL,   -- ["trigonometry", ...]
    baseline_difficulty INTEGER NOT NULL,
    source VARCHAR(20) NOT NULL,  -- ORIGINAL, REPHRASED, REVISED
    source_type VARCHAR(20) NOT NULL,  -- OCR, MANUAL_TEXT
    parent_id UUID REFERENCES problems(id),
    created_at TIMESTAMP NOT NULL
);
```

#### 2. `rephrase_sessions` 表

追蹤完整的改寫會話

```sql
CREATE TABLE rephrase_sessions (
    id UUID PRIMARY KEY,
    original_problem_id UUID REFERENCES problems(id),
    final_problem_id UUID REFERENCES problems(id),
    escalation_dimensions JSON NOT NULL,
    iteration_count INTEGER NOT NULL,
    quality_threshold FLOAT NOT NULL,
    final_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);
```

#### 3. `quality_assessments` 表

儲存每次品質評估結果

```sql
CREATE TABLE quality_assessments (
    id UUID PRIMARY KEY,
    problem_id UUID REFERENCES problems(id),
    clarity_grammar_score FLOAT NOT NULL,
    logical_coherence_score FLOAT NOT NULL,
    mathematical_validity_score FLOAT NOT NULL,
    overall_score FLOAT NOT NULL,
    thought_process TEXT NOT NULL,
    suggestions JSON NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

#### 4. `agent_executions` 表

記錄每次 Agent 執行（完整可追溯性）

```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(20) NOT NULL,  -- REPHRASE, REVIEW, REVISE
    session_id UUID REFERENCES rephrase_sessions(id),
    input_data JSON NOT NULL,
    output_data JSON NOT NULL,
    prompt_template TEXT NOT NULL,
    raw_llm_response TEXT,
    execution_time_ms INTEGER NOT NULL,
    llm_model VARCHAR(100),
    created_at TIMESTAMP NOT NULL
);
```

### 資料關聯圖

```
rephrase_sessions
├─ original_problem_id → problems (原始問題)
├─ final_problem_id → problems (最終問題)
└─ agent_executions (多次執行記錄)

problems
├─ parent_id → problems (改寫/修訂來源)
└─ quality_assessments (品質評估記錄)
```

---

## 🔧 配置與自訂

### 環境變數

```bash
# 必要
OPENAI_API_KEY=sk-...

# 可選
DATABASE_URL=postgresql://user:pass@localhost/agenticmath
LOG_LEVEL=INFO
```

### Pipeline 參數調整

```python
# src/orchestration/crewai_pipeline.py

# 品質門檻（預設 4.5）
quality_threshold=4.5  # 範圍: 1.0-5.0

# 最大迭代次數（預設 3）
max_iterations=3  # 建議: 2-5

# LLM 模型（預設 gpt-4o）
llm_client = LLMClient(model="gpt-4o")

# LLM 溫度（預設 0.7）
temperature=0.7  # 範圍: 0.0-1.0
```

### 複雜度提升維度

可用的維度清單（`research.md`）:

1. **Multi-stage Transformation** - 多階段轉換
2. **Real-world Parameterization** - 真實世界參數化
3. **Conditional Branching** - 條件分支
4. **Cross-domain Integration** - 跨領域整合
5. **Inverse Problem Design** - 反向問題設計
6. **Optimization Extension** - 最佳化延伸
7. **Proof Requirement** - 證明要求

---

## 📚 參考資源

### 相關檔案

| 檔案 | 用途 |
|-----|------|
| `src/orchestration/crewai_pipeline.py` | CrewAI Pipeline 主實作 |
| `src/orchestration/iteration_manager.py` | 迭代控制邏輯 |
| `src/agents/rephrase_agent.py` | Rephrase Agent |
| `src/agents/review_agent.py` | Review Agent |
| `src/agents/revise_agent.py` | Revise Agent |
| `src/prompts/*.py` | Agent 提示詞模板 |
| `src/parsers/*.py` | LLM 輸出解析器 |
| `src/models/*.py` | 資料庫模型定義 |

### 測試腳本

| 腳本 | 用途 |
|-----|------|
| `test_single_trigonometry.py` | 快速測試單一問題 |
| `test_trigonometry_pipeline.py` | 批次測試 5 個問題 |
| `scripts/test_rephrase_pipeline_e2e.py` | E2E 完整測試 |

---

## 🐛 常見問題排查

### 問題 1: "No suggestions provided, but score below threshold"

**症狀**: Review Agent 給低分但沒有建議
**原因**: LLM 輸出格式不符合預期
**解決**:
1. 檢查 `src/parsers/review_parser.py` 的解析邏輯
2. 查看 `agent_executions.raw_llm_response` 欄位
3. 調整提示詞模板 `src/prompts/review_prompt.py`

### 問題 2: SQLite UUID 錯誤

**症狀**: `Compiler can't render element of type UUID`
**原因**: SQLite 不支援 PostgreSQL UUID 類型
**解決**: 已修復，使用 `GUID` 類型（`src/models/types.py`）

### 問題 3: 改寫問題未應用足夠維度

**症狀**: 警告 "Only 0 dimensions applied"
**原因**: 解析器無法識別 LLM 輸出的維度名稱
**解決**: 檢查 `src/parsers/rephrase_parser.py` 的關鍵字列表

---

## 📞 支援與反饋

如有問題或建議，請聯繫專案維護團隊。

---

**文件結束**
