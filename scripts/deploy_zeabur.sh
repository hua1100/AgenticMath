#!/bin/bash
#
# Zeabur 快速部署腳本
#
# 使用方法：
#   ./scripts/deploy_zeabur.sh
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "  AgenticMath - Zeabur 快速部署"
echo "========================================="
echo ""

# 檢查是否安裝了 Zeabur CLI
if ! command -v zeabur &> /dev/null; then
    echo -e "${YELLOW}⚠ Zeabur CLI 未安裝${NC}"
    echo ""
    echo "安裝方法："
    echo "  npm install -g @zeabur/cli"
    echo ""
    echo "或使用 Zeabur Dashboard 手動部署："
    echo "  https://dash.zeabur.com"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Zeabur CLI 已安裝"
echo ""

# 檢查是否已登入
if ! zeabur auth whoami &> /dev/null; then
    echo -e "${YELLOW}⚠ 未登入 Zeabur${NC}"
    echo ""
    echo "正在打開登入頁面..."
    zeabur auth login

    if ! zeabur auth whoami &> /dev/null; then
        echo -e "${RED}✗ 登入失敗${NC}"
        exit 1
    fi
fi

WHOAMI=$(zeabur auth whoami)
echo -e "${GREEN}✓${NC} 已登入為: $WHOAMI"
echo ""

# 檢查 Git 狀態
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠ 有未提交的更改${NC}"
    echo ""
    git status --short
    echo ""
    read -p "是否繼續？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 檢查必需文件
echo -e "${BLUE}檢查必需文件...${NC}"

REQUIRED_FILES=(
    "Dockerfile"
    "requirements.txt"
    ".env.zeabur"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (缺失)"
        exit 1
    fi
done
echo ""

# 詢問項目名稱
read -p "輸入 Zeabur 項目名稱 [agenticmath]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-agenticmath}

echo ""
echo -e "${BLUE}準備部署到 Zeabur...${NC}"
echo ""
echo "項目名稱: $PROJECT_NAME"
echo ""

# 詢問是否繼續
read -p "是否繼續？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "========================================="
echo "部署步驟"
echo "========================================="
echo ""

# 步驟 1：創建或選擇項目
echo -e "${BLUE}[1/6]${NC} 創建/選擇項目..."

# 列出現有項目
echo "現有項目："
zeabur project list || true

echo ""
read -p "使用現有項目 ID（留空則創建新項目）: " EXISTING_PROJECT_ID

if [ -z "$EXISTING_PROJECT_ID" ]; then
    echo "創建新項目: $PROJECT_NAME"

    # 選擇區域
    echo ""
    echo "選擇部署區域："
    echo "  1. Hong Kong (香港) - 推薦給中國用戶"
    echo "  2. Singapore (新加坡)"
    echo "  3. US West (美國西部)"
    echo ""
    read -p "輸入選項 [1]: " REGION_CHOICE
    REGION_CHOICE=${REGION_CHOICE:-1}

    case $REGION_CHOICE in
        1)
            REGION="hkg"
            ;;
        2)
            REGION="sgp"
            ;;
        3)
            REGION="usw"
            ;;
        *)
            REGION="hkg"
            ;;
    esac

    PROJECT_ID=$(zeabur project create "$PROJECT_NAME" --region "$REGION" --json | jq -r '.id')

    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}✗ 項目創建失敗${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} 項目已創建: $PROJECT_ID"
else
    PROJECT_ID=$EXISTING_PROJECT_ID
    echo -e "${GREEN}✓${NC} 使用現有項目: $PROJECT_ID"
fi

echo ""

# 步驟 2：部署應用
echo -e "${BLUE}[2/6]${NC} 部署應用服務..."

# 獲取當前 Git 分支
BRANCH=$(git branch --show-current)

echo "從 Git 倉庫部署..."
echo "  分支: $BRANCH"

# 這裡需要用戶在 Zeabur Dashboard 中手動連接 Git
echo ""
echo -e "${YELLOW}⚠ 請在 Zeabur Dashboard 中完成以下操作：${NC}"
echo ""
echo "1. 訪問: https://dash.zeabur.com/projects/$PROJECT_ID"
echo "2. 點擊 'Add Service' → 'Git'"
echo "3. 選擇您的 GitHub 倉庫"
echo "4. 選擇分支: $BRANCH"
echo "5. 等待構建完成"
echo ""
read -p "完成後按 Enter 繼續..."

