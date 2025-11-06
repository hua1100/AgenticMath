# Feature Specification: Multi-Agent Math Problem Generator

**Feature Branch**: `001-multi-agent-problem-generator`
**Created**: 2025-11-06
**Status**: Draft
**Input**: User description: "學生可以上傳錯誤或概念不清楚的題目，生成概念近似，但能幫助學習者發現概念、策略或模式，明確、邏輯一致且沒有錯誤的問題"

## User Scenarios & Testing *(mandatory)*

### User Story 0 - Photo Upload and OCR Text Extraction (Priority: P0) 🎯 MVP

學生可以透過拍照上傳數學題目，系統使用 OCR 技術自動辨識照片中的文字內容（包含數學符號、公式、圖表），並將辨識結果轉換為可處理的文字格式，作為後續問題生成流程的輸入。

**為何是此優先級**：這是系統的入口點 - 學生主要透過拍照上傳題目，沒有 OCR 功能，其他所有功能都無法啟動。照片辨識必須先於問題改寫。

**獨立測試**：學生拍攝一張包含數學題目的照片 → 系統使用 PaddleOCR 提取文字 → 系統自動檢測並描述圖表（如有）→ 辨識結果作為文字輸入傳遞給 Rephrase Agent。

**驗收情境**：

1. **Given** 學生上傳一張包含印刷體繁體中文數學題目的照片，**When** 系統執行 OCR 處理，**Then** 文字辨識準確度 ≥85%，且自動傳遞給問題改寫流程

2. **Given** 學生上傳的照片包含數學公式（如 LaTeX 格式），**When** 系統執行 OCR，**Then** 數學符號和公式被正確辨識並保留在文字輸出中

3. **Given** 學生上傳的照片包含幾何圖形或圖表，**When** 系統執行 OCR，**Then** 系統檢測到圖表區域並生成圖表描述（例如「包含直角三角形，標註邊長 a, b, c」）

4. **Given** 學生上傳的照片品質不佳（模糊、傾斜、光線不足），**When** 系統預處理圖片，**Then** 自動執行圖片增強（去噪、旋轉校正、對比度調整）後再進行 OCR

5. **Given** 學生上傳的照片包含手寫數學題目，**When** 系統執行 OCR，**Then** 系統嘗試辨識手寫文字，準確度目標 ≥82%

6. **Given** OCR 辨識完成，**When** 系統準備將結果傳遞給 Rephrase Agent，**Then** 系統**不需要**顯示辨識結果給學生確認（直接自動進入改寫流程）

**MVP 範圍限制**：
- ✅ 支援繁體中文（必需）
- ❌ 不支援英文（MVP 階段暫不支援）
- ✅ 支援圖表辨識與描述（必需，圖表很重要）
- ✅ 自動流程（無需使用者確認 OCR 結果）

---

### User Story 1 - Problem Upload and Quality-Controlled Rephrasing (Priority: P1) 🎯 MVP

A student uploads a math problem they find confusing or have made mistakes on. The system analyzes the problem, increases its complexity through systematic escalation protocols, and iterates through review-revise cycles until producing a high-quality rephrased problem (quality score ≥ 4.5) that maintains conceptual similarity while helping the learner discover patterns and strategies.

**Why this priority**: This is the core value proposition - transforming problematic student questions into pedagogically effective practice problems. Without this, no other features matter.

**Independent Test**: Student submits a simple algebra problem → System returns a rephrased problem with higher complexity that passed quality review (score ≥ 4.5) → Problem maintains the same mathematical concept but with enhanced difficulty and clarity.

**Acceptance Scenarios**:

1. **Given** a student uploads "What is 2x + 3 = 11?", **When** the system processes it through Rephrase → Review → (Revise if needed) agents, **Then** it produces a problem like "A rectangle's length is 3 units more than twice its width. If the perimeter is 22 units, find the width" with quality score ≥ 4.5

