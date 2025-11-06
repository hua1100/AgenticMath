# Workflow State Machine: Photo Upload → OCR → Multi-Agent Pipeline

**版本**: 1.0.0
**最後更新**: 2025-11-06
**相關文件**: [spec.md](./spec.md), [data-model.md](./data-model.md), [contracts/image-extraction-agent.md](./contracts/image-extraction-agent.md)

## 概述

本文件定義從學生上傳照片到生成最終解答的完整工作流程狀態機。系統採用線性流水線架構，每個階段由不同的 Agent 負責，透過狀態轉換確保資料完整性和錯誤處理。

## 狀態定義

### 核心狀態 (Core States)

| 狀態代碼 | 狀態名稱 | 說明 | 可轉換至 |
|---------|---------|------|---------|
| `UPLOADED` | 已上傳 | 照片已上傳，等待驗證 | `VALIDATED`, `UPLOAD_FAILED` |
| `VALIDATED` | 已驗證 | 檔案格式、大小驗證通過 | `OCR_PROCESSING`, `VALIDATION_FAILED` |
| `OCR_PROCESSING` | OCR 處理中 | PaddleOCR 正在提取文字 | `OCR_COMPLETED`, `OCR_FAILED` |
| `OCR_COMPLETED` | OCR 完成 | 文字提取成功，等待建立 Problem | `PROBLEM_CREATED`, `OCR_LOW_CONFIDENCE` |
| `PROBLEM_CREATED` | 問題已建立 | Original Problem 實體已建立 | `REPHRASING` |
| `REPHRASING` | 改寫中 | Rephrase Agent 正在生成新題目 | `REPHRASE_COMPLETED`, `REPHRASE_FAILED` |
| `REPHRASE_COMPLETED` | 改寫完成 | Rephrased Problem 已生成 | `REVIEWING` |
| `REVIEWING` | 審查中 | Review Agent 正在評估品質 | `REVIEW_COMPLETED`, `REVIEW_FAILED` |
| `REVIEW_COMPLETED` | 審查完成 | 品質評估完成 | `REVISING`, `SOLVING` |
| `REVISING` | 修訂中 | Revise Agent 正在改進題目 | `REVISE_COMPLETED`, `REVISE_FAILED` |
| `REVISE_COMPLETED` | 修訂完成 | 題目已改進，重新審查 | `REVIEWING` |
| `SOLVING` | 求解中 | Solver Agent 正在生成解答 | `COMPLETED`, `SOLVING_FAILED` |
| `COMPLETED` | 完成 | 整個流程成功完成 | - |

### 錯誤狀態 (Error States)

| 狀態代碼 | 狀態名稱 | 說明 | 恢復動作 |
|---------|---------|------|---------|
| `UPLOAD_FAILED` | 上傳失敗 | 檔案上傳過程中斷 | 要求重新上傳 |
| `VALIDATION_FAILED` | 驗證失敗 | 檔案格式或大小不符 | 提示錯誤訊息，要求重新上傳 |
| `OCR_FAILED` | OCR 失敗 | OCR 引擎錯誤或無法辨識 | 記錄錯誤，要求重新拍攝 |
| `OCR_LOW_CONFIDENCE` | OCR 低信心度 | 辨識信心度 < 70% | 標記警告，繼續處理或要求確認 |
| `REPHRASE_FAILED` | 改寫失敗 | LLM API 錯誤或輸出格式錯誤 | 重試 (最多 3 次) 或人工介入 |
| `REVIEW_FAILED` | 審查失敗 | Review Agent 執行錯誤 | 重試或跳過審查 |
| `REVISE_FAILED` | 修訂失敗 | Revise Agent 執行錯誤 | 使用上一版本題目 |
| `SOLVING_FAILED` | 求解失敗 | Solver Agent 執行錯誤 | 重試或標記為未完成 |
| `MAX_ITERATIONS_EXCEEDED` | 超過最大迭代次數 | Review-Revise 循環 > 5 次 | 使用當前最佳版本 |

## 完整狀態轉換圖

