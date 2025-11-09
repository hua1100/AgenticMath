# AgenticMath - 工作流程視覺化圖表

**版本**: 1.0
**最後更新**: 2025-11-09

本文件提供 AgenticMath 系統的視覺化流程圖，使用 Mermaid 語法繪製。

---

## 📊 完整系統架構圖

```mermaid
graph TB
    subgraph "輸入層"
        A[原始數學問題] --> B[複雜度提升維度]
    end

    subgraph "CrewAI Pipeline"
        B --> C[CrewAI Pipeline]
        C --> D[AgentToolkit]
    end

    subgraph "Agent 層"
        D --> E[Rephrase Agent<br/>改寫專家]
        D --> F[Review Agent<br/>品質評審]
        D --> G[Revise Agent<br/>修訂專家]
    end

    subgraph "控制層"
        E --> H[Iteration Manager<br/>迭代控制器]
        F --> H
        G --> H
    end

    subgraph "資料層"
        H --> I[(PostgreSQL/SQLite)]
        I --> J[Problems 表]
        I --> K[RephraseSession 表]
        I --> L[QualityAssessment 表]
        I --> M[AgentExecution 表]
    end

    subgraph "輸出層"
        H --> N[最終改寫問題]
        H --> O[品質評估報告]
        H --> P[會話統計資訊]
    end

    style A fill:#e1f5ff
    style N fill:#c8e6c9
    style O fill:#c8e6c9
    style P fill:#c8e6c9
    style C fill:#fff9c4
    style H fill:#ffe0b2
```

---

## 🔄 完整執行流程圖

```mermaid
flowchart TD
    Start([開始]) --> Init[初始化 CrewAI Pipeline]
    Init --> CreateSession[創建 RephraseSession]

    CreateSession --> Rephrase[執行 Rephrase Agent]
    Rephrase --> ParseRephrase{解析成功?}

    ParseRephrase -->|否| RephraseError[拋出異常]
    ParseRephrase -->|是| SaveRephrased[保存改寫問題<br/>source=REPHRASED]

    SaveRephrased --> InitIteration[初始化迭代計數器<br/>N = 1]

    InitIteration --> LoopStart{開始迭代循環}

    LoopStart --> Review[執行 Review Agent]
    Review --> ParseReview{解析成功?}

    ParseReview -->|否| ReviewError[拋出異常]
    ParseReview -->|是| SaveAssessment[保存 QualityAssessment]

    SaveAssessment --> CheckScore{評分 >= 4.5?}

    CheckScore -->|是| Success[狀態: SUCCESS]
    CheckScore -->|否| CheckIterations{N < 3?}

    CheckIterations -->|否| MaxIter[狀態: MAX_ITERATIONS_EXCEEDED]
    CheckIterations -->|是| CheckSuggestions{有改進建議?}

    CheckSuggestions -->|否| WarnNoSuggestions[記錄警告]
    CheckSuggestions -->|是| Revise[執行 Revise Agent]

    WarnNoSuggestions --> IncrementN[N = N + 1]

    Revise --> ParseRevise{解析成功?}
    ParseRevise -->|否| ReviseError[拋出異常]
    ParseRevise -->|是| SaveRevised[保存修訂問題<br/>source=REVISED]

    SaveRevised --> IncrementN
    IncrementN --> LoopStart

    Success --> FinalizeSession[完成 RephraseSession]
    MaxIter --> FinalizeSession

    FinalizeSession --> ReturnResult[返回結果]
    ReturnResult --> End([結束])

    RephraseError --> ErrorHandler[錯誤處理]
    ReviewError --> ErrorHandler
    ReviseError --> ErrorHandler
    ErrorHandler --> End

    style Start fill:#4caf50,color:#fff
    style End fill:#4caf50,color:#fff
    style Success fill:#66bb6a,color:#fff
    style MaxIter fill:#ffa726
    style RephraseError fill:#ef5350,color:#fff
    style ReviewError fill:#ef5350,color:#fff
    style ReviseError fill:#ef5350,color:#fff
    style ErrorHandler fill:#ef5350,color:#fff
```

---

## 🎯 狀態機圖（RephraseSession）