2. **Given** a rephrased problem receives review score < 4.5, **When** the Revise agent processes improvement suggestions, **Then** the revised problem is re-evaluated by Review agent until score ≥ 4.5 or maximum iterations reached

3. **Given** a student uploads a problem in a specific domain (e.g., Geometry), **When** the system rephrases it, **Then** the rephrased problem preserves the core domain and competencies while increasing complexity through ≥3 escalation dimensions

4. **Given** the Review agent evaluates a rephrased problem, **When** scoring across three dimensions, **Then** it provides detailed ratings for Clarity & Grammar, Logical Coherence, and Mathematical Validity, plus specific improvement suggestions

---

### User Story 2 - Solution Generation with Chain-of-Thought Reasoning (Priority: P2)

For both original seed problems and refined rephrased problems that pass quality review, the system generates detailed, step-by-step solutions using Chain-of-Thought (CoT) reasoning that demonstrates mathematical rigor and pedagogical clarity.

**Why this priority**: Solutions are essential for learning - students need to see correct reasoning paths. However, the problem generation itself (P1) must work first before solutions add value.

**Independent Test**: Given a high-quality problem (score ≥ 4.5) → System generates solution with explicit thought process showing all intermediate steps → Solution includes final numerical answer.

**Acceptance Scenarios**:

1. **Given** a high-quality rephrased problem, **When** the Solver agent processes it, **Then** it outputs a solution with ###thought### (detailed step-by-step derivation) and ###answer### (concise final answer)

2. **Given** a problem with ambiguous wording, **When** the Solver agent analyzes it, **Then** it explicitly states its interpretation and reasoning before proceeding with calculations

3. **Given** a problem requiring multi-case analysis, **When** the Solver generates solution, **Then** it clearly lists all cases considered, shows intermediate calculations, and uses appropriate formulas for each step

4. **Given** both the original seed problem and its rephrased version, **When** solutions are generated, **Then** both problems receive detailed CoT solutions demonstrating the conceptual connection between them

---

### User Story 3 - Configurable Quality Thresholds and Complexity Control (Priority: P3)

Educators or advanced users can configure the quality score threshold (τ_rev), select specific escalation dimensions, and adjust the difficulty baseline to customize problem generation for different learning contexts.

**Why this priority**: This is an enhancement for advanced use cases. The system should work with reasonable defaults first (P1, P2) before adding configurability.

**Independent Test**: User sets custom quality threshold to 4.0 → System accepts problems with score ≥ 4.0 → User selects specific escalation dimensions (e.g., only Multi-stage Transformation and Cross-domain Integration) → System respects these constraints.

**Acceptance Scenarios**:

1. **Given** an educator sets quality threshold to 4.0, **When** problems are reviewed, **Then** only problems scoring ≥ 4.0 proceed to solution generation

2. **Given** a user specifies 2 escalation dimensions (e.g., "Multi-stage Transformation" and "Real-world Parameterization"), **When** the Rephrase agent processes a problem, **Then** it applies exactly those dimensions

