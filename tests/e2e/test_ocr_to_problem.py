"""
端到端測試：OCR to Problem 完整工作流程

此測試涵蓋：
1. 圖片上傳 (模擬)
2. OCR 處理（預處理 → 文字提取 → 圖表分析）
3. Problem 創建
4. 資料庫儲存

需求：
- PaddleOCR 已安裝
- .env 文件已配置
- 資料庫已初始化
"""

import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# 添加專案根目錄到 Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 載入環境變數
load_dotenv()

# 導入模組
from src.storage.database import get_db, init_db, Base, engine
from src.models.uploaded_image import UploadedImage, ImageFormat
from src.ocr import process_image
from src.orchestration import create_problem_from_ocr
from src.models.problem import Problem, MathDomain, ProblemSource, SourceType


def print_section(title: str):
    """印出區段標題"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def check_environment():
    """檢查環境配置"""
    print_section("環境檢查")

    issues = []

    # 檢查 .env 文件
    env_file = project_root / ".env"
    if not env_file.exists():
        issues.append("❌ .env 文件不存在")
        print(f"請複製 .env.example 到 .env 並填入配置")
    else:
        print(f"✅ .env 文件存在")

    # 檢查 OpenAI API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-api-key-here":
        print(f"⚠️  OPENAI_API_KEY 未設定（圖表分析將被跳過）")
    else:
        print(f"✅ OPENAI_API_KEY 已設定")

    # 檢查 PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print(f"✅ PaddleOCR 已安裝")
    except ImportError:
        issues.append("❌ PaddleOCR 未安裝")
        print(f"請執行: pip install paddleocr paddlepaddle")

    # 檢查上傳目錄
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    if not upload_dir.exists():
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 創建上傳目錄: {upload_dir}")
    else:
        print(f"✅ 上傳目錄存在: {upload_dir}")

    if issues:
        print(f"\n❌ 發現問題:")
        for issue in issues:
            print(f"   {issue}")
        return False

    print(f"\n✅ 環境檢查通過！")
    return True


def init_database():
    """初始化資料庫"""
    print_section("資料庫初始化")

    try:
        # 創建所有表格
        Base.metadata.create_all(bind=engine)
        print(f"✅ 資料庫表格創建成功")
        return True
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
        return False


def create_test_image(db: Session) -> UploadedImage:
    """創建測試用的 UploadedImage 記錄"""
    print_section("創建測試圖片記錄")

    # 使用現有的測試圖片
    test_image_path = project_root / "tests" / "fixtures" / "diagrams" / "triangle.jpg"

    if not test_image_path.exists():
        raise FileNotFoundError(f"測試圖片不存在: {test_image_path}")

    # 創建 UploadedImage 記錄
    uploaded_image = UploadedImage(
        file_path=str(test_image_path),
        file_size=test_image_path.stat().st_size,
        file_format=ImageFormat.JPEG,
        upload_timestamp=datetime.now(),
        ocr_extracted_text="",  # OCR 後會更新
        ocr_confidence_score=0.0,
        contains_diagram=False,
        preprocessing_applied=[],
        ocr_processing_time_ms=0,
    )

    db.add(uploaded_image)
    db.commit()
    db.refresh(uploaded_image)

    print(f"✅ 測試圖片記錄已創建")
    print(f"   ID: {uploaded_image.id}")
    print(f"   Path: {uploaded_image.file_path}")
    print(f"   Size: {uploaded_image.file_size} bytes")

    return uploaded_image


def test_ocr_pipeline(image_id, file_path):
    """測試 OCR Pipeline"""
    print_section("OCR Pipeline 測試")

    print(f"處理圖片: {file_path}")
    print(f"圖片 ID: {image_id}")

    # 執行 OCR
    print(f"\n⏳ 執行 OCR 處理...")
    result = process_image(image_id, file_path)

    # 顯示結果
    print(f"\n📊 OCR 結果:")
    print(f"   成功: {result['success']}")

    if result['success']:
        print(f"   提取文字: {result['extracted_text'][:100]}...")
        print(f"   信心度: {result['confidence_score']:.2%}")
        print(f"   包含圖表: {result['contains_diagram']}")
        if result['contains_diagram']:
            print(f"   圖表描述: {result.get('diagram_description')}")
        print(f"   處理時間: {result['processing_time_ms']}ms")
        print(f"   預處理步驟: {result['preprocessing_applied']}")
    else:
        print(f"   錯誤代碼: {result.get('error_code')}")
        print(f"   錯誤訊息: {result.get('error_message')}")

    return result


def test_problem_creation(ocr_result, image_id, db):
    """測試 Problem 創建"""
    print_section("Problem 創建測試")

    if not ocr_result['success']:
        print(f"❌ OCR 失敗，無法創建 Problem")
        return None

    print(f"⏳ 從 OCR 結果創建 Problem...")
    problem = create_problem_from_ocr(ocr_result, image_id, db)

    print(f"\n📝 Problem 創建成功!")
    print(f"   ID: {problem.id}")
    print(f"   內容: {problem.content[:100]}...")
    print(f"   領域: {problem.domain.value}")
    print(f"   能力: {problem.competencies}")
    print(f"   難度: {problem.baseline_difficulty}/5")
    print(f"   來源: {problem.source.value}")
    print(f"   來源類型: {problem.source_type.value}")
    print(f"   關聯圖片 ID: {problem.uploaded_image_id}")

    return problem


def verify_database_state(db: Session, image_id, problem_id):
    """驗證資料庫狀態"""
    print_section("資料庫狀態驗證")

    # 查詢 UploadedImage
    uploaded_image = db.query(UploadedImage).filter_by(id=image_id).first()
    if uploaded_image:
        print(f"✅ UploadedImage 記錄存在")
        print(f"   OCR 文字: {uploaded_image.ocr_extracted_text[:50]}...")
        print(f"   OCR 信心度: {uploaded_image.ocr_confidence_score:.2%}")
        print(f"   關聯 Problem ID: {uploaded_image.problem_id}")
    else:
        print(f"❌ UploadedImage 記錄不存在")

    # 查詢 Problem
    problem = db.query(Problem).filter_by(id=problem_id).first()
    if problem:
        print(f"\n✅ Problem 記錄存在")
        print(f"   內容: {problem.content[:50]}...")
        print(f"   領域: {problem.domain.value}")
        print(f"   關聯圖片 ID: {problem.uploaded_image_id}")
    else:
        print(f"❌ Problem 記錄不存在")

    # 驗證雙向關聯
    if uploaded_image and problem:
        if uploaded_image.problem_id == problem.id and problem.uploaded_image_id == uploaded_image.id:
            print(f"\n✅ 雙向關聯正確")
        else:
            print(f"\n❌ 雙向關聯錯誤")


def run_end_to_end_test():
    """執行完整的端到端測試"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   AgenticMath - OCR to Problem 端到端測試                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # 1. 環境檢查
    if not check_environment():
        print(f"\n❌ 環境檢查失敗，請修正後再試")
        return False

    # 2. 資料庫初始化
    if not init_database():
        print(f"\n❌ 資料庫初始化失敗")
        return False

    # 3. 創建資料庫 session
    db = next(get_db())

    try:
        # 4. 創建測試圖片記錄
        uploaded_image = create_test_image(db)

        # 5. 測試 OCR Pipeline
        ocr_result = test_ocr_pipeline(uploaded_image.id, uploaded_image.file_path)

        # 6. 測試 Problem 創建
        problem = test_problem_creation(ocr_result, uploaded_image.id, db)

        if problem:
            # 7. Commit 所有變更
            db.commit()

            # 8. 驗證資料庫狀態
            verify_database_state(db, uploaded_image.id, problem.id)

            print_section("測試總結")
            print(f"✅ 端到端測試成功完成！")
            print(f"\n完整流程:")
            print(f"   圖片 → OCR → Problem → 資料庫")
            print(f"\n創建的資源:")
            print(f"   UploadedImage ID: {uploaded_image.id}")
            print(f"   Problem ID: {problem.id}")

            return True
        else:
            print_section("測試總結")
            print(f"❌ Problem 創建失敗")
            return False

    except Exception as e:
        print_section("錯誤")
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = run_end_to_end_test()
    sys.exit(0 if success else 1)
