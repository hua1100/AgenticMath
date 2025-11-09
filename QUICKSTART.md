# 快速開始 - 測試 CrewAI Pipeline

如果您只想測試 Phase 2 (CrewAI Pipeline)，**不需要安裝 OCR 依賴**。

## 最小化安裝（推薦）

```bash
# 1. 只安裝 CrewAI 相關依賴
pip install -r requirements-crewai-only.txt

# 2. 驗證安裝
python -c "import crewai; print('CrewAI OK')"
python -c "from src.orchestration import CrewAIPipeline; print('Pipeline OK')"
```

## 快速測試

### 選項 1: Mock 測試（免費，無需 API Key）

```bash
# 運行 CrewAI Pipeline 測試（5 秒）
python -m pytest tests/integration/test_crewai_pipeline.py -v --no-cov

# 運行所有 Phase 2 測試，排除 OCR（20 秒）
python -m pytest tests/ -k "not ocr" -v --no-cov
```

**預期結果：**
- `test_crewai_pipeline.py`: 5/5 通過 ✅
- 總計: 200+ 測試通過（排除 OCR）

### 選項 2: E2E 測試（需要 OpenAI API Key）

```bash
# 1. 設置 API Key
export OPENAI_API_KEY='your-key-here'

# 2. 運行快速測試腳本
python quick_test.py
```

**預期：**
- 執行時間: 30-60 秒
- 成本: ~$0.04 USD
- 顯示完整的問題改寫流程

## 依賴說明

### Phase 1 (OCR) - 不需要
- ❌ paddlepaddle
- ❌ paddleocr
- ❌ opencv-python
- ❌ Pillow

### Phase 2 (CrewAI Pipeline) - 需要
- ✅ crewai
- ✅ openai
- ✅ langchain
- ✅ sqlalchemy
- ✅ pydantic

## 如果遇到依賴衝突

```bash
# 卸載有問題的包
pip uninstall paddlepaddle paddleocr opencv-python -y

# 只安裝 CrewAI 依賴
pip install -r requirements-crewai-only.txt
```

## 測試覆蓋範圍

使用 `requirements-crewai-only.txt`，您可以測試：

✅ **可以測試：**
- CrewAI Pipeline (5 tests)
- Iteration Manager (10 tests)
- Rephrase Pipeline (8 tests)
- All Agents (Rephrase, Review, Revise)
- LLM Client
- Parsers
- Database models
- Contract tests

❌ **無法測試：**
- OCR Pipeline (7 tests) - 需要 PaddleOCR
- 圖像處理相關功能

## 推薦工作流程

```bash
# 1. 確認安裝
pip list | grep -E "crewai|openai|langchain|pytest"

# 2. 快速驗證（免費）
python -m pytest tests/integration/test_crewai_pipeline.py -v --no-cov

# 3. 如果有 API Key，測試真實效果
export OPENAI_API_KEY='your-key'
python quick_test.py
```

## 完整安裝（包含 OCR）

如果之後需要測試 OCR 功能：

```bash
# 安裝完整依賴（包含 PaddleOCR）
pip install -r requirements.txt

# 或手動安裝 OCR 依賴
pip install paddleocr==2.7.0 paddlepaddle==2.5.2 opencv-python==4.9.0.80 Pillow==10.2.0
```

---

**現在就開始測試！** 🚀

```bash
python -m pytest tests/integration/test_crewai_pipeline.py -v --no-cov
```
