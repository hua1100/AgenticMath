# 圖表生成功能規格

**功能名稱**: Diagram Generation（圖表生成）
**使用階段**: 題目生成階段（Rephrase Agent 或專門的 Generator）
**版本**: 1.0.0
**最後更新**: 2025-11-08

## 概述

本功能用於在生成新的數學題目時，根據題目內容自動生成對應的數學圖表。這樣可以讓生成的題目具有真實考題的感覺，包含完整的圖表說明。

## 使用場景

### 場景 1：基於原題圖表生成相似圖表

**輸入**：從 OCR 階段獲得的圖表分析資料

```json
{
  "diagram_analysis": {
    "diagram_type": "right_triangle",
    "key_concepts": ["pythagorean_theorem"],
    "features": {
      "vertices": ["A", "B", "C"],
      "right_angle_at": "C",
      "labeled_sides": {"AB": "10", "AC": "6"}
    }
  }
}
```

**輸出**：生成難度相近但數值不同的新圖表

```json
{
  "generated_diagram": {
    "diagram_type": "right_triangle",
    "features": {
      "vertices": ["P", "Q", "R"],
      "right_angle_at": "R",
      "labeled_sides": {"PQ": "13", "PR": "5"}
    },
    "image_path": "/generated/diagrams/triangle_001.png",
    "tikz_code": "\\begin{tikzpicture}...",
    "matplotlib_code": "import matplotlib..."
  }
}
```

---

### 場景 2：從題目文字生成圖表

**輸入**：生成的新題目文字

```
在直角三角形 DEF 中，∠F = 90°，DE = 15，DF = 9，求 EF 的長度。
```

**輸出**：自動生成對應的圖表

```json
{
  "generated_diagram": {
    "diagram_type": "right_triangle",
    "image_path": "/generated/diagrams/triangle_002.png"
  }
}
```

---

## 功能需求

### FR-D01: 支援多種圖形類型

**優先級**: P0

**支援的圖形**:
- 三角形（直角、等腰、等邊、一般）
- 四邊形（正方形、矩形、平行四邊形、梯形）
- 圓形
- 函數圖（二次函數、三角函數等）
- 座標平面

### FR-D02: 自動標註

**優先級**: P0

**功能**:
- 自動標註頂點（A, B, C 或 自定義）
- 自動標註邊長
- 自動標註角度
- 自動標示直角符號、等長符號等

### FR-D03: 多種輸出格式

**優先級**: P1

**支援格式**:
1. **PNG 圖片** (必須) - 用於顯示
2. **SVG 向量圖** (建議) - 可縮放
3. **LaTeX TikZ 代碼** (建議) - 用於學術文件
4. **matplotlib 代碼** (可選) - 可編輯

### FR-D04: 風格一致性

**優先級**: P1

**要求**:
- 所有生成的圖表使用統一的字體
- 統一的線條粗細和顏色
- 統一的標註方式
- 符合台灣數學教科書慣例

---

## 技術實現

### 實現方式 1：使用 matplotlib（推薦）

**優點**:
- ✅ Python 原生，容易整合
- ✅ 可程式化控制
- ✅ 輸出 PNG/SVG
- ✅ 免費開源