```mermaid
stateDiagram-v2
    [*] --> INITIALIZED: 創建會話

    INITIALIZED --> REPHRASING: 開始改寫

    REPHRASING --> REVIEWING: 改寫完成
    REPHRASING --> ERROR: 改寫失敗

    REVIEWING --> QUALITY_CHECK: 評分完成
    REVIEWING --> ERROR: 評審失敗

    QUALITY_CHECK --> SUCCESS: score >= 4.5
    QUALITY_CHECK --> REVISING: score < 4.5 且 N < 3
    QUALITY_CHECK --> MAX_ITERATIONS: N >= 3

    REVISING --> REVIEWING: 修訂完成
    REVISING --> ERROR: 修訂失敗

    SUCCESS --> COMPLETED: 保存結果
    MAX_ITERATIONS --> COMPLETED: 保存結果

    ERROR --> FAILED: 記錄異常

    COMPLETED --> [*]: 正常結束
    FAILED --> [*]: 異常退出

    note right of QUALITY_CHECK
        品質門檻: 4.5/5.0
        最大迭代: 3 次
    end note

    note right of SUCCESS
        final_status = SUCCESS
        iteration_count = N
    end note

    note right of MAX_ITERATIONS
        final_status = MAX_ITERATIONS_EXCEEDED
        iteration_count = 3
    end note
```

---

## 🔁 迭代循環詳細流程

```mermaid
sequenceDiagram
    participant PM as Pipeline Manager
    participant IM as Iteration Manager
    participant RA as Review Agent
    participant VA as Revise Agent
    participant DB as Database

    PM->>IM: 啟動迭代（改寫問題）

    loop 迭代循環 (最多3次)
        IM->>RA: 評估當前問題
        RA->>RA: LLM 推理
        RA->>DB: 保存 QualityAssessment
        RA-->>IM: 返回評分 + 建議

        alt 評分 >= 4.5
            IM-->>PM: ✅ 成功（問題達標）
        else 迭代次數 >= 3
            IM-->>PM: ⚠️ 超過最大迭代次數
        else 沒有改進建議
            IM->>IM: 記錄警告
            IM->>IM: N = N + 1
        else 繼續修訂
            IM->>VA: 修訂問題（建議列表）
            VA->>VA: LLM 推理
            VA->>DB: 保存修訂問題
            VA-->>IM: 返回修訂結果
            IM->>IM: N = N + 1
        end
    end

    PM->>DB: 更新 RephraseSession
    PM->>PM: 返回最終結果
```

---

## 📦 資料模型關聯圖

```mermaid
erDiagram
    RephraseSession ||--|| Problem : "original_problem_id"
    RephraseSession ||--o| Problem : "final_problem_id"
    RephraseSession ||--o{ AgentExecution : "session_id"

    Problem ||--o| Problem : "parent_id (自關聯)"
    Problem ||--o{ QualityAssessment : "problem_id"
    Problem ||--o{ Solution : "problem_id"
    Problem ||--o| UploadedImage : "uploaded_image_id"

    RephraseSession {
        uuid id PK
        uuid original_problem_id FK
        uuid final_problem_id FK
        json escalation_dimensions
        int iteration_count
        float quality_threshold
        enum final_status
        timestamp created_at
        timestamp completed_at
    }

    Problem {
        uuid id PK
        text content
        enum domain
        json competencies
        int baseline_difficulty
        enum source
        enum source_type
        uuid parent_id FK
        uuid uploaded_image_id FK
        timestamp created_at
    }

    QualityAssessment {
        uuid id PK
        uuid problem_id FK
        float clarity_grammar_score
        float logical_coherence_score
        float mathematical_validity_score
        float overall_score
        text thought_process
        json suggestions
        timestamp created_at
    }

    AgentExecution {
        uuid id PK
        enum agent_type
        uuid session_id FK
        json input_data
        json output_data
        text prompt_template
        text raw_llm_response
        int execution_time_ms
        string llm_model
        timestamp created_at
    }
```

---

## 🧩 Agent 協作時序圖

```mermaid
sequenceDiagram
    participant User as 用戶/測試腳本
    participant Pipeline as CrewAI Pipeline
    participant Toolkit as AgentToolkit
    participant Rephrase as Rephrase Agent
    participant Review as Review Agent
    participant Revise as Revise Agent
    participant LLM as OpenAI GPT-4o
    participant DB as Database

    User->>Pipeline: process(problem, dimensions)
    Pipeline->>DB: 創建 RephraseSession

    Note over Pipeline,Toolkit: 階段 1: 改寫
    Pipeline->>Toolkit: 執行 Rephrase
    Toolkit->>Rephrase: rephrase(problem, dimensions)
    Rephrase->>LLM: 呼叫 GPT-4o（改寫提示詞）
    LLM-->>Rephrase: 返回改寫結果（Raw JSON）
    Rephrase->>Rephrase: 解析 RephraseOutput
    Rephrase->>DB: 保存 Problem (REPHRASED)
    Rephrase->>DB: 保存 AgentExecution
    Rephrase-->>Toolkit: 返回 RephraseOutput
    Toolkit-->>Pipeline: 返回改寫問題

    Note over Pipeline,Revise: 階段 2: 迭代循環
    loop 最多 3 次迭代
        Pipeline->>Review: review(rephrased_problem)
        Review->>LLM: 呼叫 GPT-4o（評審提示詞）
        LLM-->>Review: 返回評分 + 建議
        Review->>Review: 解析 ReviewOutput
        Review->>DB: 保存 QualityAssessment
        Review->>DB: 保存 AgentExecution
        Review-->>Pipeline: 返回評估結果

        alt 評分 >= 4.5
            Pipeline->>Pipeline: 結束迭代（成功）
        else 迭代次數 < 3
            Pipeline->>Revise: revise(problem, suggestions)
            Revise->>LLM: 呼叫 GPT-4o（修訂提示詞）
            LLM-->>Revise: 返回修訂問題
            Revise->>Revise: 解析 ReviseOutput
            Revise->>DB: 保存 Problem (REVISED)
            Revise->>DB: 保存 AgentExecution
            Revise-->>Pipeline: 返回修訂問題
        else 迭代次數 >= 3
            Pipeline->>Pipeline: 結束迭代（超過次數）
        end
    end

    Note over Pipeline,DB: 階段 3: 完成會話
    Pipeline->>DB: 更新 RephraseSession（final_status, iteration_count）
    Pipeline-->>User: 返回最終結果
```

