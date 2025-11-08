#!/bin/bash

# OCR 測試環境設置腳本
# 此腳本會創建一個乾淨的虛擬環境，只安裝 OCR 測試所需的依賴

set -e  # 遇到錯誤立即停止

echo "=========================================="
echo "OCR 測試環境設置"
echo "=========================================="
echo ""

# 檢查是否已在虛擬環境中
if [ -n "$VIRTUAL_ENV" ]; then
    echo "⚠️  警告：您目前在虛擬環境中： $VIRTUAL_ENV"
    echo "建議先退出虛擬環境 (執行 'deactivate')，讓腳本創建新環境"
    echo ""
    read -p "是否繼續？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 1
    fi
fi

# 步驟 1: 創建新的虛擬環境
echo "步驟 1/4: 創建虛擬環境 'venv-ocr-test'..."
python -m venv venv-ocr-test
echo "✅ 虛擬環境已創建"
echo ""

# 步驟 2: 啟動虛擬環境並升級 pip
echo "步驟 2/4: 升級 pip..."
./venv-ocr-test/bin/pip install --upgrade pip
echo "✅ pip 已升級"
echo ""

# 步驟 3: 安裝 OCR 測試依賴
echo "步驟 3/4: 安裝 OCR 測試依賴..."
echo "（這可能需要幾分鐘，請耐心等待）"
./venv-ocr-test/bin/pip install -r requirements-ocr-test.txt
echo "✅ 依賴已安裝"
echo ""

# 步驟 4: 驗證安裝
echo "步驟 4/4: 驗證安裝..."
./venv-ocr-test/bin/python -c "import paddleocr; print('✅ PaddleOCR 版本:', paddleocr.__version__)"
./venv-ocr-test/bin/python -c "import cv2; print('✅ OpenCV 版本:', cv2.__version__)"
./venv-ocr-test/bin/python -c "import numpy; print('✅ NumPy 版本:', numpy.__version__)"
./venv-ocr-test/bin/python -c "import pytest; print('✅ pytest 版本:', pytest.__version__)"
echo ""

echo "=========================================="
echo "✅ 設置完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 啟動虛擬環境："
echo "   source venv-ocr-test/bin/activate"
echo ""
echo "2. 執行 OCR 測試："
echo "   pytest tests/unit/test_text_extractor.py -v"
echo ""
echo "3. 測試完成後，退出虛擬環境："
echo "   deactivate"
echo ""
