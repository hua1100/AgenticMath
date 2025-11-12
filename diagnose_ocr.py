#!/usr/bin/env python3
"""
診斷 OCR 問題的腳本

這個腳本會：
1. 檢查圖片是否可讀取
2. 顯示圖片資訊
3. 嘗試用最簡單的 PaddleOCR 配置處理圖片
"""

import sys
import cv2
import time
from pathlib import Path


def diagnose_image(image_path: str):
    """診斷圖片"""
    print("=" * 80)
    print("  🔍 OCR 診斷工具")
    print("=" * 80)
    print()

    # 檢查檔案存在
    path = Path(image_path)
    print(f"📂 圖片路徑: {path}")

    if not path.exists():
        print(f"❌ 錯誤：檔案不存在")
        return False

    print(f"✅ 檔案存在")
    print(f"   大小: {path.stat().st_size / 1024:.2f} KB")
    print()

    # 嘗試讀取圖片
    print("📖 讀取圖片...")
    image = cv2.imread(str(path))

    if image is None:
        print(f"❌ 錯誤：無法讀取圖片（可能格式不支援）")
        return False

    print(f"✅ 圖片讀取成功")
    print(f"   尺寸: {image.shape[1]} x {image.shape[0]}")
    print(f"   通道: {image.shape[2] if len(image.shape) > 2 else 1}")
    print()

    # 嘗試使用 PaddleOCR
    print("🔧 初始化 PaddleOCR（最簡配置）...")
    try:
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(
            lang='chinese_cht',
            use_angle_cls=False,
            use_gpu=False,
            show_log=False,
        )
        print("✅ PaddleOCR 初始化成功")
        print()

        # 嘗試 OCR
        print("⏳ 開始 OCR 處理（請等待最多 60 秒）...")
        print("   如果卡住超過 60 秒，請按 Ctrl+C 中斷")
        print()

        start_time = time.time()
        result = ocr.ocr(str(path))
        elapsed_time = time.time() - start_time

        print(f"✅ OCR 完成！耗時: {elapsed_time:.2f} 秒")
        print()

        # 顯示結果
        if result and result[0]:
            print(f"📝 識別結果:")
            print(f"   識別到 {len(result[0])} 個文字區域")
            print()

            for i, line in enumerate(result[0][:5], 1):  # 只顯示前 5 個
                if isinstance(line, list) and len(line) >= 2:
                    text = line[1][0] if isinstance(line[1], tuple) else str(line[1])
                    conf = line[1][1] if isinstance(line[1], tuple) and len(line[1]) > 1 else 0.0
                    print(f"   {i}. \"{text}\" (信心度: {conf:.2f})")

            if len(result[0]) > 5:
                print(f"   ... 還有 {len(result[0]) - 5} 個區域")
        else:
            print("⚠️  沒有識別到文字")

        return True

    except KeyboardInterrupt:
        print()
        print("⚠️  用戶中斷")
        return False
    except Exception as e:
        print(f"❌ OCR 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python diagnose_ocr.py <圖片路徑>")
        print("範例: python diagnose_ocr.py tests/fixtures/diagrams/test.png")
        sys.exit(1)

    image_path = sys.argv[1]
    success = diagnose_image(image_path)

    print()
    print("=" * 80)
    if success:
        print("  ✅ 診斷完成 - OCR 可以正常處理這張圖片")
    else:
        print("  ⚠️  診斷發現問題 - 請檢查上面的錯誤訊息")
    print("=" * 80)

    sys.exit(0 if success else 1)
