# 🚀 OCR to Problem 測試快速開始

## 📁 您已獲得的測試文件

### 1. **測試腳本**
- `tests/e2e/test_ocr_to_problem.py` - 完整端到端測試
- `scripts/check_test_environment.sh` - 環境檢查腳本

### 2. **測試圖片**（已創建）
- `tests/fixtures/math_problems/algebra_simple.jpg` - 代數題目
- `tests/fixtures/math_problems/geometry_triangle.jpg` - 幾何題目（含圖）
- `tests/fixtures/math_problems/probability_balls.jpg` - 機率題目
- `tests/fixtures/math_problems/number_theory_gcd.jpg` - 數論題目
- `tests/fixtures/math_problems/combinatorics_committee.jpg` - 組合題目
- `tests/fixtures/math_problems/algebra_system.jpg` - 聯立方程式

### 3. **文件**
- `OCR_TO_PROBLEM_TEST_GUIDE.md` - 完整測試指南
- `TEST_QUICK_START.md` - 本文件（快速開始）

---

## ⚡ 3 步驟快速測試

### 步驟 1: 配置環境

```bash
# 如果 .env 不存在，複製範例文件
cp .env.example .env

# 編輯 .env，確保以下設定正確
# DATABASE_URL=sqlite:///./agenticmath.db
# OCR_LANGUAGE=chinese_cht
# UPLOAD_DIR=./uploads
```

### 步驟 2: 檢查環境

```bash
# 執行環境檢查
./scripts/check_test_environment.sh
```

應該看到：
```
✅ 環境檢查完成，可以開始測試！
```

### 步驟 3: 執行測試

```bash
# 執行端到端測試
python tests/e2e/test_ocr_to_problem.py
```

成功的話會看到：
```
✅ 端到端測試成功完成！

完整流程:
   圖片 → OCR → Problem → 資料庫

創建的資源:
   UploadedImage ID: xxx-xxx-xxx
   Problem ID: xxx-xxx-xxx
```

---

## 🎯 測試內容

此測試將驗證：

1. ✅ **圖片預處理** - 旋轉校正、降噪、對比度增強
2. ✅ **OCR 文字提取** - PaddleOCR 提取繁體中文
3. ✅ **圖表檢測** - OpenCV 檢測幾何圖形
4. ✅ **領域識別** - 關鍵字匹配識別數學領域
5. ✅ **Problem 創建** - 從 OCR 結果創建 Problem
6. ✅ **資料庫儲存** - UploadedImage ↔ Problem 雙向關聯

---

## 📊 預期輸出

### OCR 結果
```
📊 OCR 結果:
   成功: True
   提取文字: 題目 2：直角三角形...
   信心度: 88%
   包含圖表: True
   處理時間: 2340ms
```

### Problem 創建
```
📝 Problem 創建成功!
   ID: xxx-xxx-xxx
   內容: 題目 2：直角三角形...
   領域: geometry
   能力: ['geometric_reasoning', 'spatial_visualization']
   難度: 3/5
   來源: original
   來源類型: ocr
```

---

## ⚙️ 可選配置

### 啟用圖表深度分析（GPT-4 Vision）

在 `.env` 中設定：
```ini
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o
```

有 API key 時會額外分析：
- 圖表類型（right_triangle, circle, etc.）
- 數學考點（pythagorean_theorem, etc.）
- 圖表特徵（頂點、邊長、角度）
- 難度指標

---

## 🔧 測試不同圖片

### 方法 1: 修改測試腳本

編輯 `tests/e2e/test_ocr_to_problem.py`，找到：
```python
test_image_path = project_root / "tests" / "fixtures" / "diagrams" / "triangle.jpg"
```

改為：
```python
# 測試代數題目
test_image_path = project_root / "tests" / "fixtures" / "math_problems" / "algebra_simple.jpg"

# 或測試幾何題目
test_image_path = project_root / "tests" / "fixtures" / "math_problems" / "geometry_triangle.jpg"
```

### 方法 2: 使用自己的圖片

```bash
# 1. 放置圖片
cp your_math_problem.jpg tests/fixtures/diagrams/

# 2. 修改測試腳本指向您的圖片
# test_image_path = project_root / "tests" / "fixtures" / "diagrams" / "your_math_problem.jpg"

# 3. 執行測試
python tests/e2e/test_ocr_to_problem.py
```

---

## 📂 檔案結構

```
AgenticMath/
├── tests/
│   ├── e2e/
│   │   └── test_ocr_to_problem.py          # 端到端測試腳本 ⭐
│   └── fixtures/
│       ├── diagrams/                        # 基本圖形測試圖片
│       │   └── triangle.jpg
│       └── math_problems/                   # 數學題目測試圖片 ⭐
│           ├── algebra_simple.jpg
│           ├── geometry_triangle.jpg
│           ├── probability_balls.jpg
│           ├── number_theory_gcd.jpg
│           ├── combinatorics_committee.jpg
│           └── algebra_system.jpg
├── scripts/
│   └── check_test_environment.sh            # 環境檢查腳本 ⭐
├── .env.example                             # 環境配置範例
├── .env                                     # 實際配置（需創建）
├── OCR_TO_PROBLEM_TEST_GUIDE.md            # 完整測試指南 ⭐
└── TEST_QUICK_START.md                     # 本文件 ⭐
```

---

## ❓ 常見問題

### Q1: 環境檢查失敗怎麼辦？

```bash
# 安裝缺少的依賴
pip install -r requirements.txt

# 創建 .env 文件
cp .env.example .env
```

### Q2: PaddleOCR 下載模型很慢？

首次運行時 PaddleOCR 會下載模型（約 100MB），請耐心等待。

### Q3: 測試失敗怎麼辦？

1. 檢查 `.env` 配置是否正確
2. 確認 PaddleOCR 可正常運行：
   ```bash
   python -c "from paddleocr import PaddleOCR; print('OK')"
   ```
3. 查看詳細錯誤訊息
4. 參考 `OCR_TO_PROBLEM_TEST_GUIDE.md` 的「常見問題」章節

### Q4: 沒有 OpenAI API Key 能測試嗎？

可以！沒有 API key 時：
- ✅ OCR 文字提取正常運作
- ✅ 圖表檢測正常運作（OpenCV）
- ⚠️ 圖表深度分析會被跳過（GPT-4 Vision）
- ✅ Problem 創建正常運作

---

## 📚 延伸閱讀

- 完整測試指南：`OCR_TO_PROBLEM_TEST_GUIDE.md`
- OCR 合約規範：`specs/001-multi-agent-problem-generator/contracts/image-extraction-agent.md`
- 任務清單：`specs/001-multi-agent-problem-generator/tasks.md`

---

**準備好了嗎？開始測試吧！** 🎉

```bash
python tests/e2e/test_ocr_to_problem.py
```
