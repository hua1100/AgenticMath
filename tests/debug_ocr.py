"""
OCR 調試腳本 - 幫助診斷 OCR 處理問題

使用方法:
    python tests/debug_ocr.py <image_path>

例如:
    python tests/debug_ocr.py tests/fixtures/diagrams/test.png
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import cv2
import numpy as np

load_dotenv()


def check_image(image_path: str):
    """檢查圖片基本信息"""
    print(f"\n{'='*80}")
    print(f"  圖片檢查")
    print(f"{'='*80}\n")

    path = Path(image_path)

    # 1. 檢查文件存在
    if not path.exists():
        print(f"❌ 文件不存在: {image_path}")
        return False

    print(f"✅ 文件存在: {image_path}")
    print(f"   文件大小: {path.stat().st_size:,} bytes")

    # 2. 檢查能否用 OpenCV 讀取
    image = cv2.imread(str(path))
    if image is None:
        print(f"❌ 無法用 OpenCV 讀取圖片")
        return False

    print(f"✅ OpenCV 可讀取")
    print(f"   圖片尺寸: {image.shape[1]} x {image.shape[0]} pixels")
    print(f"   色彩通道: {image.shape[2] if len(image.shape) > 2 else 1}")

    # 3. 檢查圖片是否太大或太小
    height, width = image.shape[:2]
    if width < 50 or height < 50:
        print(f"⚠️  圖片太小，OCR 可能識別不出文字")
    elif width > 4000 or height > 4000:
        print(f"⚠️  圖片很大，OCR 處理可能較慢")
    else:
        print(f"✅ 圖片尺寸適中")

    # 4. 檢查圖片亮度和對比度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) > 2 else image
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)

    print(f"   平均亮度: {mean_brightness:.1f}/255")
    print(f"   亮度標準差: {std_brightness:.1f}")

    if mean_brightness < 30:
        print(f"⚠️  圖片太暗，可能影響 OCR 識別")
    elif mean_brightness > 225:
        print(f"⚠️  圖片太亮，可能影響 OCR 識別")

    if std_brightness < 10:
        print(f"⚠️  對比度很低，可能影響 OCR 識別")

    return True


def test_preprocessing(image_path: str):
    """測試圖片預處理"""
    print(f"\n{'='*80}")
    print(f"  預處理測試")
    print(f"{'='*80}\n")

    try:
        from src.ocr import preprocess_image

        result = preprocess_image(image_path)

        if result["success"]:
            print(f"✅ 預處理成功")
            print(f"   應用步驟: {result['preprocessing_applied']}")
            print(f"   處理時間: {result['processing_time_ms']}ms")
            print(f"   旋轉角度: {result['rotation_angle']:.2f}°")
            return True
        else:
            print(f"❌ 預處理失敗")
            return False

    except Exception as e:
        print(f"❌ 預處理錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr(image_path: str):
    """測試 OCR 文字提取"""
    print(f"\n{'='*80}")
    print(f"  OCR 文字提取測試")
    print(f"{'='*80}\n")

    try:
        from src.ocr import extract_text

        print(f"⏳ 初始化 PaddleOCR（首次運行需要下載模型，可能需要幾分鐘）...")
        result = extract_text(image_path)

        if result["success"]:
            print(f"✅ OCR 成功")
            print(f"   識別出文字: {result['has_text']}")
            print(f"   文字區域數: {result['num_regions']}")
            print(f"   平均信心度: {result['confidence_score']:.2%}")
            print(f"   處理時間: {result['processing_time_ms']}ms")

            if result["text"]:
                print(f"\n   提取的文字:")
                for i, line in enumerate(result["text"].split('\n')[:5], 1):
                    print(f"   {i}. {line}")
                if result["num_regions"] > 5:
                    print(f"   ... 還有 {result['num_regions'] - 5} 行")
            else:
                print(f"⚠️  沒有提取到文字")

            return True
        else:
            print(f"❌ OCR 失敗")
            return False

    except Exception as e:
        print(f"❌ OCR 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline(image_path: str):
    """測試完整 OCR Pipeline"""
    print(f"\n{'='*80}")
    print(f"  完整 OCR Pipeline 測試")
    print(f"{'='*80}\n")

    try:
        from src.ocr import process_image
        from uuid import uuid4

        image_id = uuid4()
        print(f"⏳ 執行完整 Pipeline（預處理 → OCR → 圖表分析）...")
        result = process_image(image_id, image_path)

        print(f"\n📊 Pipeline 結果:")
        print(f"   成功: {result['success']}")

        if result['success']:
            print(f"   提取文字: {result['extracted_text'][:100]}{'...' if len(result['extracted_text']) > 100 else ''}")
            print(f"   信心度: {result['confidence_score']:.2%}")
            print(f"   包含圖表: {result['contains_diagram']}")
            print(f"   處理時間: {result['processing_time_ms']}ms")
            print(f"   預處理步驟: {result['preprocessing_applied']}")

            if result.get('warnings'):
                print(f"\n   ⚠️  警告:")
                for warning in result['warnings']:
                    print(f"      - {warning}")

            return True
        else:
            print(f"   錯誤代碼: {result.get('error_code')}")
            print(f"   錯誤訊息: {result.get('error_message')}")
            return False

    except Exception as e:
        print(f"❌ Pipeline 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("使用方法: python tests/debug_ocr.py <image_path>")
        print("\n例如:")
        print("  python tests/debug_ocr.py tests/fixtures/diagrams/triangle.jpg")
        print("  python tests/debug_ocr.py tests/fixtures/diagrams/test.png")
        sys.exit(1)

    image_path = sys.argv[1]

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                          OCR 調試工具                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # 1. 檢查圖片
    if not check_image(image_path):
        print(f"\n❌ 圖片檢查失敗，無法繼續")
        sys.exit(1)

    # 2. 測試預處理
    preprocessing_ok = test_preprocessing(image_path)

    # 3. 測試 OCR
    ocr_ok = test_ocr(image_path)

    # 4. 測試完整 Pipeline
    pipeline_ok = test_full_pipeline(image_path)

    # 總結
    print(f"\n{'='*80}")
    print(f"  調試總結")
    print(f"{'='*80}\n")

    print(f"   圖片檢查: ✅")
    print(f"   預處理: {'✅' if preprocessing_ok else '❌'}")
    print(f"   OCR 提取: {'✅' if ocr_ok else '❌'}")
    print(f"   完整 Pipeline: {'✅' if pipeline_ok else '❌'}")

    if pipeline_ok:
        print(f"\n✅ 所有測試通過！您的 OCR 環境配置正確。")
        sys.exit(0)
    else:
        print(f"\n⚠️  部分測試失敗，請查看上面的錯誤信息。")
        print(f"\n常見問題:")
        print(f"  1. 如果提示「No available model hosting platforms」：")
        print(f"     - 確保網絡連接正常")
        print(f"     - 首次運行需要下載 PaddleOCR 模型")
        print(f"  2. 如果識別不出文字：")
        print(f"     - 檢查圖片是否清晰")
        print(f"     - 檢查圖片對比度是否足夠")
        print(f"     - 嘗試使用其他測試圖片")
        sys.exit(1)


if __name__ == "__main__":
    main()
