# Agent 合約：Image Extraction (OCR) Agent

**Agent 名稱**: Image Extraction Agent (圖片文字提取代理)
**版本**: 1.0.0
**最後更新**: 2025-11-06
**技術**: PaddleOCR (Apache 2.0)

## 職責

Image Extraction Agent 負責從學生上傳的照片中提取數學題目文字內容，包含數學符號、公式和圖表描述。此 Agent 使用 PaddleOCR 開源 OCR 引擎，支援繁體中文和 LaTeX 公式辨識。

## 輸入格式

### 輸入

```json
{
  "image_id": "uuid-string",
  "file_path": "/uploads/2025/11/student_photo_001.jpg",
  "file_format": "jpeg" | "png",
  "file_size": 2458693,
  "preprocessing_config": {
    "auto_rotation": true,
    "noise_reduction": true,
    "contrast_enhancement": true
  },
  "ocr_config": {
    "language": "chinese_cht",
    "use_angle_cls": true,
    "use_gpu": false
  }
}
```

### 輸入欄位說明

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `image_id` | String (UUID) | 是 | 圖片的唯一識別碼 |
| `file_path` | String | 是 | 圖片檔案的儲存路徑 |
| `file_format` | Enum | 是 | 圖片格式（jpeg 或 png） |
| `file_size` | Integer | 是 | 檔案大小（bytes） |
| `preprocessing_config` | Object | 否 | 預處理設定 |
| `preprocessing_config.auto_rotation` | Boolean | 否 | 是否自動旋轉校正（預設 true） |
| `preprocessing_config.noise_reduction` | Boolean | 否 | 是否降噪（預設 true） |
| `preprocessing_config.contrast_enhancement` | Boolean | 否 | 是否對比度增強（預設 true） |
| `ocr_config` | Object | 否 | OCR 引擎設定 |
| `ocr_config.language` | String | 否 | OCR 語言（預設 "chinese_cht"） |
| `ocr_config.use_angle_cls` | Boolean | 否 | 是否使用角度分類器（預設 true） |
| `ocr_config.use_gpu` | Boolean | 否 | 是否使用 GPU 加速（預設 false） |

## 輸出格式

### 輸出

```json
{
  "success": true,
  "extracted_text": "求解方程式：在直角三角形 ABC 中，∠C = 90°，若 AB = 10，AC = 6，求 BC 的長度。",
  "confidence_score": 0.92,
  "contains_diagram": true,
  "diagram_description": "包含直角三角形 ABC，標註直角於 C 點，斜邊 AB 標註長度 10，直角邊 AC 標註長度 6",
  "text_regions": [
    {
      "text": "求解方程式：",
      "confidence": 0.95,
      "bbox": [[10, 20], [150, 20], [150, 45], [10, 45]]
    },
    {
      "text": "在直角三角形 ABC 中，∠C = 90°",
      "confidence": 0.89,
      "bbox": [[10, 50], [380, 50], [380, 75], [10, 75]]
    }
  ],
  "diagram_regions": [
    {
      "bbox": [[400, 100], [600, 100], [600, 300], [400, 300]],
      "type": "geometric_figure",
      "description": "直角三角形，標註邊長"
    }
  ],
  "diagram_analysis": {
    "diagram_type": "right_triangle",
    "key_concepts": ["pythagorean_theorem", "trigonometry"],
    "features": {
      "vertices": ["A", "B", "C"],
      "right_angle_at": "C",
      "labeled_sides": {
        "AB": "10",
        "AC": "6"
      },
      "unlabeled_sides": ["BC"]
    },
    "difficulty_indicators": {
      "has_labels": true,
      "requires_calculation": true,
      "complexity": "medium"
    }
  },
  "preprocessing_applied": ["rotation_corrected", "contrast_enhanced"],
  "processing_time_ms": 2340,
  "ocr_engine": "paddleocr",
  "ocr_version": "2.7.0",
  "warnings": []
}
```

