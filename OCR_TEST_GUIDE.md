# OCR 功能測試指南

本指南說明如何使用最小化依賴清單來測試 PaddleOCR 功能，避免安裝整個專案的所有依賴。

## 📋 測試檔案說明

- **`requirements-ocr-test.txt`**: OCR 測試專用的最小化依賴清單
- **`setup_ocr_test_env.sh`**: 自動化設置腳本（推薦使用）
- **`tests/unit/test_text_extractor.py`**: OCR 功能的測試檔案

## 🚀 快速開始（推薦方法）

### 方法 A：使用自動化腳本（最簡單）

```bash
# 1. 執行設置腳本（會自動創建虛擬環境並安裝依賴）
./setup_ocr_test_env.sh

# 2. 啟動虛擬環境
source venv-ocr-test/bin/activate

# 3. 執行測試
pytest tests/unit/test_text_extractor.py -v

# 4. 測試完成後退出虛擬環境
deactivate
```

### 方法 B：手動設置

```bash
# 1. 創建新的虛擬環境
python -m venv venv-ocr-test

# 2. 啟動虛擬環境
source venv-ocr-test/bin/activate

# 3. 升級 pip
pip install --upgrade pip

# 4. 安裝 OCR 測試依賴
pip install -r requirements-ocr-test.txt

# 5. 驗證安裝
python -c "import paddleocr; print('PaddleOCR 版本:', paddleocr.__version__)"

# 6. 執行測試
pytest tests/unit/test_text_extractor.py -v

# 7. 測試完成後退出虛擬環境
deactivate
```

## 📊 預期測試結果

### 在有網絡連接的環境中：

```
======================== test session starts =========================
collected 24 items

test_text_extractor.py::TestOCRConfig::test_default_config PASSED
test_text_extractor.py::TestOCRConfig::test_custom_config PASSED
... (更多測試)
test_text_extractor.py::TestPerformance::test_singleton_performance PASSED

===================== 24 passed in 45.2s ========================
```

**說明**：
- 首次執行時，PaddleOCR 會自動下載繁體中文模型（約需 3-5 分鐘）
- 模型會被緩存到 `~/.paddleocr/` 目錄
- 後續測試會直接使用已下載的模型，速度會快很多

### 在離線環境中（無網絡連接）：

```
===================== test session starts ========================
collected 24 items

test_text_extractor.py::TestOCRConfig::test_default_config PASSED
... (10 個測試 PASSED)
test_text_extractor.py::TestOCRExtractor::test_extract_from_image SKIPPED
... (14 個測試 SKIPPED)

============= 10 passed, 14 skipped in 5.2s =================
```

**說明**：
- 10 個測試通過（配置、初始化、錯誤處理）
- 14 個測試被跳過（需要 PaddleOCR 模型）
- 這是正常現象，不代表代碼有問題

## 🔍 測試內容說明

### ✅ 通過的測試（無需模型）

1. **OCRConfig 測試**
   - 預設配置驗證
   - 自定義配置驗證

2. **TextRegion 測試**
   - 資料結構創建
   - 字典轉換
   - 字串表示

3. **錯誤處理測試**
   - 不存在的檔案
   - 無效的圖片格式
   - 初始化驗證

### ⏭️ 跳過的測試（需要模型）

1. **OCR 執行測試**
   - 從圖片提取文字
   - 處理空白圖片
   - 多行文字識別

2. **整合測試**
   - 完整 OCR 流程
   - 信心分數驗證
   - 批次處理

3. **性能測試**
   - 提取速度驗證
   - 單例模式性能

## 🛠️ 疑難排解

### 問題 1: ModuleNotFoundError: No module named 'numpy.exceptions'

**原因**：numpy 版本衝突

**解決方案**：
```bash
# 使用專門的 OCR 測試依賴清單
pip install -r requirements-ocr-test.txt
```

### 問題 2: PaddleOCR 模型下載失敗

**可能原因**：
- 網絡連接問題
- 防火牆阻擋

**解決方案**：
```bash
# 1. 檢查網絡連接
ping www.baidu.com

# 2. 手動設置代理（如果需要）
export http_proxy=http://your-proxy:port
export https_proxy=http://your-proxy:port

# 3. 重新執行測試
pytest tests/unit/test_text_extractor.py -v
```

### 問題 3: 測試執行時間過長

**原因**：首次執行需要下載模型

**正常情況**：
- 首次執行：3-5 分鐘（下載模型）
- 後續執行：30-60 秒（使用緩存模型）

## 📝 依賴清單內容

`requirements-ocr-test.txt` 只包含以下核心依賴：

- **PaddlePaddle**: 深度學習框架（CPU 版本）
- **PaddleOCR**: OCR 引擎
- **OpenCV**: 圖像處理
- **Pillow**: 圖像處理
- **NumPy**: 數值計算（固定為 1.26.4 以避免衝突）
- **pytest**: 測試框架

**不包含**：
- ❌ CrewAI（多代理框架，OCR 測試不需要）
- ❌ OpenAI（LLM API，OCR 測試不需要）
- ❌ FastAPI（Web 框架，OCR 測試不需要）
- ❌ SQLAlchemy（數據庫 ORM，OCR 測試不需要）

## 🎯 測試完成後的下一步

測試成功後，您可以：

1. **整合到主環境**：
   ```bash
   # 回到主虛擬環境
   source venv/bin/activate

   # 安裝完整依賴
   pip install -r requirements.txt
   ```

2. **繼續開發 Task 1.4**（圖表檢測與描述）

3. **進行手動功能測試**：
   ```python
   from src.ocr.text_extractor import extract_text

   # 測試自己的圖片
   result = extract_text("path/to/your/image.jpg")
   print(result["text"])
   ```

## 💡 建議

- ✅ 使用獨立的虛擬環境測試 OCR 功能
- ✅ 首次測試在有網絡的環境中進行
- ✅ 模型下載後可離線使用
- ✅ 定期更新 PaddleOCR 以獲得更好的識別效果
