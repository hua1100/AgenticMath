"""
深度調試 PaddleOCR - 查看原始輸出

使用方法:
    python tests/debug_paddleocr.py <image_path>
"""

import sys
from pathlib import Path
import cv2
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


def debug_paddleocr(image_path: str):
    """深度調試 PaddleOCR"""
    print(f"\n{'='*80}")
    print(f"  PaddleOCR 深度調試")
    print(f"{'='*80}\n")

    # 讀取圖片
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 無法讀取圖片: {image_path}")
        return

    print(f"✅ 圖片信息:")
    print(f"   尺寸: {image.shape[1]} x {image.shape[0]}")
    print(f"   通道: {image.shape[2] if len(image.shape) > 2 else 1}")

    # 初始化 PaddleOCR
    print(f"\n⏳ 初始化 PaddleOCR...")
    try:
        from paddleocr import PaddleOCR

        # 嘗試不同配置
        configs = [
            {"name": "預設配置", "params": {"lang": "ch"}},
            {"name": "繁體中文", "params": {"lang": "chinese_cht"}},
            {"name": "降低閾值", "params": {"lang": "ch", "det_db_thresh": 0.2, "det_db_box_thresh": 0.3}},
        ]

        for config in configs:
            print(f"\n{'─'*80}")
            print(f"測試配置: {config['name']}")
            print(f"{'─'*80}")

            try:
                ocr = PaddleOCR(use_angle_cls=False, **config['params'])
                result = ocr.ocr(image_path)

                print(f"\n原始輸出:")
                print(f"  類型: {type(result)}")
                print(f"  內容: {result}")

                if result and result[0]:
                    print(f"\n✅ 識別到 {len(result[0])} 個文字區域:")
                    for i, line in enumerate(result[0][:5], 1):
                        print(f"\n  區域 {i}:")
                        print(f"    Bounding Box: {line[0]}")
                        print(f"    文字: {line[1][0]}")
                        print(f"    信心度: {line[1][1]:.2%}")

                    if len(result[0]) > 5:
                        print(f"\n  ... 還有 {len(result[0]) - 5} 個區域")
                else:
                    print(f"\n⚠️  沒有識別到任何文字區域")
                    print(f"  result 為空或 result[0] 為空")

            except Exception as e:
                print(f"❌ 錯誤: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"❌ PaddleOCR 初始化失敗: {e}")
        import traceback
        traceback.print_exc()


def analyze_image_for_text(image_path: str):
    """分析圖片是否適合 OCR"""
    print(f"\n{'='*80}")
    print(f"  圖片文字適合度分析")
    print(f"{'='*80}\n")

    image = cv2.imread(image_path)
    if image is None:
        return

    # 轉灰階
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) > 2 else image

    # 分析亮度分布
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)

    print(f"亮度分析:")
    print(f"  平均亮度: {mean_brightness:.1f}/255")
    print(f"  亮度標準差: {std_brightness:.1f}")

    if std_brightness < 20:
        print(f"  ⚠️  對比度很低，可能影響文字識別")

    # 計算邊緣
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = np.sum(edges > 0) / edges.size

    print(f"\n邊緣分析:")
    print(f"  邊緣像素比例: {edge_ratio:.2%}")

    if edge_ratio < 0.05:
        print(f"  ⚠️  邊緣太少，可能沒有清晰的文字")
    elif edge_ratio > 0.30:
        print(f"  ⚠️  邊緣太多，可能是複雜圖表")

    # 嘗試二值化
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 計算連通組件
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    # 過濾太小或太大的組件
    text_like_components = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        width = stats[i, cv2.CC_STAT_WIDTH]
        height = stats[i, cv2.CC_STAT_HEIGHT]

        # 文字特徵：面積適中，長寬比合理
        if 50 < area < 5000 and 0.1 < height/width < 10:
            text_like_components += 1

    print(f"\n連通組件分析:")
    print(f"  總組件數: {num_labels - 1}")
    print(f"  類文字組件: {text_like_components}")

    if text_like_components < 5:
        print(f"  ⚠️  類文字組件太少，圖片可能主要是圖形")


def main():
    if len(sys.argv) < 2:
        print("使用方法: python tests/debug_paddleocr.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"❌ 圖片不存在: {image_path}")
        sys.exit(1)

    # 1. 分析圖片
    analyze_image_for_text(image_path)

    # 2. 測試 PaddleOCR
    debug_paddleocr(image_path)

    print(f"\n{'='*80}")
    print(f"  調試完成")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
