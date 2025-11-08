# OCR to Problem 端到端測試指南

本指南將引導您完成 **OCR → Problem 完整工作流程** 的測試。

## 📋 測試涵蓋範圍

此端到端測試涵蓋以下流程：

```
學生照片 → 圖片上傳 → OCR 處理 → Problem 創建 → 資料庫儲存
```

具體步驟：
1. ✅ **圖片預處理**：旋轉校正、降噪、對比度增強
2. ✅ **文字提取**：使用 PaddleOCR 提取繁體中文文字
3. ✅ **圖表檢測**：使用 OpenCV 檢測幾何圖形
4. ✅ **圖表分析**：使用 GPT-4 Vision 深度分析（可選）
5. ✅ **領域識別**：關鍵字匹配識別數學領域
6. ✅ **Problem 創建**：創建 Problem 實體
7. ✅ **資料庫儲存**：儲存 UploadedImage 和 Problem

---

## 🚀 快速開始

### 1. 環境檢查

```bash
# 1.1 執行環境檢查腳本
chmod +x scripts/check_test_environment.sh
./scripts/check_test_environment.sh
```

如果檢查通過，您將看到：
```
✅ 環境檢查完成，可以開始測試！
```

### 2. 配置 .env 文件

如果 `.env` 文件不存在：

```bash
# 2.1 複製範例文件
cp .env.example .env

# 2.2 編輯 .env 文件
nano .env  # 或使用您喜歡的編輯器
```

**必要配置**：
```ini
# SQLite 資料庫（開發環境）
DATABASE_URL=sqlite:///./agenticmath.db

# OCR 配置
OCR_LANGUAGE=chinese_cht
OCR_USE_GPU=false
OCR_USE_ANGLE_CLS=true

# 上傳目錄
UPLOAD_DIR=./uploads
```

**可選配置**（用於圖表深度分析）：
```ini
# OpenAI API Key（沒有的話圖表分析會被跳過）
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o
```

### 3. 安裝依賴（如果尚未安裝）

```bash
# 3.1 安裝 Python 依賴
pip install -r requirements.txt

# 3.2 驗證 PaddleOCR 安裝
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

### 4. 執行測試

```bash
# 4.1 執行端到端測試
python tests/e2e/test_ocr_to_problem.py
```

---

## 📊 測試輸出說明

測試將輸出詳細的執行資訊：

### 成功輸出範例

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   AgenticMath - OCR to Problem 端到端測試                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
  環境檢查
================================================================================

✅ .env 文件存在
✅ OPENAI_API_KEY 已設定
✅ PaddleOCR 已安裝
✅ 上傳目錄存在: ./uploads

✅ 環境檢查通過！

================================================================================
  資料庫初始化
================================================================================

✅ 資料庫表格創建成功

================================================================================
  創建測試圖片記錄
================================================================================

✅ 測試圖片記錄已創建
   ID: 550e8400-e29b-41d4-a716-446655440000
   Path: /home/user/AgenticMath/tests/fixtures/diagrams/triangle.jpg
   Size: 12440 bytes

================================================================================
  OCR Pipeline 測試
================================================================================

處理圖片: /home/user/AgenticMath/tests/fixtures/diagrams/triangle.jpg
圖片 ID: 550e8400-e29b-41d4-a716-446655440000

⏳ 執行 OCR 處理...

📊 OCR 結果:
   成功: True
   提取文字: 題目 2：直角三角形 在直角三角形 ABC 中，角 C = 90度 已知 AB = 10，AC = 6...
   信心度: 88%
   包含圖表: True
   圖表描述: 包含三角形
   處理時間: 2340ms
   預處理步驟: ['rotation_corrected', 'contrast_enhanced']

================================================================================
  Problem 創建測試
================================================================================

⏳ 從 OCR 結果創建 Problem...

📝 Problem 創建成功!
   ID: 660e8400-e29b-41d4-a716-446655440001
   內容: 題目 2：直角三角形 在直角三角形 ABC 中，角 C = 90度 已知 AB = 10，AC = 6 求 BC 的長度。
   領域: geometry
   能力: ['geometric_reasoning', 'spatial_visualization']
   難度: 3/5
   來源: original
   來源類型: ocr
   關聯圖片 ID: 550e8400-e29b-41d4-a716-446655440000

================================================================================
  資料庫狀態驗證
================================================================================

✅ UploadedImage 記錄存在
   OCR 文字: 題目 2：直角三角形 在直角三角形 ABC 中，角 C = 90度...
   OCR 信心度: 88%
   關聯 Problem ID: 660e8400-e29b-41d4-a716-446655440001

✅ Problem 記錄存在
   內容: 題目 2：直角三角形 在直角三角形 ABC 中，角 C = 90度...
   領域: geometry
   關聯圖片 ID: 550e8400-e29b-41d4-a716-446655440000

✅ 雙向關聯正確

================================================================================
  測試總結
================================================================================

✅ 端到端測試成功完成！

完整流程:
   圖片 → OCR → Problem → 資料庫

創建的資源:
   UploadedImage ID: 550e8400-e29b-41d4-a716-446655440000
   Problem ID: 660e8400-e29b-41d4-a716-446655440001
```

---

## 🎨 創建自訂測試圖片

### 使用圖片生成器

```bash
# 生成各種數學題目圖片
python tests/fixtures/create_math_problem_images.py
```