```
[學生上傳照片]
      ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Photo Upload & OCR (User Story 0)                 │
└─────────────────────────────────────────────────────────────┘
      ↓
  UPLOADED ────────────────→ UPLOAD_FAILED (終止)
      ↓
  [檔案驗證]
      ↓
  VALIDATED ────────────────→ VALIDATION_FAILED (終止)
      ↓
  OCR_PROCESSING
      ↓
      ├─→ OCR_FAILED (終止)
      ├─→ OCR_LOW_CONFIDENCE (警告但繼續)
      ↓
  OCR_COMPLETED
      ↓
  [創建 Problem 實體]
      ↓
  PROBLEM_CREATED
      ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Problem Rephrase & Quality Control (User Story 1) │
└─────────────────────────────────────────────────────────────┘
      ↓
  REPHRASING ────────────────→ REPHRASE_FAILED (重試或終止)
      ↓
  REPHRASE_COMPLETED
      ↓
  REVIEWING ─────────────────→ REVIEW_FAILED (重試或跳過)
      ↓
  REVIEW_COMPLETED
      ↓
  [檢查品質分數]
      ↓
      ├─→ score ≥ 4.5 ─────→ [通過審查]
      │                           ↓
      │                       SOLVING
      │
      ├─→ score < 4.5 ─────→ [需要修訂]
      │                           ↓
      │                       REVISING ───→ REVISE_FAILED (使用當前版本)
      │                           ↓
      │                       REVISE_COMPLETED
      │                           ↓
      │                       [iteration_count++]
      │                           ↓
      │                       ├─→ iteration_count ≤ 5 ───→ REVIEWING (循環)
      │                       │
      │                       └─→ iteration_count > 5 ───→ MAX_ITERATIONS_EXCEEDED
      │                                                         ↓
      │                                                    [使用當前最佳版本]
      │                                                         ↓
      └─────────────────────────────────────────────────→ SOLVING
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Solution Generation (User Story 2)                │
└─────────────────────────────────────────────────────────────┘
      ↓
  SOLVING ───────────────────→ SOLVING_FAILED (重試或標記未完成)
      ↓
  COMPLETED
      ↓
  [返回結果給學生]
```

## 狀態轉換規則

### Rule 1: Photo Upload & Validation

```python
def handle_photo_upload(image_file: UploadFile) -> State:
    """
    處理照片上傳和驗證

    State transitions:
    - Success: UPLOADED → VALIDATED → OCR_PROCESSING
    - Failure: UPLOADED → UPLOAD_FAILED (network error)
    - Failure: VALIDATED → VALIDATION_FAILED (invalid format/size)
    """
    state = State.UPLOADED

    try:
        # 驗證檔案
        if not validate_file_format(image_file):
            return State.VALIDATION_FAILED

        if not validate_file_size(image_file):
            return State.VALIDATION_FAILED

        state = State.VALIDATED

        # 儲存檔案
        file_path = save_uploaded_file(image_file)

        # 觸發 OCR 處理
        state = State.OCR_PROCESSING

    except Exception as e:
        log_error(f"Upload failed: {e}")
        return State.UPLOAD_FAILED

    return state
```

### Rule 2: OCR Processing

```python
def handle_ocr_processing(uploaded_image: UploadedImage) -> State:
    """
    處理 OCR 文字提取

    State transitions:
    - Success (high confidence): OCR_PROCESSING → OCR_COMPLETED → PROBLEM_CREATED
    - Success (low confidence): OCR_PROCESSING → OCR_LOW_CONFIDENCE → PROBLEM_CREATED
    - Failure: OCR_PROCESSING → OCR_FAILED
    """
    state = State.OCR_PROCESSING

    try:
        # 執行 OCR (參見 contracts/image-extraction-agent.md)
        ocr_result = image_extraction_agent.process({
            "image_id": uploaded_image.id,
            "file_path": uploaded_image.file_path,
            "file_format": uploaded_image.file_format,
            "file_size": uploaded_image.file_size
        })

        if not ocr_result["success"]:
            log_error(f"OCR failed: {ocr_result.get('error_message')}")
            return State.OCR_FAILED

        # 檢查信心度
        confidence = ocr_result["confidence_score"]

        if confidence < 0.50:
            # 信心度過低，拒絕處理
            return State.OCR_FAILED

        if confidence < 0.70:
            # 信心度偏低，發出警告但繼續處理
            state = State.OCR_LOW_CONFIDENCE
            log_warning(f"Low OCR confidence: {confidence:.2f}")
        else:
            state = State.OCR_COMPLETED

        # 創建 Problem 實體
        problem = create_problem_from_ocr(ocr_result, uploaded_image.id)

        return State.PROBLEM_CREATED

    except Exception as e:
        log_error(f"OCR processing error: {e}")
        return State.OCR_FAILED
```

### Rule 3: Rephrase Agent