### 輸出欄位說明

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `success` | Boolean | 是 | OCR 是否成功執行 |
| `extracted_text` | String | 是 | 提取的完整文字內容（包含文字和公式） |
| `confidence_score` | Float (0.0-1.0) | 是 | 整體信心度分數（所有文字區域的平均值） |
| `contains_diagram` | Boolean | 是 | 照片中是否包含圖表或幾何圖形 |
| `diagram_description` | String | 否 | 圖表的文字描述（如果 contains_diagram = true） |
| `text_regions` | Array | 是 | 所有辨識出的文字區域詳細資訊 |
| `text_regions[].text` | String | 是 | 該區域的文字內容 |
| `text_regions[].confidence` | Float | 是 | 該區域的信心度分數 |
| `text_regions[].bbox` | Array | 是 | 文字框的四個角座標 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] |
| `diagram_regions` | Array | 否 | 檢測到的圖表區域 |
| `diagram_regions[].bbox` | Array | 是 | 圖表區域的邊界框 |
| `diagram_regions[].type` | String | 是 | 圖表類型（geometric_figure, chart, table） |
| `diagram_regions[].description` | String | 否 | 圖表描述 |
| `diagram_analysis` | Object | 否 | 圖表深度分析（如果 contains_diagram = true） |
| `diagram_analysis.diagram_type` | String | 是 | 具體圖形類型（right_triangle, circle, parabola 等） |
| `diagram_analysis.key_concepts` | Array[String] | 是 | 相關數學考點（pythagorean_theorem, similarity 等） |
| `diagram_analysis.features` | Object | 是 | 圖表特徵（頂點、邊長、角度等） |
| `diagram_analysis.difficulty_indicators` | Object | 是 | 難度指標（用於生成近似題） |
| `preprocessing_applied` | Array[String] | 是 | 實際執行的預處理步驟 |
| `processing_time_ms` | Integer | 是 | OCR 處理耗時（毫秒） |
| `ocr_engine` | String | 是 | 使用的 OCR 引擎名稱 |
| `ocr_version` | String | 是 | OCR 引擎版本號 |
| `warnings` | Array[String] | 是 | 警告訊息（例如：信心度過低、圖片品質不佳等） |

### 錯誤輸出

當 OCR 失敗時：

```json
{
  "success": false,
  "error_code": "OCR_NO_TEXT_DETECTED",
  "error_message": "無法辨識照片中的文字內容，請確認照片清晰且包含可辨識的文字。",
  "extracted_text": "",
  "confidence_score": 0.0,
  "contains_diagram": false,
  "warnings": [
    "圖片品質過低，信心度 < 70%",
    "未檢測到任何文字區域"
  ],
  "processing_time_ms": 1240
}
```

### 錯誤代碼

| 錯誤代碼 | 說明 | 建議處理 |
|---------|------|---------|
| `OCR_NO_TEXT_DETECTED` | 照片中未檢測到任何文字 | 要求學生重新拍攝更清晰的照片 |
| `OCR_LOW_CONFIDENCE` | 辨識信心度過低（< 70%） | 標記為低信心度，繼續處理但記錄警告 |
| `OCR_IMAGE_TOO_LARGE` | 圖片檔案過大（> 10MB） | 要求壓縮或重新拍攝 |
| `OCR_UNSUPPORTED_FORMAT` | 不支援的圖片格式 | 只接受 JPEG/PNG 格式 |
| `OCR_CORRUPTED_IMAGE` | 圖片檔案損壞無法讀取 | 要求重新上傳 |
| `OCR_ENGINE_ERROR` | OCR 引擎內部錯誤 | 記錄錯誤日誌，稍後重試 |

## 處理流程

### 1. 圖片預處理

```python
def preprocess_image(image_path: str, config: dict) -> Image:
    """
    預處理圖片以提高 OCR 準確度

    步驟：
    1. 讀取圖片
    2. 檢測並校正旋轉角度（use_angle_cls=True）
    3. 降噪處理（去除雜訊）
    4. 對比度增強（提高文字清晰度）
    5. 調整大小（如果圖片過大）
    """
    image = Image.open(image_path)

    if config.get('auto_rotation', True):
        image = detect_and_rotate(image)

    if config.get('noise_reduction', True):
        image = reduce_noise(image)

    if config.get('contrast_enhancement', True):
        image = enhance_contrast(image)

    return image
```

