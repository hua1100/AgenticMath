#!/bin/bash
#
# AgenticMath 部署驗證腳本
#
# 檢查項目是否準備好部署
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 計數器
PASSED=0
FAILED=0
WARNINGS=0

# 檢查函數
check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file (缺失)"
        ((FAILED++))
        return 1
    fi
}

check_dir() {
    local dir=$1
    local description=$2

    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description: $dir"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $description: $dir (不存在)"
        ((WARNINGS++))
        return 1
    fi
}

check_executable() {
    local file=$1
    local description=$2

    if [ -f "$file" ] && [ -x "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file (可執行)"
        ((PASSED++))
        return 0
    elif [ -f "$file" ]; then
        echo -e "${YELLOW}⚠${NC} $description: $file (不可執行)"
        ((WARNINGS++))
        return 1
    else
        echo -e "${RED}✗${NC} $description: $file (缺失)"
        ((FAILED++))
        return 1
    fi
}

echo "========================================="
echo "  AgenticMath 部署驗證"
echo "========================================="
echo ""

# 1. 檢查核心代碼文件
echo -e "${BLUE}[1/10]${NC} 檢查核心代碼文件..."
check_file "src/agents/ocr_agent.py" "OCR Agent"
check_file "src/agents/rephrase_agent.py" "Rephrase Agent"
check_file "src/agents/solver_agent.py" "Solver Agent"
check_file "src/config/settings.py" "配置管理"
check_file "src/cli/main.py" "CLI 主程序"
echo ""

# 2. 檢查 Prompts
echo -e "${BLUE}[2/10]${NC} 檢查 Prompt 文件..."
check_file "src/prompts/ocr_prompt.py" "OCR Prompt"
check_file "src/prompts/rephrase_prompt.py" "Rephrase Prompt"
check_file "src/prompts/solver_prompt.py" "Solver Prompt"
echo ""

# 3. 檢查 Parsers
echo -e "${BLUE}[3/10]${NC} 檢查 Parser 文件..."
check_file "src/parsers/ocr_parser.py" "OCR Parser"
check_file "src/parsers/rephrase_parser.py" "Rephrase Parser"
check_file "src/parsers/solver_parser.py" "Solver Parser"
echo ""

# 4. 檢查部署配置
echo -e "${BLUE}[4/10]${NC} 檢查部署配置..."
check_file "Dockerfile" "Dockerfile"
check_file "docker-compose.yml" "Docker Compose"
check_file ".dockerignore" "Docker ignore"
check_file "requirements.txt" "Python 依賴"
echo ""

# 5. 檢查文檔
echo -e "${BLUE}[5/10]${NC} 檢查文檔..."
check_file "docs/DEPLOYMENT.md" "部署文檔"
check_file "docs/PRE_LAUNCH_CHECKLIST.md" "上線檢查清單"
check_file "docs/TROUBLESHOOTING.md" "故障排除指南"
check_file "docs/PROMPT_TESTING_GUIDE.md" "Prompt 測試指南"
check_file "docs/CLI_GUIDE.md" "CLI 指南"
check_file "README.md" "README"
echo ""

# 6. 檢查腳本
echo -e "${BLUE}[6/10]${NC} 檢查腳本工具..."
check_executable "scripts/check_dependencies.py" "依賴檢查腳本"
check_executable "scripts/quick_install.sh" "快速安裝腳本"
check_executable "scripts/test_prompts.py" "Prompt 測試腳本"
check_executable "scripts/deploy_production.sh" "部署腳本"
check_executable "agenticmath" "CLI 入口"
echo ""

# 7. 檢查測試文件
echo -e "${BLUE}[7/10]${NC} 檢查測試文件..."
check_dir "tests/unit" "單元測試目錄"
check_dir "tests/integration" "集成測試目錄"
check_dir "tests/contract" "契約測試目錄"
check_file "tests/fixtures/prompt_test_cases.json" "Prompt 測試數據"
echo ""

# 8. 檢查數據庫遷移
echo -e "${BLUE}[8/10]${NC} 檢查數據庫遷移..."
check_dir "alembic" "Alembic 目錄"
check_file "alembic.ini" "Alembic 配置"
check_dir "alembic/versions" "遷移版本"
echo ""

# 9. 檢查配置模板
echo -e "${BLUE}[9/10]${NC} 檢查配置文件..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env 文件存在"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} .env 文件不存在（需要從 .env.example 創建）"
    ((WARNINGS++))
fi

if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓${NC} .env.example 文件存在"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} .env.example 文件缺失"
    ((FAILED++))
fi
echo ""

# 10. 檢查 Git 狀態
echo -e "${BLUE}[10/10]${NC} 檢查 Git 狀態..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Git 倉庫已初始化"
    ((PASSED++))

    # 檢查是否有未提交的更改
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${GREEN}✓${NC} 沒有未提交的更改"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} 有未提交的更改"
        ((WARNINGS++))
        git status --short
    fi

    # 檢查分支
    BRANCH=$(git branch --show-current)
    echo -e "${BLUE}  當前分支:${NC} $BRANCH"
else
    echo -e "${RED}✗${NC} 不是 Git 倉庫"
    ((FAILED++))
fi
echo ""

# 總結
echo "========================================="
echo "驗證結果"
echo "========================================="
echo -e "${GREEN}通過: $PASSED${NC}"
echo -e "${YELLOW}警告: $WARNINGS${NC}"
echo -e "${RED}失敗: $FAILED${NC}"
echo "========================================="
echo ""

# 建議
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}⚠ 有 $FAILED 項檢查失敗${NC}"
    echo "請修復上述問題後再進行部署"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ 有 $WARNINGS 項警告${NC}"
    echo "建議處理警告項目，但可以繼續部署"
    echo ""
    echo "後續步驟："
    echo "  1. 閱讀部署驗證報告: DEPLOYMENT_VALIDATION_REPORT.md"
    echo "  2. 運行依賴檢查: python scripts/check_dependencies.py"
    echo "  3. 運行測試: pytest tests/"
    echo "  4. 查看部署指南: docs/DEPLOYMENT.md"
    exit 0
else
    echo -e "${GREEN}✓ 所有檢查通過！${NC}"
    echo ""
    echo "項目已準備好部署！"
    echo ""
    echo "後續步驟："
    echo "  1. 閱讀部署驗證報告: DEPLOYMENT_VALIDATION_REPORT.md"
    echo "  2. 運行依賴檢查: python scripts/check_dependencies.py"
    echo "  3. 運行測試: pytest tests/"
    echo "  4. 選擇部署方式: docs/DEPLOYMENT.md"
    echo "  5. 執行部署: ./scripts/deploy_production.sh --dry-run"
    exit 0
fi
