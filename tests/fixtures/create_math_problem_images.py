"""
創建測試用的數學題目圖片

此腳本創建包含繁體中文數學題目的測試圖片，用於端到端測試。
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os


def create_math_problem_image(
    text: str,
    filename: str,
    width: int = 800,
    height: int = 600,
    include_diagram: bool = False
):
    """
    創建包含數學題目的圖片

    Args:
        text: 題目文字
        filename: 輸出檔名
        width: 圖片寬度
        height: 圖片高度
        include_diagram: 是否包含簡單圖形
    """
    # 創建白色背景圖片
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # 使用預設字體（如果有系統字體更好）
    try:
        # 嘗試使用中文字體
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        # 降級到預設字體
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()

    # 繪製題目文字
    y_position = 50
    for line in text.split('\n'):
        draw.text((50, y_position), line, fill='black', font=font_medium)
        y_position += 40

    # 如果需要，繪製簡單圖形
    if include_diagram:
        # 繪製直角三角形
        triangle_points = [
            (500, 400),  # 右下角
            (500, 250),  # 右上角
            (350, 400),  # 左下角
        ]
        draw.polygon(triangle_points, outline='black', width=3)

        # 標註頂點
        draw.text((490, 240), "A", fill='black', font=font_large)
        draw.text((340, 410), "B", fill='black', font=font_large)
        draw.text((510, 410), "C", fill='black', font=font_large)

        # 標註邊長
        draw.text((420, 320), "10", fill='blue', font=font_medium)
        draw.text((520, 320), "6", fill='blue', font=font_medium)

        # 繪製直角標記
        draw.line([(485, 400), (485, 385)], fill='black', width=2)
        draw.line([(485, 385), (500, 385)], fill='black', width=2)

    # 儲存圖片
    output_path = Path(__file__).parent / "math_problems" / filename
    output_path.parent.mkdir(exist_ok=True)
    img.save(output_path, 'JPEG', quality=95)
    print(f"✅ 創建圖片: {output_path}")


def main():
    """創建各種測試圖片"""
    print("創建測試用數學題目圖片...\n")

    # 1. 代數題目 - 簡單方程式
    create_math_problem_image(
        text="""題目 1：求解方程式

解方程式：2x + 5 = 13

請求出 x 的值。""",
        filename="algebra_simple.jpg",
        include_diagram=False
    )

    # 2. 幾何題目 - 直角三角形（含圖）
    create_math_problem_image(
        text="""題目 2：直角三角形

在直角三角形 ABC 中，角 C = 90度
已知 AB = 10，AC = 6
求 BC 的長度。""",
        filename="geometry_triangle.jpg",
        include_diagram=True
    )

    # 3. 機率題目
    create_math_problem_image(
        text="""題目 3：機率計算

一個袋子中有 5 個紅球和 3 個藍球。
隨機抽取 2 個球（不放回），
求抽到 2 個紅球的機率。""",
        filename="probability_balls.jpg",
        include_diagram=False
    )

    # 4. 數論題目
    create_math_problem_image(
        text="""題目 4：最大公因數

求 24 和 36 的最大公因數 (GCD)。

並求出它們的最小公倍數 (LCM)。""",
        filename="number_theory_gcd.jpg",
        include_diagram=False
    )

    # 5. 組合題目
    create_math_problem_image(
        text="""題目 5：排列組合

從 10 個人中選出 3 個人組成委員會，
有多少種不同的選法？

(使用組合公式計算)""",
        filename="combinatorics_committee.jpg",
        include_diagram=False
    )

    # 6. 複雜代數題目
    create_math_problem_image(
        text="""題目 6：聯立方程式

解聯立方程式：
x + 2y = 10
3x - y = 5

求 x 和 y 的值。""",
        filename="algebra_system.jpg",
        include_diagram=False
    )

    print(f"\n✅ 所有測試圖片創建完成！")
    print(f"位置: {Path(__file__).parent / 'math_problems'}")


if __name__ == "__main__":
    main()