---

## 🎨 複雜度提升維度應用流程

```mermaid
flowchart LR
    subgraph "輸入"
        A[原始問題<br/>難度 = 2]
        B[維度清單:<br/>1. Multi-stage<br/>2. Real-world<br/>3. Conditional]
    end

    A --> C{Rephrase Agent}
    B --> C

    subgraph "改寫分析"
        C --> D[Stage 1:<br/>問題解構]
        D --> E[Stage 2:<br/>維度應用]
        E --> F[Stage 3:<br/>問題重構]
    end

    F --> G[改寫問題<br/>預期難度 = 3.5]

    G --> H{驗證}

    H -->|格式正確| I[✅ 通過]
    H -->|格式錯誤| J[❌ 失敗]

    I --> K[保存到資料庫]
    J --> L[拋出異常]

    style A fill:#e3f2fd
    style G fill:#c8e6c9
    style I fill:#a5d6a7
    style J fill:#ef9a9a
```

---

## 📊 品質評分流程圖

```mermaid
flowchart TD
    Start[開始評審] --> Input[接收改寫問題]

    Input --> Analyze[分析三個維度]

    Analyze --> Clarity[評估文法與清晰度<br/>score_1 = 1.0-5.0]
    Analyze --> Logic[評估邏輯連貫性<br/>score_2 = 1.0-5.0]
    Analyze --> Math[評估數學有效性<br/>score_3 = 1.0-5.0]

    Clarity --> Aggregate[計算整體評分]
    Logic --> Aggregate
    Math --> Aggregate

    Aggregate --> Overall[overall_score =<br/>avg score_1, score_2, score_3]

    Overall --> CheckThreshold{score >= 4.5?}

    CheckThreshold -->|是| Pass[✅ 通過<br/>無需修訂]
    CheckThreshold -->|否| Suggestions[生成改進建議清單]

    Pass --> SavePass[保存評估<br/>suggestions = []]
    Suggestions --> SaveFail[保存評估<br/>suggestions = [建議1, 建議2...]]

    SavePass --> Return[返回評估結果]
    SaveFail --> Return

    Return --> End[結束]

    style Pass fill:#66bb6a,color:#fff
    style Suggestions fill:#ffa726
```

---

## 🔧 LLM API 呼叫與重試流程

```mermaid
flowchart TD
    Start[呼叫 LLM API] --> Try[嘗試 API 請求<br/>attempt = 1]

    Try --> Success{成功?}

    Success -->|是| Parse[解析 JSON 回應]
    Success -->|否| CheckError{錯誤類型?}

    CheckError -->|RateLimitError<br/>429| Wait1[等待 2^attempt 秒]
    CheckError -->|APIError<br/>500/503| Wait1
    CheckError -->|Timeout| Wait1
    CheckError -->|其他錯誤| FinalError[拋出異常]

    Wait1 --> CheckAttempt{attempt < 3?}

    CheckAttempt -->|是| Retry[attempt = attempt + 1]
    CheckAttempt -->|否| FinalError

    Retry --> Try

    Parse --> Return[返回 LLM 回應]
    Return --> End[結束]

    FinalError --> End

    style Success fill:#81c784
    style FinalError fill:#e57373,color:#fff
    style Return fill:#66bb6a,color:#fff
```

---

## 📈 測試執行流程圖