# 步驟 3：添加 PostgreSQL
echo ""
echo -e "${BLUE}[3/6]${NC} 添加 PostgreSQL 數據庫..."

read -p "是否需要添加 PostgreSQL？(y/n) [y]: " ADD_POSTGRES
ADD_POSTGRES=${ADD_POSTGRES:-y}

if [[ $ADD_POSTGRES =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}⚠ 請在 Zeabur Dashboard 中完成以下操作：${NC}"
    echo ""
    echo "1. 在項目中點擊 'Add Service' → 'Marketplace'"
    echo "2. 選擇 'PostgreSQL'"
    echo "3. 等待部署完成"
    echo ""
    read -p "完成後按 Enter 繼續..."
fi

# 步驟 4：配置環境變量
echo ""
echo -e "${BLUE}[4/6]${NC} 配置環境變量..."

echo ""
echo "環境變量配置模板已保存在: .env.zeabur"
echo ""
echo -e "${YELLOW}⚠ 請在 Zeabur Dashboard 中設置環境變量：${NC}"
echo ""
echo "1. 進入應用服務 → Variables"
echo "2. 複製 .env.zeabur 的內容"
echo "3. 填入實際的 API 密鑰等信息"
echo "4. 保存並重啟服務"
echo ""

# 顯示關鍵環境變量
echo "關鍵環境變量（必須設置）："
echo ""
echo "  OPENAI_API_KEY=sk-your-key"
echo "  DATABASE_URL=postgresql://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/\${POSTGRES_DATABASE}"
echo "  ENVIRONMENT=production"
echo ""

read -p "完成後按 Enter 繼續..."

# 步驟 5：運行數據庫遷移
echo ""
echo -e "${BLUE}[5/6]${NC} 運行數據庫遷移..."

echo ""
echo -e "${YELLOW}⚠ 請在 Zeabur Dashboard 中運行遷移：${NC}"
echo ""
echo "1. 進入應用服務 → Console"
echo "2. 運行命令: alembic upgrade head"
echo "3. 確認遷移成功"
echo ""
read -p "完成後按 Enter 繼續..."

# 步驟 6：生成域名
echo ""
echo -e "${BLUE}[6/6]${NC} 生成訪問域名..."

echo ""
echo -e "${YELLOW}⚠ 請在 Zeabur Dashboard 中生成域名：${NC}"
echo ""
echo "1. 進入應用服務 → Networking"
echo "2. 點擊 'Generate Domain'"
echo "3. 複製生成的 URL"
echo ""

read -p "輸入生成的域名（例如 your-app.zeabur.app）: " APP_DOMAIN

if [ -n "$APP_DOMAIN" ]; then
    echo ""
    echo "========================================="
    echo "部署完成！"
    echo "========================================="
    echo ""
    echo -e "${GREEN}✓${NC} 應用 URL: https://$APP_DOMAIN"
    echo ""
    echo "下一步："
    echo ""
    echo "1. 測試健康檢查："
    echo "   curl https://$APP_DOMAIN/health"
    echo ""
    echo "2. 查看日誌："
    echo "   在 Dashboard → Logs 中查看"
    echo ""
    echo "3. 測試 API："
    echo "   curl -X POST https://$APP_DOMAIN/api/upload \\"
    echo "     -F \"file=@test.jpg\" \\"
    echo "     -F \"difficulty=3\" \\"
    echo "     -F \"num_questions=5\""
    echo ""
    echo "4. 查看完整文檔："
    echo "   docs/ZEABUR_DEPLOYMENT.md"
    echo ""
fi

echo ""
echo -e "${GREEN}部署流程已完成！${NC}"
echo ""
echo "如有問題，請查看："
echo "  - 文檔: docs/ZEABUR_DEPLOYMENT.md"
echo "  - 故障排除: docs/TROUBLESHOOTING.md"
echo "  - Zeabur 支持: https://discord.gg/zeabur"
echo ""
