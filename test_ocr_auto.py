#!/usr/bin/env python
"""
自動化 OCR 測試腳本（非互動式）

使用方式：
    python test_ocr_auto.py
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.ocr.text_extractor import extract_text
import json


def main():
    """主程式 - 自動執行所有測試"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║      PaddleOCR 自動化測試工具（非互動式）                 ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # 測試圖片列表
    test_images = [
        ("simple_math.jpg", "數學題目圖片"),
        ("numbers.jpg", "數字圖片"),
        ("multi_line.jpg", "多行文字圖片"),
        ("empty.jpg", "空白圖片"),
    ]

    results = []
    success_count = 0
    total_count = 0

    print("🔍 開始測試所有圖片...")
    print("=" * 70)
    print()

    for filename, description in test_images:
        image_path = Path(f"tests/fixtures/images/{filename}")

        if not image_path.exists():
            print(f"⏭️  跳過：{filename} - 檔案不存在")
            continue

        print(f"📸 測試：{filename} ({description})")
        total_count += 1

        try:
            # 執行 OCR
            result = extract_text(image_path)

            # 顯示結果
            if result['success']:
                status = "✅ 成功"
                success_count += 1

                # 截斷過長的文字
                text_preview = result['text'][:60] if result['text'] else "（無文字）"
                if result['text'] and len(result['text']) > 60:
                    text_preview += "..."

                print(f"   {status}")
                print(f"   文字: {text_preview}")
                print(f"   信心分數: {result['confidence_score']:.2f}")
                print(f"   處理時間: {result['processing_time_ms']:.0f}ms")
            else:
                status = "❌ 失敗"
                print(f"   {status}")
                if 'error' in result:
                    print(f"   錯誤: {result['error']}")

            results.append({
                'filename': filename,
                'success': result['success'],
                'has_text': result.get('has_text', False),
                'confidence': result.get('confidence_score', 0.0),
                'time_ms': result.get('processing_time_ms', 0),
            })

        except Exception as e:
            print(f"   ❌ 執行失敗: {type(e).__name__}")
            print(f"   錯誤訊息: {str(e)[:100]}")
            results.append({
                'filename': filename,
                'success': False,
                'error': str(e)[:100]
            })

        print()

    # 顯示摘要
    print("=" * 70)
    print("📊 測試摘要")
    print("=" * 70)
    print(f"總測試數: {total_count}")
    print(f"成功: {success_count}")
    print(f"失敗: {total_count - success_count}")
    print(f"成功率: {(success_count / total_count * 100) if total_count > 0 else 0:.1f}%")
    print()

    # 詳細結果
    if results:
        print("📋 詳細結果:")
        print("-" * 70)
        for r in results:
            status_icon = "✅" if r['success'] else "❌"
            print(f"{status_icon} {r['filename']}")
            if r['success'] and 'confidence' in r:
                print(f"   信心分數: {r['confidence']:.2f}, 處理時間: {r['time_ms']:.0f}ms")
            elif 'error' in r:
                print(f"   錯誤: {r['error']}")
        print()

    # 返回狀態
    print("=" * 70)
    if success_count == total_count and total_count > 0:
        print("🎉 所有測試通過！OCR 功能運作正常")
        exit_code = 0
    elif success_count > 0:
        print("⚠️  部分測試通過")
        exit_code = 1
    else:
        print("❌ 所有測試失敗，請檢查環境設置")
        print()
        print("💡 可能的原因：")
        print("   1. 沒有網絡連接（首次使用需要下載 PaddleOCR 模型）")
        print("   2. 依賴未正確安裝")
        print()
        print("🔧 建議：")
        print("   1. 確認網絡連接")
        print("   2. 重新安裝依賴: pip install -r requirements-ocr-test.txt")
        exit_code = 1

    print("=" * 70)
    print()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
