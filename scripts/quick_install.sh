#!/bin/bash
#
# AgenticMath 快速安裝腳本
#
# 用法: ./scripts/quick_install.sh
#
# 此腳本會：
# 1. 檢查系統環境
# 2. 安裝系統依賴
# 3. 創建虛擬環境
# 4. 安裝 Python 依賴
# 5. 運行依賴驗證
# 6. 設置配置文件
#

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢測操作系統
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$(echo $DISTRIB_ID | tr '[:upper:]' '[:lower:]')
        VER=$DISTRIB_RELEASE
    else
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
        VER=$(uname -r)
    fi

    echo "$OS"
}

echo "========================================="
echo "  AgenticMath 快速安裝"
echo "========================================="
echo ""

# 步驟 1: 檢查 Python 版本
log_info "步驟 1/7: 檢查 Python 版本"

if ! command -v python3.11 &> /dev/null; then
    log_error "Python 3.11 未安裝"
    echo ""
    echo "請先安裝 Python 3.11："
    echo "  Ubuntu/Debian: sudo apt install python3.11 python3.11-venv python3.11-dev"
    echo "  macOS: brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3.11 --version)
log_success "發現 $PYTHON_VERSION"

# 步驟 2: 檢測操作系統並安裝系統依賴
log_info "步驟 2/7: 安裝系統依賴"

OS_TYPE=$(detect_os)
log_info "檢測到操作系統: $OS_TYPE"

case $OS_TYPE in
    ubuntu|debian)
        log_info "使用 apt 安裝依賴..."

        # 檢查是否有 sudo 權限
        if ! sudo -v; then
            log_error "需要 sudo 權限來安裝系統依賴"
            exit 1
        fi

        # 更新包列表
        sudo apt-get update

        # 安裝依賴
        sudo apt-get install -y \
            build-essential \
            cmake \
            git \
            wget \
            libpq-dev \
            libgomp1 \
            libglib2.0-0 \
            libgthread-2.0-0 \
            libsm6 \
            libxext6 \
            libxrender-dev \
            libxrender1 \
            libfontconfig1 \
            libice6 \
            libgl1-mesa-glx \
            libgl1-mesa-dev \
            libglu1-mesa \
            libglu1-mesa-dev \
            libjpeg-dev \
            libpng-dev \
            libtiff-dev \
            libwebp-dev \
            libavcodec-dev \
            libavformat-dev \
            libswscale-dev \
            libv4l-dev \
            libxvidcore-dev \
            libx264-dev \
            libatlas-base-dev \
            gfortran \
            fonts-liberation \
            fonts-noto-cjk \
            fonts-wqy-zenhei \
            2>&1 | tee /tmp/apt-install.log

        if [ $? -eq 0 ]; then
            log_success "系統依賴安裝完成"
        else
            log_error "系統依賴安裝失敗，請檢查日誌：/tmp/apt-install.log"
            exit 1
        fi
        ;;

    darwin)
        log_info "使用 Homebrew 安裝依賴..."

        if ! command -v brew &> /dev/null; then
            log_error "Homebrew 未安裝"
            echo "請先安裝 Homebrew: https://brew.sh"
            exit 1
        fi

        # macOS 的依賴安裝
        brew install \
            postgresql \
            libomp \
            jpeg \
            libpng \
            libtiff \
            webp \
            || log_warning "某些依賴可能已經安裝"

        log_success "系統依賴安裝完成"
        ;;

    *)
        log_warning "未識別的操作系統: $OS_TYPE"
        log_warning "請手動安裝系統依賴，參考 docs/DEPLOYMENT.md"
        read -p "是否繼續？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        ;;
esac

# 步驟 3: 創建虛擬環境
log_info "步驟 3/7: 創建 Python 虛擬環境"

if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    log_success "虛擬環境創建成功"
else
    log_info "虛擬環境已存在，跳過創建"
fi

# 步驟 4: 激活虛擬環境
log_info "步驟 4/7: 激活虛擬環境"
source venv/bin/activate
log_success "虛擬環境已激活"

# 步驟 5: 升級 pip
log_info "步驟 5/7: 升級 pip"
pip install --upgrade pip setuptools wheel
log_success "pip 升級完成"

# 步驟 6: 安裝 Python 依賴
log_info "步驟 6/7: 安裝 Python 依賴"
log_info "這可能需要幾分鐘..."

pip install -r requirements.txt 2>&1 | tee /tmp/pip-install.log

if [ $? -eq 0 ]; then
    log_success "Python 依賴安裝完成"
else
    log_error "Python 依賴安裝失敗"
    log_error "常見問題："
    echo "  1. PaddleOCR 安裝失敗："
    echo "     - 檢查是否缺少系統庫：ldd venv/lib/python3.11/site-packages/cv2/*.so"
    echo "     - 嘗試單獨安裝：pip install paddleocr==2.7.0"
    echo ""
    echo "  2. OpenCV 安裝失敗："
    echo "     - 缺少 OpenGL 庫：sudo apt install libgl1-mesa-glx"
    echo "     - 缺少字體庫：sudo apt install fonts-noto-cjk"
    echo ""
    echo "完整日誌：/tmp/pip-install.log"
    exit 1
fi

# 安裝項目
log_info "安裝 AgenticMath 包..."
pip install -e .
log_success "AgenticMath 安裝完成"

# 步驟 7: 運行依賴檢查
log_info "步驟 7/7: 驗證依賴"

if [ -f "scripts/check_dependencies.py" ]; then
    python scripts/check_dependencies.py

    if [ $? -eq 0 ]; then
        log_success "依賴驗證通過！"
    else
        log_error "依賴驗證失敗"
        log_warning "某些功能可能無法正常工作"
        echo ""
        echo "常見修復方法："
        echo "  1. 重新安裝 OpenCV："
        echo "     pip uninstall opencv-python && pip install opencv-python==4.9.0.80"
        echo ""
        echo "  2. 重新安裝 PaddleOCR："
        echo "     pip uninstall paddleocr paddlepaddle && pip install paddleocr==2.7.0"
        echo ""
        exit 1
    fi
else
    log_warning "依賴檢查腳本不存在，跳過驗證"
fi

# 步驟 8: 設置配置文件
log_info "設置配置文件"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "已創建 .env 文件（從 .env.example）"
        log_warning "請編輯 .env 文件並填入您的配置"
    else
        log_warning ".env.example 不存在，請手動創建 .env 文件"
    fi
else
    log_info ".env 文件已存在"
fi

# 完成
echo ""
echo "========================================="
log_success "安裝完成！"
echo "========================================="
echo ""

log_info "後續步驟："
echo "  1. 配置環境變量："
echo "     編輯 .env 文件，設置 OPENAI_API_KEY 等"
echo ""
echo "  2. 初始化數據庫："
echo "     alembic upgrade head"
echo ""
echo "  3. 運行測試："
echo "     pytest tests/"
echo ""
echo "  4. 啟動應用："
echo "     # CLI 模式："
echo "     ./agenticmath --help"
echo ""
echo "     # API 模式："
echo "     uvicorn src.api.server:app --reload"
echo ""

log_info "故障排除："
echo "  - 查看日誌："
echo "    /tmp/apt-install.log  (系統依賴安裝)"
echo "    /tmp/pip-install.log  (Python 依賴安裝)"
echo ""
echo "  - 重新運行依賴檢查："
echo "    python scripts/check_dependencies.py"
echo ""
echo "  - 查看完整文檔："
echo "    docs/DEPLOYMENT.md"
echo ""

log_success "祝使用愉快！"
echo ""
