# Testing Guide - Rephrase Pipeline

## 概述

本指南說明如何測試 Phase 2 實現的 Multi-Agent 數學問題改寫系統。

## 測試類型

### 1. 單元測試和合約測試 (已完成 ✅)

所有 agents 都有完整的測試覆蓋：

```bash
# 測試所有單元測試
pytest tests/unit/ -v

# 測試所有合約測試
pytest tests/contract/ -v

# 測試集成測試
pytest tests/integration/ -v

# 運行所有測試
pytest -v
```

**測試覆蓋率：**
- RephraseAgent: 合約測試 7/7 通過
- ReviewAgent: 合約測試 14/14 通過
- ReviseAgent: 合約測試 26/26 通過
- IterationManager: 集成測試 10/10 通過
- RephrasePipeline: 集成測試 8/8 通過

### 2. 端到端測試 (E2E) - 真實 LLM API

**重要：** 上述測試都是 mock 測試（模擬的 LLM 響應）。要驗證系統真實運作，需要進行 E2E 測試。

## E2E 測試步驟

### 前置條件

1. **設定 OpenAI API Key:**

```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

2. **確認環境：**

```bash
# 檢查 Python 環境
python --version  # Should be 3.11+

# 檢查依賴
pip list | grep openai
```

### 運行 E2E 測試

#### 測試單個 Agent

```bash
# 測試 Rephrase Agent
python scripts/test_rephrase_pipeline_e2e.py --test-agent rephrase

# 測試 Review Agent
python scripts/test_rephrase_pipeline_e2e.py --test-agent review

# 測試 Revise Agent
python scripts/test_rephrase_pipeline_e2e.py --test-agent revise
```

#### 測試 Iteration Manager

```bash
python scripts/test_rephrase_pipeline_e2e.py --test-iteration
```

這將執行完整的 Review → Revise 循環，可能需要 2-3 次迭代。

#### 測試所有組件

```bash
python scripts/test_rephrase_pipeline_e2e.py --test-all
```

### 預期輸出範例

**成功的 Rephrase Agent 測試：**
```
================================================================================
TEST 1: Rephrase Agent
================================================================================
✓ OpenAI API Key found: sk-proj...

📝 Original Problem:
   一個長方形的長度比寬度多3公尺，周長為22公尺，求寬度。

🎯 Escalation Dimensions:
   - Multi-stage Transformation
   - Real-world Parameterization
   - Conditional Branching

⏳ Calling Rephrase Agent...

✅ Success! (took 5.2s)

📊 Results:
   Domain: Algebra
   Difficulty: 4/5
   Competencies: linear_equations, multi_step_reasoning, constraint_analysis

📝 Rephrased Question:
   [複雜的改寫問題...]

💡 Applied Dimensions: Multi-stage Transformation, Real-world Parameterization, Conditional Branching

📈 Token Usage:
   Prompt: 450
   Completion: 380
   Total: 830
   Cost: $0.0080
```

### 成本估算

**每次完整測試預估成本：**
- Rephrase Agent: ~$0.008 (800 tokens)
- Review Agent: ~$0.006 (600 tokens)
- Revise Agent: ~$0.007 (700 tokens)
- Iteration Manager (3 iterations): ~$0.025 (2500 tokens)

**完整測試套件**: ~$0.05 USD

## 可能遇到的問題

### 1. API Key 錯誤

```
❌ Error: OPENAI_API_KEY not set
```

**解決：**
```bash
export OPENAI_API_KEY='your-key-here'
```

### 2. Rate Limit 錯誤

```
❌ Error: Rate limit exceeded
```

**解決：**
- 等待幾分鐘後重試
- 使用更高級別的 API plan
- LLMClient 已實現自動重試（最多 3 次，指數退避）

### 3. 解析錯誤

```
❌ Error: Could not find ###revised_question### section
```

**原因：** LLM 輸出格式不符合預期

**解決：**
- 檢查 prompt template
- 查看 raw LLM response（在日誌中）
- 可能需要調整 temperature 或 prompt

### 4. 驗證失敗

```
❌ Error: revised_question failed to preserve mathematical content
```

**原因：** LLM 移除了關鍵數學內容

**解決：**
- 這是正常的品質控制
- 調整 prompt 強調保留數學內容
- 或放寬驗證規則（不推薦）

## 驗證清單

在確認系統正常運作前，請檢查：

- [ ] Rephrase Agent 能成功改寫問題
- [ ] 改寫後的問題確實更複雜
- [ ] 應用了指定的 escalation dimensions
- [ ] Review Agent 能正確評估品質
- [ ] 分數在 1.0-5.0 範圍內
- [ ] 能提供具體的改進建議
- [ ] Revise Agent 能根據建議改進
- [ ] 改進後保留了原始數學內容
- [ ] Iteration Manager 能成功達到品質閾值
- [ ] 或在最大迭代次數內停止

## 調試技巧

### 查看詳細日誌

```bash
# 設置日誌級別
export LOG_LEVEL=DEBUG

# 運行測試
python scripts/test_rephrase_pipeline_e2e.py --test-agent rephrase
```

### 查看 LLM 原始響應

在代碼中添加：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 保存測試結果

```bash
python scripts/test_rephrase_pipeline_e2e.py --test-all > test_results.txt 2>&1
```

## 下一步

如果所有 E2E 測試都通過：
1. ✅ 系統可以投入使用
2. 考慮添加 API endpoints (Phase 4)
3. 集成到完整應用中

如果測試失敗：
1. 檢查錯誤訊息
2. 查看本指南的「可能遇到的問題」
3. 調整 prompt 或參數
4. 重新測試

## 常見問題 (FAQ)

**Q: 測試需要多長時間？**
A: 單個 agent 測試 ~5-10 秒，完整測試套件 ~30-60 秒（取決於 LLM 響應時間）

**Q: 可以使用其他 LLM 模型嗎？**
A: 可以，修改 `model="gpt-4o"` 為其他模型（如 `gpt-4-turbo`），但需要調整 cost calculation

**Q: 如何降低測試成本？**
A:
- 使用更小的模型（如 gpt-3.5-turbo）
- 減少測試次數
- 使用 mock 測試進行開發

**Q: 中文支援如何？**
A: 所有 agents 都經過中文測試，支援繁體和簡體中文

## 支援

如有問題，請查看：
- 項目 README
- 各 agent 的合約文檔（`specs/001-multi-agent-problem-generator/contracts/`）
- GitHub Issues