### 2. OCR 文字提取

```python
from paddleocr import PaddleOCR

def extract_text(image_path: str, ocr_config: dict) -> dict:
    """
    使用 PaddleOCR 提取文字

    配置：
    - lang='chinese_cht'：繁體中文
    - use_angle_cls=True：自動旋轉校正
    - use_gpu=False：CPU 模式（可根據環境調整）
    """
    ocr = PaddleOCR(
        use_angle_cls=ocr_config.get('use_angle_cls', True),
        lang=ocr_config.get('language', 'chinese_cht'),
        use_gpu=ocr_config.get('use_gpu', False)
    )

    result = ocr.ocr(image_path, cls=True)

    # 提取文字和信心度
    text_regions = []
    for line in result[0]:
        bbox, (text, confidence) = line
        text_regions.append({
            "text": text,
            "confidence": confidence,
            "bbox": bbox
        })

    # 組合完整文字
    extracted_text = "\n".join([r["text"] for r in text_regions])
    avg_confidence = sum([r["confidence"] for r in text_regions]) / len(text_regions)

    return {
        "extracted_text": extracted_text,
        "confidence_score": avg_confidence,
        "text_regions": text_regions
    }
```

### 3. 圖表檢測與分析

#### 3.1 基礎檢測（OpenCV）

```python
def detect_diagrams_basic(image_path: str) -> dict:
    """
    使用 OpenCV 進行基礎圖表檢測

    目的：快速檢測圖表存在與位置
    """
    # 檢測圖表區域
    # 識別基本形狀（三角形、圓形、矩形）
    # 返回邊界框
```

#### 3.2 深度分析（Vision LLM）

```python
def analyze_diagram_with_llm(image_path: str, bbox: list) -> dict:
    """
    使用 GPT-4 Vision 深度分析圖表

    目的：
    1. 理解圖表類型和特徵
    2. 識別數學考點
    3. 為生成近似題準備資訊

    注意：只在檢測到圖表時才調用（節省 API 成本）
    """
    # 裁剪圖表區域
    diagram_image = crop_image(image_path, bbox)

    # 構建 Vision LLM prompt
    prompt = """
    請分析這個數學圖表，提供以下資訊：

    1. 圖形類型（例如：直角三角形、等腰三角形、圓形、拋物線等）
    2. 數學考點（例如：畢氏定理、三角函數、相似三角形等）
    3. 圖表特徵：
       - 頂點標註（如 A, B, C）
       - 已標註的邊長或角度
       - 未標註但可能需要求解的部分
    4. 難度指標：
       - 是否有完整標註
       - 是否需要計算
       - 複雜度（簡單/中等/困難）

    以 JSON 格式回答，範例：
    {
      "diagram_type": "right_triangle",
      "key_concepts": ["pythagorean_theorem", "trigonometry"],
      "features": {
        "vertices": ["A", "B", "C"],
        "right_angle_at": "C",
        "labeled_sides": {"AB": "10", "AC": "6"},
        "unlabeled_sides": ["BC"]
      },
      "difficulty_indicators": {
        "has_labels": true,
        "requires_calculation": true,
        "complexity": "medium"
      }
    }
    """

    # 調用 GPT-4 Vision API
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": encode_image(diagram_image)}}
                ]
            }
        ]
    )

    # 解析回應
    analysis = json.loads(response.choices[0].message.content)

    return {
        "diagram_type": analysis["diagram_type"],
        "key_concepts": analysis["key_concepts"],
        "features": analysis["features"],
        "difficulty_indicators": analysis["difficulty_indicators"]
    }
```

## 品質標準

### 成功標準

1. **文字辨識準確度 ≥ 85%** (印刷體繁體中文)
2. **文字辨識準確度 ≥ 82%** (清晰手寫體)
3. **處理時間 < 3 秒** (CPU 模式)
4. **圖表檢測成功率 ≥ 80%** (包含幾何圖形的照片)