```mermaid
flowchart TD
    Start([開始測試]) --> Setup[設置內存資料庫]
    Setup --> InitLLM[初始化 LLM Client]
    InitLLM --> InitPipeline[初始化 CrewAI Pipeline]

    InitPipeline --> CreateProblems[創建 5 個測試問題]

    CreateProblems --> Loop{遍歷每個問題}

    Loop --> ProcessOne[處理問題 N/5]
    ProcessOne --> Execute[執行 Pipeline.process]

    Execute --> CheckStatus{狀態?}

    CheckStatus -->|SUCCESS| RecordSuccess[✅ 記錄成功<br/>保存評分 + 結果]
    CheckStatus -->|MAX_ITERATIONS| RecordFail[❌ 記錄失敗<br/>保存評分 + 結果]
    CheckStatus -->|ERROR| RecordError[❌ 記錄錯誤<br/>保存異常訊息]

    RecordSuccess --> TrackCost[追蹤 Tokens 與成本]
    RecordFail --> TrackCost
    RecordError --> TrackCost

    TrackCost --> CheckMore{還有問題?}

    CheckMore -->|是| Loop
    CheckMore -->|否| Summary[生成測試摘要]

    Summary --> DisplayResults[顯示結果表格:<br/>- 成功/失敗統計<br/>- 評分分布<br/>- 總成本]

    DisplayResults --> End([結束測試])

    style RecordSuccess fill:#66bb6a,color:#fff
    style RecordFail fill:#ffa726
    style RecordError fill:#ef5350,color:#fff
```

---

## 🗂️ 資料流轉示意圖

```mermaid
flowchart LR
    subgraph "輸入數據"
        A1[原始問題文字]
        A2[數學領域]
        A3[基礎難度]
        A4[複雜度維度]
    end

    subgraph "Rephrase 處理"
        B1[Prompt 構建]
        B2[LLM 推理]
        B3[輸出解析]
        B4[格式驗證]
    end

    subgraph "資料庫寫入 1"
        C1[(Problem<br/>REPHRASED)]
        C2[(AgentExecution<br/>REPHRASE)]
    end

    subgraph "Review 處理"
        D1[Prompt 構建]
        D2[LLM 推理]
        D3[評分解析]
    end

    subgraph "資料庫寫入 2"
        E1[(QualityAssessment)]
        E2[(AgentExecution<br/>REVIEW)]
    end

    subgraph "Revise 處理"
        F1[Prompt 構建]
        F2[LLM 推理]
        F3[輸出解析]
    end

    subgraph "資料庫寫入 3"
        G1[(Problem<br/>REVISED)]
        G2[(AgentExecution<br/>REVISE)]
    end

    subgraph "最終輸出"
        H1[最終問題]
        H2[品質評分]
        H3[迭代次數]
        H4[會話狀態]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1

    B1 --> B2 --> B3 --> B4

    B4 --> C1
    B4 --> C2

    C1 --> D1 --> D2 --> D3

    D3 --> E1
    D3 --> E2

    E1 --> F1 --> F2 --> F3

    F3 --> G1
    F3 --> G2

    G1 --> H1
    E1 --> H2
    G2 --> H3
    G2 --> H4

    style C1 fill:#bbdefb
    style C2 fill:#bbdefb
    style E1 fill:#c5e1a5
    style E2 fill:#c5e1a5
    style G1 fill:#ffccbc
    style G2 fill:#ffccbc
    style H1 fill:#c8e6c9
    style H2 fill:#c8e6c9
    style H3 fill:#c8e6c9
    style H4 fill:#c8e6c9
```

---

## 🎭 Agent 角色互動圖

```mermaid
graph TB
    subgraph "Rephrase Agent - 改寫專家"
        R1[接收原始問題]
        R2[分析問題結構]
        R3[應用複雜度維度]
        R4[生成改寫問題]
        R1 --> R2 --> R3 --> R4
    end

    subgraph "Review Agent - 品質評審"
        V1[接收改寫問題]
        V2[評估三個維度]
        V3[計算整體評分]
        V4[生成改進建議]
        V1 --> V2 --> V3 --> V4
    end

    subgraph "Revise Agent - 修訂專家"
        E1[接收問題 + 建議]
        E2[分析改進方向]
        E3[修正問題內容]
        E4[輸出修訂問題]
        E1 --> E2 --> E3 --> E4
    end

    R4 -->|改寫問題| V1
    V4 -->|評分 + 建議| Decision{評分 >= 4.5?}
    Decision -->|否| E1
    Decision -->|是| Success[✅ 完成]
    E4 -->|修訂問題| V1

    style R4 fill:#e1f5fe
    style V3 fill:#fff9c4
    style E4 fill:#ffe0b2
    style Success fill:#c8e6c9
```

---

**文件結束**

這些圖表可以在支援 Mermaid 的環境中渲染，例如：
- GitHub Markdown
- GitLab Markdown
- VS Code (with Mermaid extension)
- Obsidian
- Mermaid Live Editor (https://mermaid.live)
