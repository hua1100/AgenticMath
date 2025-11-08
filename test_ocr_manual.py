#!/usr/bin/env python
"""
手動測試 OCR 功能的腳本

使用方式：
    python test_ocr_manual.py

或者測試自己的圖片：
    python test_ocr_manual.py path/to/your/image.jpg
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.ocr.text_extractor import extract_text, OCRConfig
import json


def test_basic_ocr():
    """測試基本的 OCR 功能"""
    print("=" * 60)
    print("🧪 測試 1: 基本 OCR 功能")
    print("=" * 60)

    # 使用測試圖片
    test_image = Path("tests/fixtures/images/simple_math.jpg")

    if not test_image.exists():
        print(f"❌ 測試圖片不存在: {test_image}")
        print("   請先執行: python tests/fixtures/create_test_images.py")
        return False

    print(f"📸 測試圖片: {test_image}")
    print("⏳ 執行 OCR 識別...")
    print("   （首次執行會下載模型，約需 3-5 分鐘，請耐心等待）")
    print()

    try:
        # 執行 OCR
        result = extract_text(test_image)

        # 顯示結果
        print("✅ OCR 執行成功！")
        print()
        print("📊 識別結果:")
        print("-" * 60)
        print(f"成功: {result['success']}")
        print(f"是否有文字: {result['has_text']}")
        print(f"文字區域數量: {result['num_regions']}")
        print(f"信心分數: {result['confidence_score']:.2f}")
        print(f"處理時間: {result['processing_time_ms']:.0f} ms")
        print()
        print("📝 識別出的文字:")
        print("-" * 60)
        print(result['text'] if result['text'] else "（無文字）")
        print()

        if result['text_regions']:
            print("📍 文字區域詳情:")
            print("-" * 60)
            for i, region in enumerate(result['text_regions'], 1):
                print(f"{i}. 文字: {region.text}")
                print(f"   信心: {region.confidence:.2f}")
                print()

        return True

    except Exception as e:
        print(f"❌ OCR 執行失敗: {type(e).__name__}")
        print(f"   錯誤訊息: {e}")
        print()
        print("💡 可能的原因:")
        print("   1. 沒有網絡連接（首次使用需要下載模型）")
        print("   2. PaddlePaddle 安裝不正確")
        print("   3. 圖片格式不支援")
        print()
        print("🔧 建議:")
        print("   1. 確認網絡連接正常")
        print("   2. 檢查是否已安裝所有依賴: pip install -r requirements-ocr-test.txt")
        print("   3. 查看完整錯誤訊息（上方）")
        return False


def test_custom_image(image_path):
    """測試自定義圖片"""
    print("=" * 60)
    print("🧪 測試自定義圖片")
    print("=" * 60)

    image_path = Path(image_path)

    if not image_path.exists():
        print(f"❌ 圖片不存在: {image_path}")
        return False

    print(f"📸 圖片路徑: {image_path}")
    print("⏳ 執行 OCR 識別...")
    print()

    try:
        # 執行 OCR
        result = extract_text(image_path)

        # 顯示結果
        print("✅ OCR 執行成功！")
        print()
        print("📝 識別出的文字:")
        print("-" * 60)
        print(result['text'] if result['text'] else "（無文字）")
        print()
        print(f"信心分數: {result['confidence_score']:.2f}")
        print(f"文字區域: {result['num_regions']}")
        print(f"處理時間: {result['processing_time_ms']:.0f} ms")

        return True

    except Exception as e:
        print(f"❌ OCR 執行失敗: {type(e).__name__}: {e}")
        return False


def test_all_test_images():
    """測試所有測試圖片"""
    print("=" * 60)
    print("🧪 測試所有測試圖片")
    print("=" * 60)
    print()

    test_images = [
        "tests/fixtures/images/simple_math.jpg",
        "tests/fixtures/images/numbers.jpg",
        "tests/fixtures/images/multi_line.jpg",
        "tests/fixtures/images/empty.jpg",
    ]

    results = []

    for image_path in test_images:
        image_path = Path(image_path)

        if not image_path.exists():
            print(f"⏭️  跳過不存在的圖片: {image_path.name}")
            continue

        print(f"📸 測試: {image_path.name}")

        try:
            result = extract_text(image_path)
            status = "✅" if result['success'] else "❌"
            print(f"   {status} 識別文字: {result['text'][:50] if result['text'] else '（無文字）'}")
            print(f"   信心分數: {result['confidence_score']:.2f}, 處理時間: {result['processing_time_ms']:.0f}ms")
            results.append(True)
        except Exception as e:
            print(f"   ❌ 失敗: {type(e).__name__}")
            results.append(False)

        print()

    # 摘要
    success_count = sum(results)
    total_count = len(results)
    print("=" * 60)
    print(f"📊 測試摘要: {success_count}/{total_count} 成功")
    print("=" * 60)

    return all(results)


def main():
    """主程式"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         PaddleOCR 功能手動測試工具                        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # 檢查命令行參數
    if len(sys.argv) > 1:
        # 測試自定義圖片
        image_path = sys.argv[1]
        success = test_custom_image(image_path)
    else:
        # 執行基本測試
        print("📋 測試選項:")
        print("   1. 測試單一圖片（simple_math.jpg）")
        print("   2. 測試所有測試圖片")
        print()

        choice = input("請選擇 (1/2) [預設: 1]: ").strip() or "1"
        print()

        if choice == "2":
            success = test_all_test_images()
        else:
            success = test_basic_ocr()

    print()
    print("=" * 60)
    if success:
        print("🎉 測試完成！OCR 功能運作正常")
    else:
        print("⚠️  測試未完全通過，請檢查錯誤訊息")
    print("=" * 60)
    print()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