這將創建 6 張測試圖片：
- `algebra_simple.jpg` - 簡單代數方程式
- `geometry_triangle.jpg` - 直角三角形（含圖）
- `probability_balls.jpg` - 機率問題
- `number_theory_gcd.jpg` - 最大公因數
- `combinatorics_committee.jpg` - 組合問題
- `algebra_system.jpg` - 聯立方程式

### 使用自己的圖片

1. **準備圖片**：
   - 格式：JPEG 或 PNG
   - 大小：< 10MB
   - 內容：清晰的繁體中文數學題目
   - 解析度：建議 800x600 以上

2. **放置圖片**：
   ```bash
   cp your_image.jpg tests/fixtures/diagrams/
   ```

3. **修改測試腳本**：
   編輯 `tests/e2e/test_ocr_to_problem.py`，找到這一行：
   ```python
   test_image_path = project_root / "tests" / "fixtures" / "diagrams" / "triangle.jpg"
   ```
   改為：
   ```python
   test_image_path = project_root / "tests" / "fixtures" / "diagrams" / "your_image.jpg"
   ```

---

## 🔍 進階測試選項

### 測試不同領域

修改測試腳本以測試特定領域的題目：

```python
# 測試代數題目
test_image_path = "tests/fixtures/math_problems/algebra_simple.jpg"

# 測試幾何題目
test_image_path = "tests/fixtures/math_problems/geometry_triangle.jpg"

# 測試機率題目
test_image_path = "tests/fixtures/math_problems/probability_balls.jpg"
```

### 測試圖表分析功能

確保 `.env` 中設定了 `OPENAI_API_KEY`，然後使用包含圖表的圖片：

```python
test_image_path = "tests/fixtures/math_problems/geometry_triangle.jpg"
```

### 批量測試

創建一個循環測試多張圖片：

```python
test_images = [
    "algebra_simple.jpg",
    "geometry_triangle.jpg",
    "probability_balls.jpg",
    "number_theory_gcd.jpg",
]

for image_file in test_images:
    print(f"\n{'='*80}")
    print(f"  測試圖片: {image_file}")
    print(f"{'='*80}\n")

    # 執行測試...
```

---

## ⚠️ 常見問題

### 1. PaddleOCR 下載模型失敗

**問題**：首次運行時 PaddleOCR 需要下載模型，可能因網路問題失敗。

**解決方案**：
```bash
# 設定 PaddleOCR 使用國內鏡像
export HUB_HOME=/path/to/models
```

### 2. OpenCV 錯誤

**問題**：`ImportError: libGL.so.1: cannot open shared object file`

**解決方案**：
```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-glx

# 或使用 headless 版本
pip uninstall opencv-python
pip install opencv-python-headless
```

### 3. 資料庫錯誤

**問題**：`sqlite3.OperationalError: table already exists`

**解決方案**：
```bash
# 刪除舊資料庫重新創建
rm agenticmath.db
python tests/e2e/test_ocr_to_problem.py
```

### 4. OCR 無法識別中文

**問題**：提取的文字為空或亂碼

**解決方案**：
- 確認 `.env` 中 `OCR_LANGUAGE=chinese_cht`
- 確認圖片清晰度足夠
- 嘗試增加對比度或調整解析度

### 5. 圖表分析被跳過

**問題**：`⚠️ OPENAI_API_KEY 未設定（圖表分析將被跳過）`

**解決方案**：
- 這是正常的，沒有 API key 時只會跳過深度分析
- 如需測試圖表分析，請在 `.env` 中設定有效的 `OPENAI_API_KEY`

---

## 📈 效能基準

正常情況下的處理時間（僅供參考）：

| 步驟 | 預期時間 | 說明 |
|------|---------|------|
| 圖片預處理 | 100-200ms | OpenCV 處理 |
| 文字提取 (OCR) | 1000-2000ms | PaddleOCR 處理 |
| 圖表檢測 | 100-200ms | OpenCV 輪廓檢測 |
| 圖表分析 | 500-1000ms | GPT-4 Vision API |
| Problem 創建 | 50-100ms | 資料庫操作 |
| **總計** | **2000-3500ms** | 完整流程 |

---

## 🔗 相關文件

- [OCR_TEST_GUIDE.md](./OCR_TEST_GUIDE.md) - OCR 模組測試指南
- [specs/001-multi-agent-problem-generator/contracts/image-extraction-agent.md](./specs/001-multi-agent-problem-generator/contracts/image-extraction-agent.md) - OCR Agent 合約
- [specs/001-multi-agent-problem-generator/tasks.md](./specs/001-multi-agent-problem-generator/tasks.md) - 任務清單

---

## ✅ 測試檢查清單

執行測試前，請確認：

- [ ] Python 版本 >= 3.11
- [ ] 已安裝所有依賴 (`pip install -r requirements.txt`)
- [ ] `.env` 文件已配置
- [ ] `uploads/` 目錄已創建
- [ ] 測試圖片存在於 `tests/fixtures/diagrams/`
- [ ] PaddleOCR 可正常運行
- [ ] （可選）OpenAI API Key 已設定

執行 `./scripts/check_test_environment.sh` 可自動檢查以上項目！

---

**祝測試順利！** 🎉

如有問題，請查看上方的「常見問題」章節或聯繫開發團隊。