**範例代碼**:

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def generate_right_triangle(vertices, labeled_sides, right_angle_at):
    """
    生成直角三角形圖表

    Args:
        vertices: {"A": [0, 0], "B": [10, 0], "C": [0, 6]}
        labeled_sides: {"AB": "10", "AC": "6"}
        right_angle_at: "C"

    Returns:
        image_path: 生成的圖片路徑
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # 繪製三角形
    triangle = patches.Polygon([
        vertices["A"], vertices["B"], vertices["C"]
    ], fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(triangle)

    # 標註頂點
    for vertex, pos in vertices.items():
        ax.text(pos[0], pos[1], vertex, fontsize=14,
                ha='center', va='center')

    # 標註邊長
    for edge, length in labeled_sides.items():
        # 計算邊的中點位置
        v1, v2 = edge[0], edge[1]
        mid_x = (vertices[v1][0] + vertices[v2][0]) / 2
        mid_y = (vertices[v1][1] + vertices[v2][1]) / 2
        ax.text(mid_x, mid_y, length, fontsize=12)

    # 標示直角符號
    if right_angle_at:
        # 繪製直角符號
        pass

    # 設定座標軸
    ax.set_aspect('equal')
    ax.axis('off')

    # 儲存
    image_path = f"/generated/diagrams/triangle_{uuid.uuid4()}.png"
    plt.savefig(image_path, dpi=300, bbox_inches='tight')
    plt.close()

    return image_path
```

---

### 實現方式 2：使用 LaTeX TikZ

**優點**:
- ✅ 學術標準
- ✅ 高品質輸出
- ✅ 可直接用於論文

**缺點**:
- ❌ 需要 LaTeX 環境
- ❌ 生成較慢

**範例代碼**:

```latex
\begin{tikzpicture}
  % 定義頂點
  \coordinate (A) at (0,0);
  \coordinate (B) at (10,0);
  \coordinate (C) at (0,6);

  % 繪製三角形
  \draw[thick] (A) -- (B) -- (C) -- cycle;

  % 標註頂點
  \node[below left] at (A) {$A$};
  \node[below right] at (B) {$B$};
  \node[above left] at (C) {$C$};

  % 標註邊長
  \node at ($(A)!0.5!(B)$) [below] {10};
  \node at ($(A)!0.5!(C)$) [left] {6};

  % 直角符號
  \draw (A) rectangle +(0.5,0.5);
\end{tikzpicture}
```

---

### 實現方式 3：使用 GPT-4 Vision + Code Interpreter

**優點**:
- ✅ 高度自動化
- ✅ 可處理複雜圖形
- ✅ 自然語言描述即可

**缺點**:
- ❌ 需要 API 費用
- ❌ 較慢

**使用方式**:

```python
def generate_diagram_with_gpt(description):
    """
    使用 GPT-4 生成圖表代碼

    Args:
        description: "直角三角形 ABC，∠C=90°，AB=10，AC=6"

    Returns:
        matplotlib_code: 生成的 Python 代碼
    """
    prompt = f"""
    請用 matplotlib 生成以下數學圖表：
    {description}

    要求：
    1. 使用中文標註
    2. 清晰的線條和標籤
    3. 適當的比例
    4. 標準的數學符號

    請直接提供可執行的 Python 代碼。
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

---

## API 設計

### 主要函數

```python
def generate_diagram(
    diagram_spec: dict,
    output_format: str = "png",
    style: str = "standard"
) -> dict:
    """
    生成數學圖表

    Args:
        diagram_spec: 圖表規格
        {
          "type": "right_triangle",
          "vertices": {"A": [0,0], "B": [10,0], "C": [0,6]},
          "labeled_sides": {"AB": "10", "AC": "6"},
          "right_angle_at": "C"
        }

        output_format: 輸出格式 ("png", "svg", "tikz", "matplotlib")
        style: 風格 ("standard", "textbook", "minimal")

    Returns:
        {
          "success": true,
          "image_path": "/generated/diagrams/xxx.png",
          "code": "...",  # 如果需要
          "format": "png"
        }
    """
    pass
```

---

## 整合方式

### 與 Rephrase Agent 整合

```python
# Rephrase Agent 生成新題目
rephrased_problem = {
    "content": "在直角三角形 DEF 中，∠F = 90°，DE = 15，DF = 9，求 EF 的長度。",
    "needs_diagram": true,
    "original_diagram_analysis": {...}
}

# 如果需要圖表，調用圖表生成器
if rephrased_problem["needs_diagram"]:
    diagram = generate_diagram_for_problem(
        problem_content=rephrased_problem["content"],
        original_analysis=rephrased_problem["original_diagram_analysis"]
    )

    rephrased_problem["diagram_path"] = diagram["image_path"]
```

---

## 測試需求

### 測試案例

1. **基本三角形生成**
   - 輸入：直角三角形規格
   - 驗證：生成的圖片包含正確的頂點和邊長標註

2. **圖形類型支援**
   - 驗證：所有支援的圖形類型都能正確生成

3. **標註準確性**
   - 驗證：標註位置合理，不重疊

4. **風格一致性**
   - 驗證：多次生成的圖表風格一致

---

## 實現優先級

| 功能 | 優先級 | 預計時間 |
|------|--------|---------|
| 基礎三角形生成 (matplotlib) | P0 | 4 小時 |
| 其他基本圖形 | P0 | 3 小時 |
| 自動標註系統 | P0 | 3 小時 |
| SVG 輸出 | P1 | 2 小時 |
| TikZ 代碼生成 | P2 | 4 小時 |
| 函數圖表支援 | P2 | 6 小時 |

---

## 總結

圖表生成功能將在**題目生成階段**實現，與 OCR 階段的圖表分析功能互補：

1. **OCR 階段** (Task 1.4)：理解原題的圖表
2. **生成階段** (未來 Task)：根據理解生成新的圖表

這種分離式設計可以：
- ✅ 降低 OCR 階段的複雜度
- ✅ 提高系統的模組化程度
- ✅ 更好地控制成本（OCR 不需要生成功能）