3. **Given** a user sets baseline difficulty level to 3 (using Krathwohl's Cognitive Rigor Index), **When** rephrasing a problem, **Then** the target difficulty escalates appropriately from that baseline

4. **Given** different subject domains (Algebra, Geometry, Calculus), **When** problems are processed, **Then** the system correctly identifies the domain and applies domain-appropriate escalation strategies

---

### Edge Cases

#### OCR 相關邊界情況

- **照片中沒有可辨識的文字時會發生什麼？**
  - OCR 系統應返回錯誤訊息「無法辨識文字內容」，並建議學生重新拍攝更清晰的照片

- **照片包含多個題目時會發生什麼？**
  - MVP 階段系統應辨識所有文字，並將完整內容傳遞給 Rephrase Agent（由 Agent 決定如何處理多題目情況）
  - 未來可考慮加入「題目分割」功能

- **照片旋轉角度錯誤（倒置、側向）時會發生什麼？**
  - 預處理階段應自動檢測並校正旋轉角度（PaddleOCR 的 `use_angle_cls=True` 功能）

- **照片檔案過大（>10MB）時會發生什麼？**
  - 系統應在上傳前端驗證檔案大小，超過限制則壓縮或拒絕上傳

- **圖表無法自動辨識時會發生什麼？**
  - 系統應在文字輸出中標註「包含無法辨識的圖形」，並建議學生手動補充圖表描述

- **OCR 辨識準確度過低（<70%）時會發生什麼？**
  - 系統應記錄警告日誌，並標記此題目為「低信心度辨識」，但仍繼續處理（不中斷流程）

#### Agent 相關邊界情況

- **What happens when a problem is mathematically unsolvable?**
  - Review agent must detect this through "Mathematical Validity & Solvability" criterion and assign very low score, triggering Revise agent to fix contradictions

- **What happens when review-revise iterations exceed maximum attempts without reaching threshold?**
  - System should flag the problem as "Unable to achieve quality threshold" and provide diagnostic information to user

- **What happens when uploaded problem is too vague or not mathematical?**
  - Rephrase agent's Stage 1 should identify domain and competencies; if unable to identify mathematical content, system should request clarification

- **What happens when multiple valid solution paths exist?**
  - Solver agent should either: (a) show one complete solution path with note about alternatives, or (b) explicitly state "multiple valid approaches exist" in thought process

- **What happens with extremely long problems or solutions?**
  - System should handle token limits gracefully, potentially summarizing intermediate steps while preserving mathematical correctness

## Requirements *(mandatory)*

### Functional Requirements

#### Photo Upload & OCR Processing (User Story 0 - P0)
- **FR-001**: System MUST accept photo uploads in JPEG/PNG formats with maximum file size 10MB
- **FR-002**: System MUST validate uploaded images (檢查檔案格式、大小、是否包含圖像內容)
- **FR-003**: System MUST preprocess images before OCR: auto-rotation correction, noise reduction, contrast enhancement
- **FR-004**: System MUST use PaddleOCR (Apache 2.0 licensed) with Traditional Chinese language pack (`lang='chinese_cht'`)
- **FR-005**: System MUST extract text from images with ≥85% accuracy for printed Traditional Chinese text
- **FR-006**: System MUST recognize mathematical symbols and formulas (LaTeX format support)
- **FR-007**: System MUST detect and describe diagram regions in photos (e.g., "包含直角三角形，標註邊長 a, b, c")
- **FR-008**: System MUST handle handwritten Chinese text with ≥82% accuracy target
- **FR-009**: System MUST automatically pass OCR results to Rephrase Agent without requiring user confirmation
- **FR-010**: System MUST log OCR confidence scores and processing time for monitoring
- **FR-011**: System MUST store uploaded images with metadata (upload timestamp, file size, OCR confidence)
- **FR-012**: System MUST handle OCR failures gracefully with clear error messages to users

#### Problem Input & Analysis
- **FR-013**: System MUST accept text-based mathematical problems as input from students (from OCR or direct text input)
- **FR-014**: System MUST identify the mathematical domain (Algebra, Geometry, Calculus, etc.) of input problems
- **FR-015**: System MUST identify core competencies (theorems, formulas, methods) required for input problems
- **FR-016**: System MUST assess baseline difficulty using Krathwohl's Cognitive Rigor Index (Level 1-5)

#### Problem Rephrase Agent
- **FR-017**: Rephrase Agent MUST apply ≥3 complexity escalation dimensions from: Multi-stage Transformation, Cross-domain Integration, Real-world Parameterization, Conditional Branching, Inverse Problem Design, Uncertainty Integration, Optimization Extension
- **FR-018**: Rephrase Agent MUST preserve core mathematical concepts while varying surface features
- **FR-019**: Rephrase Agent MUST ensure rephrased problems are definitive mathematical problems with unique, specific answers
- **FR-020**: Rephrase Agent MUST output in structured format: Stage 1 (Problem Deconstruction), Stage 2 (Escalation Protocol), Stage 3 (Finally Rewritten question)

#### Problem Review Agent
- **FR-021**: Review Agent MUST evaluate problems on three dimensions, each scored 1-5:
  - Clarity & Grammar
  - Logical Coherence & Completeness
  - Mathematical Validity & Solvability
- **FR-022**: Review Agent MUST calculate an overall quality score (1-5) from dimension scores
- **FR-023**: Review Agent MUST generate specific, detailed improvement suggestions when score < threshold
- **FR-024**: Review Agent MUST output in structured format: ###thought###, ###rating_score###, ###suggestions###
- **FR-025**: Review Agent MUST detect mathematical contradictions (e.g., probability > 1, impossible geometric constraints) and flag them explicitly

#### Problem Revise Agent
- **FR-026**: Revise Agent MUST process improvement suggestions from Review Agent
- **FR-027**: Revise Agent MUST optimize problems to improve scores across all three quality dimensions
- **FR-028**: Revise Agent MUST output in structured format: ###revised_question###, ###revision_notes###
- **FR-029**: Revise Agent MUST preserve the original mathematical intent while addressing quality issues

#### Review-Revise Iteration Loop
- **FR-030**: System MUST iterate through Review → Revise cycles until quality score ≥ τ_rev (default: 4.5)
- **FR-031**: System MUST limit maximum review-revise iterations to prevent infinite loops (suggested: 5 iterations)
- **FR-032**: System MUST track and log all iteration attempts with scores and suggestions

#### Solution Generation Agent
- **FR-033**: Solver Agent MUST generate solutions for all problems with quality score ≥ τ_rev
- **FR-034**: Solver Agent MUST use Chain-of-Thought (CoT) reasoning showing:
  - Problem deconstruction with given data, variables, constraints, objectives
  - Clarification of any ambiguities
  - Step-by-step derivation with all intermediate calculations
  - Final calculation and answer
- **FR-035**: Solver Agent MUST output in structured format: ###thought###, ###answer###
- **FR-036**: Solver Agent MUST show all intermediate steps without skipping calculations
- **FR-037**: Solver Agent MUST list all cases/combinations for multi-case analysis problems
- **FR-038**: Solver Agent MUST generate solutions for both original seed problems and rephrased problems

#### Quality Assurance
- **FR-039**: System MUST verify that rephrased problems maintain conceptual similarity to original problems
- **FR-040**: System MUST ensure all generated problems are mathematically correct and solvable
- **FR-041**: System MUST log all agent decisions, scores, and transformations for traceability

#### Configuration (for User Story 3)
- **FR-042**: System SHOULD allow configuration of quality threshold τ_rev (default: 4.5, range: 3.0-5.0)
- **FR-043**: System SHOULD allow selection of specific escalation dimensions
- **FR-044**: System SHOULD allow configuration of baseline difficulty level

### Key Entities

- **UploadedImage**: Represents a photo uploaded by student with attributes:
  - id (unique identifier)
  - file_path (storage location of image file)
  - file_size (size in bytes)
  - file_format (JPEG/PNG)
  - upload_timestamp (when photo was uploaded)
  - ocr_extracted_text (text extracted by OCR)
  - ocr_confidence_score (0.0-1.0, average confidence from PaddleOCR)
  - contains_diagram (boolean, whether diagram detected)
  - diagram_description (text description of detected diagrams, if any)
  - preprocessing_applied (list of preprocessing steps: rotation_corrected, noise_reduced, contrast_enhanced)
  - ocr_processing_time (milliseconds taken for OCR)
  - problem_id (reference to Problem created from this image)

- **Problem**: Represents a mathematical problem with attributes:
  - id (unique identifier)
  - content (problem text)
  - domain (e.g., Algebra, Geometry, Calculus)
  - competencies (list of required concepts/methods)
  - baseline_difficulty (1-5 using Krathwohl's index)
  - source (original/rephrased/revised)
  - source_type (ocr/manual_text, indicates whether from photo or direct text)
  - parent_id (reference to original problem if rephrased)
  - uploaded_image_id (reference to UploadedImage if from photo)

- **QualityAssessment**: Represents a review evaluation with attributes:
  - problem_id (reference to Problem)
  - clarity_grammar_score (1-5)
  - logical_coherence_score (1-5)
  - mathematical_validity_score (1-5)
  - overall_score (1-5)
  - thought_process (detailed reasoning)
  - suggestions (list of improvement recommendations)
  - timestamp

- **Solution**: Represents a generated solution with attributes:
  - problem_id (reference to Problem)
  - thought_process (detailed CoT reasoning)
  - final_answer (concise numerical/analytical answer)
  - intermediate_steps (list of calculation steps)
  - timestamp

- **RephraseSession**: Represents a complete rephrase workflow with attributes:
  - original_problem_id
  - rephrased_problem_id
  - escalation_dimensions (list of applied dimensions)
  - iteration_count (number of review-revise cycles)
  - quality_assessments (list of QualityAssessment)
  - final_status (success/max_iterations_exceeded)
  - timestamp

- **Agent**: Represents an agent's execution with attributes:
  - agent_type (rephrase/review/revise/solver)
  - input (problem or suggestions)
  - output (structured response)
  - prompt_template (the prompt used)
  - execution_time
  - timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### OCR & Photo Processing (User Story 0)

- **SC-001**: OCR text extraction achieves ≥85% accuracy for printed Traditional Chinese mathematical text (measured against ground truth manual transcriptions)

- **SC-002**: OCR processing time is <3 seconds per image on CPU (including preprocessing and text extraction)

- **SC-003**: System successfully detects and describes diagrams in ≥80% of photos containing geometric figures or charts

- **SC-004**: Handwritten text recognition achieves ≥82% accuracy for clear handwriting samples

- **SC-005**: Image preprocessing correctly identifies and corrects rotation in ≥95% of tilted photos (within ±15° tolerance)

- **SC-006**: System successfully processes ≥95% of uploaded photos without errors (remaining 5% can be low-quality images that trigger graceful error handling)

#### Problem Generation & Quality (User Stories 1-3)

- **SC-007**: System successfully rephrases ≥90% of valid input problems (from OCR or manual input) into high-quality problems (score ≥ 4.5) within 5 review-revise iterations

- **SC-008**: Rephrased problems maintain >95% conceptual alignment with original problems (measured by domain and competency preservation)

- **SC-009**: Generated solutions contain complete step-by-step reasoning for 100% of problems (no skipped steps, all intermediate calculations shown)

- **SC-010**: Review Agent's quality scores correlate with human expert ratings at ≥0.85 Pearson correlation coefficient

- **SC-011**: System processes a single problem through full pipeline (Photo OCR → Rephrase → Review → Revise loop → Solution) in <60 seconds on average

- **SC-012**: Zero mathematically invalid problems pass quality threshold (all problems with score ≥ 4.5 are mathematically correct and solvable)

- **SC-013**: Rephrased problems demonstrate measurable complexity increase: ≥3 escalation dimensions applied, difficulty level increases by ≥1 point on Krathwohl's index

- **SC-014**: For problems requiring multiple iterations, 100% of revision notes explicitly address the suggestions from prior review

- **SC-015**: System maintains complete traceability: 100% of agent decisions, scores, transformations, and OCR logs are logged and retrievable

- **SC-016**: Student comprehension improvement: In pilot testing, students practicing with rephrased problems show ≥20% improvement in similar problem-solving tasks compared to control group using only original problems
