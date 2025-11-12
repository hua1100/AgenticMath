#!/usr/bin/env python3
"""
調試 PaddleOCR - 顯示詳細的 OCR 結果
"""

import sys
from paddleocr import PaddleOCR
import cv2

def debug_ocr(image_path: str):
    print("=" * 80)
    print("  🔍 PaddleOCR 調試工具")
    print("=" * 80)
    print()

    # 檢查圖片
    print(f"📂 圖片路徑: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 無法讀取圖片")
        return

    print(f"✅ 圖片讀取成功")
    print(f"   尺寸: {image.shape[1]} x {image.shape[0]}")
    print()

    # 測試多種語言配置
    configs = [
        {"lang": "chinese_cht", "name": "繁體中文"},
        {"lang": "ch", "name": "簡體中文"},
        {"lang": "en", "name": "英文"},
    ]

    for config in configs:
        print(f"{'=' * 80}")
        print(f"  測試配置: {config['name']} (lang={config['lang']})")
        print(f"{'=' * 80}")

        try:
            ocr = PaddleOCR(
                lang=config['lang'],
                use_angle_cls=False,
                use_gpu=False,
                show_log=False,
            )

            result = ocr.ocr(image_path)

            print(f"\n📊 原始返回結果:")
            print(f"   類型: {type(result)}")
            print(f"   長度: {len(result) if result else 0}")

            if result:
                print(f"\n   result[0] 類型: {type(result[0])}")
                print(f"   result[0] 長度: {len(result[0]) if result[0] else 0}")

                if result[0]:
                    print(f"\n📝 識別結果:")
                    for i, item in enumerate(result[0][:5], 1):
                        print(f"\n   [{i}] 類型: {type(item)}")
                        if isinstance(item, list) and len(item) >= 2:
                            bbox = item[0]
                            text_info = item[1]
                            print(f"       bbox: {bbox}")
                            print(f"       text_info: {text_info}")
                            if isinstance(text_info, tuple) and len(text_info) >= 2:
                                print(f"       文字: {text_info[0]}")
                                print(f"       信心度: {text_info[1]:.2f}")
                        elif isinstance(item, dict):
                            print(f"       內容: {item}")

                    if len(result[0]) > 5:
                        print(f"\n   ... 還有 {len(result[0]) - 5} 個結果")
                else:
                    print(f"\n   ⚠️  result[0] 是空的")
            else:
                print(f"\n   ⚠️  result 是空的")

        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()

        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_ocr_debug.py <圖片路徑>")
        sys.exit(1)

    debug_ocr(sys.argv[1])