```python
def handle_rephrase(problem: Problem) -> State:
    """
    處理問題改寫

    State transitions:
    - Success: REPHRASING → REPHRASE_COMPLETED → REVIEWING
    - Failure: REPHRASING → REPHRASE_FAILED (retry or terminate)
    """
    state = State.REPHRASING
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # 執行 Rephrase Agent (參見 contracts/rephrase-agent.md)
            rephrase_result = rephrase_agent.process({
                "problem_content": problem.content,
                "domain": problem.domain,
                "competencies": problem.competencies,
                "difficulty": problem.difficulty
            })

            # 創建 Rephrased Problem
            rephrased_problem = create_rephrased_problem(rephrase_result, problem.id)

            state = State.REPHRASE_COMPLETED

            # 自動轉換到 REVIEWING
            return State.REVIEWING

        except Exception as e:
            log_error(f"Rephrase attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return State.REPHRASE_FAILED

            # 重試前等待指數退避
            time.sleep(2 ** attempt)

    return State.REPHRASE_FAILED
```

### Rule 4: Review-Revise Loop

```python
def handle_review_revise_loop(rephrased_problem: Problem, session: RephraseSession) -> State:
    """
    處理審查-修訂循環

    State transitions:
    - Quality ≥ 4.5: REVIEW_COMPLETED → SOLVING
    - Quality < 4.5 and iterations < 5: REVIEW_COMPLETED → REVISING → REVISE_COMPLETED → REVIEWING
    - Quality < 4.5 and iterations ≥ 5: REVIEW_COMPLETED → MAX_ITERATIONS_EXCEEDED → SOLVING
    """
    state = State.REVIEWING
    current_problem = rephrased_problem
    iteration_count = 0
    max_iterations = 5
    quality_threshold = 4.5

    while iteration_count < max_iterations:
        try:
            # 執行 Review Agent (參見 contracts/review-agent.md)
            review_result = review_agent.process({
                "problem_content": current_problem.content,
                "original_problem_content": session.original_problem.content,
                "domain": current_problem.domain
            })

            state = State.REVIEW_COMPLETED

            # 儲存品質評估
            assessment = create_quality_assessment(review_result, current_problem.id)

            # 檢查品質分數
            if assessment.overall_score >= quality_threshold:
                log_info(f"Quality passed: {assessment.overall_score:.2f}")
                return State.SOLVING

            log_info(f"Quality below threshold: {assessment.overall_score:.2f}, revising...")

            # 需要修訂
            state = State.REVISING
            iteration_count += 1

            # 執行 Revise Agent (參見 contracts/revise-agent.md)
            revise_result = revise_agent.process({
                "problem_content": current_problem.content,
                "review_feedback": review_result["suggestions"],
                "quality_scores": review_result["rating_scores"]
            })

            state = State.REVISE_COMPLETED

            # 更新 Problem
            current_problem = update_problem_with_revision(current_problem, revise_result)

            # 更新 Session
            update_session_iteration(session, iteration_count)

            # 回到 REVIEWING
            state = State.REVIEWING

        except Exception as e:
            log_error(f"Review-Revise loop error at iteration {iteration_count}: {e}")
            # 使用當前最佳版本繼續
            break

    # 超過最大迭代次數
    if iteration_count >= max_iterations:
        log_warning(f"Max iterations exceeded: {iteration_count}")
        state = State.MAX_ITERATIONS_EXCEEDED

    # 使用當前版本繼續到 Solver
    return State.SOLVING
```

### Rule 5: Solution Generation

```python
def handle_solution_generation(problem: Problem) -> State:
    """
    處理解答生成

    State transitions:
    - Success: SOLVING → COMPLETED
    - Failure: SOLVING → SOLVING_FAILED (retry or terminate)
    """
    state = State.SOLVING
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # 執行 Solver Agent (參見 contracts/solver-agent.md)
            solver_result = solver_agent.process({
                "problem_content": problem.content,
                "domain": problem.domain,
                "difficulty": problem.difficulty
            })

            # 儲存解答
            solution = create_solution(solver_result, problem.id)

            state = State.COMPLETED

            log_info(f"Solution generated successfully for problem {problem.id}")

            return state

        except Exception as e:
            log_error(f"Solution generation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return State.SOLVING_FAILED

            # 重試前等待
            time.sleep(2 ** attempt)

    return State.SOLVING_FAILED
```

## 狀態持久化

所有狀態轉換必須持久化到資料庫，確保系統重啟後可以恢復處理：

### AgentExecution 狀態記錄

```python
class AgentExecution(BaseModel):
    """記錄每個 Agent 的執行狀態"""
    id: UUID
    agent_type: AgentType  # OCR, REPHRASE, REVIEW, REVISE, SOLVER
    status: ExecutionStatus  # PENDING, RUNNING, COMPLETED, FAILED
    start_time: datetime
    end_time: Optional[datetime]

    # 狀態轉換記錄
    previous_state: Optional[str]  # 執行前的狀態
    current_state: str  # 執行後的狀態

    # 錯誤處理
    error_message: Optional[str]
    retry_count: int = 0
```