### 信心度分級

| 信心度範圍 | 等級 | 處理建議 |
|-----------|------|---------|
| 0.90 - 1.00 | 極高 | 直接使用，無需人工確認 |
| 0.85 - 0.89 | 高 | 直接使用，記錄日誌 |
| 0.70 - 0.84 | 中 | 使用但標記為中等信心度 |
| 0.50 - 0.69 | 低 | 使用但標記警告，建議人工檢查 |
| < 0.50 | 極低 | 拒絕處理，要求重新拍攝 |

## 測試案例

### 測試案例 1：印刷體數學題目（無圖表）

**輸入圖片**: 清晰的課本題目照片
**預期輸出**:
- `confidence_score` ≥ 0.90
- `extracted_text` 完整且正確
- `contains_diagram` = false
- `processing_time_ms` < 2000

### 測試案例 2：手寫數學題目（含圖表）

**輸入圖片**: 學生手寫題目 + 幾何圖形
**預期輸出**:
- `confidence_score` ≥ 0.82
- `extracted_text` 包含手寫文字
- `contains_diagram` = true
- `diagram_description` 描述幾何圖形

### 測試案例 3：模糊或傾斜的照片

**輸入圖片**: 角度傾斜 15° 的照片
**預期輸出**:
- `preprocessing_applied` 包含 "rotation_corrected"
- `confidence_score` ≥ 0.80
- `warnings` 可能包含品質警告

### 測試案例 4：無可辨識文字

**輸入圖片**: 空白頁面或純圖片
**預期輸出**:
- `success` = false
- `error_code` = "OCR_NO_TEXT_DETECTED"
- `extracted_text` = ""

## 與其他 Agent 的整合

OCR Agent 的輸出會直接傳遞給 Rephrase Agent 作為輸入：

```
Student Photo → [OCR Agent] → extracted_text → [Rephrase Agent] → ...
```

整合範例：

```python
# 1. OCR Agent 處理照片
ocr_result = image_extraction_agent.process(image_input)

# 2. 創建 Problem 實體
if ocr_result["success"] and ocr_result["confidence_score"] >= 0.70:
    problem = Problem(
        content=ocr_result["extracted_text"],
        source=ProblemSource.ORIGINAL,
        source_type=SourceType.OCR,
        domain=identify_domain(ocr_result["extracted_text"]),
        ...
    )

    # 3. 傳遞給 Rephrase Agent
    rephrase_input = {
        "problem_content": problem.content,
        "domain": problem.domain,
        ...
    }
    rephrase_result = rephrase_agent.process(rephrase_input)
```

## 依賴項目

### Python 套件

```bash
# 必需
paddleocr==2.7.0
paddlepaddle==2.5.0  # CPU 版本
# 或
paddlepaddle-gpu==2.5.0  # GPU 版本

# 圖片處理
Pillow==10.0.0
opencv-python==4.8.0
numpy==1.24.0
```

### 系統需求

- **CPU**: 最低 4 核心（推薦 8 核心）
- **記憶體**: 最低 4GB（推薦 8GB）
- **GPU** (可選): CUDA 11.2+ 支援的 NVIDIA GPU

## 效能基準

| 場景 | 圖片大小 | 處理時間 (CPU) | 處理時間 (GPU) | 信心度 |
|------|---------|---------------|---------------|--------|
| 印刷體題目 | 2MB | 2.3 秒 | 0.5 秒 | 0.92 |
| 手寫題目 | 3MB | 2.8 秒 | 0.6 秒 | 0.85 |
| 含圖表題目 | 4MB | 3.5 秒 | 0.8 秒 | 0.89 |
| 複雜版面 | 5MB | 4.2 秒 | 1.0 秒 | 0.87 |

**測試環境**: Intel i7-9700K, 16GB RAM, NVIDIA GTX 1080 (GPU 測試)

---

**版本歷史**:
- v1.0.0 (2025-11-06): 初始版本，支援繁體中文 OCR 和圖表檢測
