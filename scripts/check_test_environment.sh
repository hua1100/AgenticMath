#!/bin/bash
# 檢查測試環境是否就緒

set -e

echo "=========================================================================="
echo "  AgenticMath - 測試環境檢查"
echo "=========================================================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

# 檢查函數
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((SUCCESS++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

# 1. 檢查 Python 版本
echo "1️⃣  檢查 Python 版本..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    check_pass "Python 版本: $PYTHON_VERSION (>= $REQUIRED_VERSION)"
else
    check_fail "Python 版本過舊: $PYTHON_VERSION (需要 >= $REQUIRED_VERSION)"
fi
echo ""

# 2. 檢查必要的 Python 套件
echo "2️⃣  檢查必要套件..."
REQUIRED_PACKAGES=(
    "paddleocr"
    "paddlepaddle"
    "opencv-python"
    "Pillow"
    "sqlalchemy"
    "pydantic"
    "python-dotenv"
    "openai"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python -c "import ${package//-/_}" 2>/dev/null; then
        check_pass "$package 已安裝"
    else
        check_fail "$package 未安裝"
    fi
done
echo ""

# 3. 檢查 .env 文件
echo "3️⃣  檢查環境配置..."
if [ -f ".env" ]; then
    check_pass ".env 文件存在"

    # 檢查重要配置
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        if grep -q "OPENAI_API_KEY=sk-your-api-key-here" .env; then
            check_warn "OPENAI_API_KEY 尚未設定（圖表分析將被跳過）"
        else
            check_pass "OPENAI_API_KEY 已設定"
        fi
    else
        check_warn "OPENAI_API_KEY 未設定"
    fi

    if grep -q "DATABASE_URL=" .env; then
        check_pass "DATABASE_URL 已設定"
    else
        check_warn "DATABASE_URL 未設定"
    fi
else
    check_fail ".env 文件不存在（請從 .env.example 複製）"
fi
echo ""

# 4. 檢查目錄結構
echo "4️⃣  檢查目錄結構..."
REQUIRED_DIRS=(
    "src/ocr"
    "src/orchestration"
    "src/models"
    "src/storage"
    "tests/e2e"
    "tests/fixtures"
    "uploads"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "目錄存在: $dir"
    else
        if [ "$dir" = "uploads" ]; then
            mkdir -p "$dir"
            check_pass "創建目錄: $dir"
        else
            check_fail "目錄不存在: $dir"
        fi
    fi
done
echo ""

# 5. 檢查資料庫
echo "5️⃣  檢查資料庫..."
if [ -f "agenticmath.db" ]; then
    check_pass "SQLite 資料庫存在"
else
    check_warn "資料庫不存在（將在首次運行時創建）"
fi
echo ""

# 6. 檢查測試圖片
echo "6️⃣  檢查測試圖片..."
if [ -d "tests/fixtures/diagrams" ]; then
    IMAGE_COUNT=$(ls tests/fixtures/diagrams/*.jpg 2>/dev/null | wc -l)
    if [ $IMAGE_COUNT -gt 0 ]; then
        check_pass "測試圖片: $IMAGE_COUNT 張"
    else
        check_warn "測試圖片目錄為空"
    fi
else
    check_fail "測試圖片目錄不存在"
fi
echo ""

# 總結
echo "=========================================================================="
echo "  檢查總結"
echo "=========================================================================="
echo -e "${GREEN}✅ 通過: $SUCCESS${NC}"
echo -e "${YELLOW}⚠️  警告: $WARNINGS${NC}"
echo -e "${RED}❌ 錯誤: $ERRORS${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 環境檢查完成，可以開始測試！${NC}"
    echo ""
    echo "執行測試："
    echo "  python tests/e2e/test_ocr_to_problem.py"
    exit 0
else
    echo -e "${RED}❌ 發現 $ERRORS 個錯誤，請修正後再試${NC}"
    echo ""
    echo "安裝缺少的套件："
    echo "  pip install -r requirements.txt"
    echo ""
    echo "創建 .env 文件："
    echo "  cp .env.example .env"
    echo "  # 然後編輯 .env 填入您的配置"
    exit 1
fi