### RephraseSession 狀態追蹤

```python
class RephraseSession(BaseModel):
    """追蹤整個 Rephrase 流程的狀態"""
    id: UUID
    current_state: str  # 當前所在狀態
    iteration_count: int = 0  # Review-Revise 循環次數

    # 狀態歷史
    state_history: List[StateTransition] = []

    # 完成標記
    is_completed: bool = False
    completed_at: Optional[datetime] = None

class StateTransition(BaseModel):
    """狀態轉換記錄"""
    from_state: str
    to_state: str
    timestamp: datetime
    triggered_by: str  # Agent 名稱或系統事件
    metadata: Dict[str, Any] = {}  # 額外資訊（如品質分數、錯誤訊息等）
```

## 錯誤處理策略

### 1. 可重試錯誤 (Retryable Errors)

- **REPHRASE_FAILED**: 重試 3 次（指數退避：2s, 4s, 8s）
- **REVIEW_FAILED**: 重試 2 次，若仍失敗則跳過審查直接進入 SOLVING
- **REVISE_FAILED**: 不重試，使用上一版本 Problem
- **SOLVING_FAILED**: 重試 3 次，若仍失敗則標記為未完成但保留其他結果

### 2. 不可重試錯誤 (Non-Retryable Errors)

- **UPLOAD_FAILED**: 要求學生重新上傳
- **VALIDATION_FAILED**: 提示具體錯誤訊息（格式不支援、檔案過大等）
- **OCR_FAILED** (信心度 < 50%): 要求重新拍攝更清晰的照片
- **MAX_ITERATIONS_EXCEEDED**: 使用當前最佳版本，記錄警告

### 3. 降級處理 (Graceful Degradation)

- **OCR_LOW_CONFIDENCE** (50% ≤ 信心度 < 70%): 標記警告但繼續處理，最終結果標註「OCR 信心度較低，建議人工檢查」
- **REVIEW_FAILED**: 跳過品質審查，直接使用改寫結果
- **REVISE_FAILED**: 使用修訂前的版本

## 監控和日誌

### 關鍵監控指標

```python
class WorkflowMetrics:
    """工作流程監控指標"""

    # 整體流程
    total_photos_uploaded: int
    successful_completions: int
    failed_completions: int
    average_processing_time_seconds: float

    # 各階段成功率
    ocr_success_rate: float
    rephrase_success_rate: float
    review_pass_rate: float  # 首次審查通過率
    average_revise_iterations: float
    solver_success_rate: float

    # 錯誤統計
    ocr_failures: int
    rephrase_failures: int
    max_iterations_exceeded_count: int

    # 效能指標
    average_ocr_time_ms: float
    average_rephrase_time_ms: float
    average_review_time_ms: float
    average_solve_time_ms: float
```

### 日誌記錄規範

```python
# 狀態轉換日誌
logger.info(
    "State transition",
    extra={
        "session_id": session.id,
        "from_state": previous_state,
        "to_state": current_state,
        "triggered_by": agent_type,
        "duration_ms": duration,
        "metadata": {
            "quality_score": score,
            "iteration": iteration_count
        }
    }
)

# 錯誤日誌
logger.error(
    "Agent execution failed",
    extra={
        "session_id": session.id,
        "agent_type": agent_type,
        "current_state": current_state,
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "retry_count": retry_count
    }
)
```

## 測試場景

### Scenario 1: Happy Path (所有步驟成功)

```
UPLOADED → VALIDATED → OCR_PROCESSING → OCR_COMPLETED → PROBLEM_CREATED
  → REPHRASING → REPHRASE_COMPLETED → REVIEWING → REVIEW_COMPLETED (score = 4.7)
  → SOLVING → COMPLETED

預期時間: <60 秒
```

### Scenario 2: One Revision Needed (需要一次修訂)

```
... → REVIEW_COMPLETED (score = 4.2) → REVISING → REVISE_COMPLETED
  → REVIEWING → REVIEW_COMPLETED (score = 4.6) → SOLVING → COMPLETED

預期時間: <90 秒
```

### Scenario 3: Max Iterations (超過最大迭代次數)

```
... → REVIEW_COMPLETED (score = 4.3) → REVISING → REVISE_COMPLETED
  → REVIEWING → REVIEW_COMPLETED (score = 4.4) → REVISING → ...
  (重複 5 次)
  → MAX_ITERATIONS_EXCEEDED → SOLVING → COMPLETED

預期時間: <180 秒
警告: "Quality threshold not reached after 5 iterations, using best available version"
```

### Scenario 4: OCR Low Confidence (低信心度但繼續)

```
UPLOADED → VALIDATED → OCR_PROCESSING → OCR_LOW_CONFIDENCE (confidence = 0.68)
  → PROBLEM_CREATED → REPHRASING → ... → COMPLETED

警告: "OCR confidence below 70%, manual verification recommended"
```

### Scenario 5: OCR Failure (OCR 失敗)

```
UPLOADED → VALIDATED → OCR_PROCESSING → OCR_FAILED

終止原因: "No text detected in image"
建議: "Please retake a clearer photo"
```

### Scenario 6: Rephrase Failure with Retry (改寫失敗但重試成功)

```
... → PROBLEM_CREATED → REPHRASING (嘗試 1 失敗) → REPHRASING (嘗試 2 失敗)
  → REPHRASING (嘗試 3 成功) → REPHRASE_COMPLETED → ...

記錄: "Rephrase succeeded after 3 attempts"
```

## 並發處理

系統支援多個照片同時處理，每個照片的處理流程獨立：

```python
class WorkflowOrchestrator:
    """工作流程編排器"""

    async def process_photo(self, image_file: UploadFile) -> str:
        """
        異步處理單張照片

        Returns:
            session_id: 用於追蹤處理進度
        """
        # 創建新的 Session
        session = create_rephrase_session()

        # 異步執行完整流程
        asyncio.create_task(
            self._execute_full_pipeline(image_file, session)
        )

        return str(session.id)

    async def _execute_full_pipeline(self, image_file: UploadFile, session: RephraseSession):
        """執行完整流水線"""
        try:
            # Phase 1: Upload & OCR
            uploaded_image = await self._handle_upload(image_file)
            session.current_state = State.OCR_PROCESSING

            ocr_result = await self._handle_ocr(uploaded_image)
            session.current_state = State.OCR_COMPLETED

            problem = await self._create_problem(ocr_result, uploaded_image.id)
            session.current_state = State.PROBLEM_CREATED
            session.original_problem_id = problem.id

            # Phase 2: Rephrase & Quality Control
            rephrased_problem = await self._handle_rephrase(problem)
            session.current_state = State.REPHRASE_COMPLETED
            session.rephrased_problem_id = rephrased_problem.id

            final_problem = await self._handle_review_revise_loop(rephrased_problem, session)

            # Phase 3: Solution Generation
            session.current_state = State.SOLVING
            solution = await self._handle_solution(final_problem)

            # 完成
            session.current_state = State.COMPLETED
            session.is_completed = True
            session.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Pipeline failed for session {session.id}: {e}")
            session.current_state = self._determine_error_state(e)
            session.is_completed = False
```

## 狀態查詢 API

```python
@app.get("/sessions/{session_id}/status")
async def get_session_status(session_id: UUID) -> SessionStatus:
    """
    查詢工作流程當前狀態

    Returns:
        SessionStatus: {
            session_id: UUID,
            current_state: str,
            progress_percentage: int (0-100),
            iteration_count: int,
            estimated_completion_time: Optional[datetime],
            is_completed: bool,
            has_errors: bool,
            error_message: Optional[str]
        }
    """
    session = get_session_by_id(session_id)

    # 計算進度百分比
    progress = calculate_progress(session.current_state)

    # 估算完成時間
    estimated_time = estimate_completion_time(session)

    return {
        "session_id": session.id,
        "current_state": session.current_state,
        "progress_percentage": progress,
        "iteration_count": session.iteration_count,
        "estimated_completion_time": estimated_time,
        "is_completed": session.is_completed,
        "has_errors": session.current_state in ERROR_STATES,
        "error_message": get_error_message(session)
    }

def calculate_progress(current_state: str) -> int:
    """根據當前狀態計算進度百分比"""
    progress_map = {
        State.UPLOADED: 5,
        State.VALIDATED: 10,
        State.OCR_PROCESSING: 15,
        State.OCR_COMPLETED: 20,
        State.PROBLEM_CREATED: 25,
        State.REPHRASING: 35,
        State.REPHRASE_COMPLETED: 45,
        State.REVIEWING: 55,
        State.REVIEW_COMPLETED: 65,
        State.REVISING: 70,
        State.REVISE_COMPLETED: 75,
        State.SOLVING: 85,
        State.COMPLETED: 100
    }
    return progress_map.get(current_state, 0)
```

---

**版本歷史**:
- v1.0.0 (2025-11-06): 初始版本，定義完整狀態機和轉換規則
