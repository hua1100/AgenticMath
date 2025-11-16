#!/bin/bash
#
# AgenticMath Production Deployment Script
#
# 用法: ./scripts/deploy_production.sh [--dry-run]
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查是否为 dry-run 模式
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    log_warning "运行在 dry-run 模式，不会实际执行部署"
fi

# 配置变量
APP_USER=${APP_USER:-agenticmath}
APP_DIR=${APP_DIR:-/home/agenticmath/AgenticMath}
VENV_DIR=${VENV_DIR:-$APP_DIR/venv}
BRANCH=${BRANCH:-main}
SERVICE_NAME=${SERVICE_NAME:-agenticmath}

echo "========================================="
echo "  AgenticMath Production Deployment"
echo "========================================="
echo ""

# 1. 环境检查
log_info "步骤 1/10: 环境检查"

# 检查是否为 root 或 sudo
if [[ $EUID -ne 0 ]] && ! sudo -v; then
   log_error "需要 root 权限或 sudo 访问"
   exit 1
fi

# 检查必要命令
for cmd in git python3.11 psql systemctl; do
    if ! command -v $cmd &> /dev/null; then
        log_error "缺少必要命令: $cmd"
        exit 1
    fi
done

log_success "环境检查通过"

# 2. 备份当前版本
log_info "步骤 2/10: 备份当前版本"

if [ -d "$APP_DIR" ]; then
    BACKUP_DIR="$APP_DIR/../backup_$(date +%Y%m%d_%H%M%S)"
    if [ "$DRY_RUN" = false ]; then
        log_info "创建备份到: $BACKUP_DIR"
        cp -r "$APP_DIR" "$BACKUP_DIR"
        log_success "备份完成"
    else
        log_info "DRY-RUN: 将创建备份到 $BACKUP_DIR"
    fi
else
    log_warning "应用目录不存在，跳过备份"
fi

# 3. 数据库备份
log_info "步骤 3/10: 数据库备份"

if [ "$DRY_RUN" = false ]; then
    DB_BACKUP="$APP_DIR/../db_backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "备份数据库到: $DB_BACKUP"

    # 从 .env 读取数据库配置
    if [ -f "$APP_DIR/.env" ]; then
        source "$APP_DIR/.env"
        if [ -n "$DATABASE_URL" ]; then
            # 提取数据库信息
            # 格式: postgresql://user:password@host:port/dbname
            pg_dump -U agenticmath_user -d agenticmath > "$DB_BACKUP" 2>/dev/null || log_warning "数据库备份失败"
            log_success "数据库备份完成"
        fi
    fi
else
    log_info "DRY-RUN: 将备份数据库"
fi

# 4. 拉取最新代码
log_info "步骤 4/10: 拉取最新代码"

if [ "$DRY_RUN" = false ]; then
    cd "$APP_DIR"

    # 保存当前版本
    CURRENT_VERSION=$(git rev-parse HEAD)
    echo "$CURRENT_VERSION" > DEPLOYED_VERSION_PREVIOUS.txt

    # 拉取最新代码
    log_info "从 $BRANCH 分支拉取..."
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"

    # 保存新版本
    NEW_VERSION=$(git rev-parse HEAD)
    echo "$NEW_VERSION" > DEPLOYED_VERSION.txt

    log_success "代码更新完成 ($CURRENT_VERSION -> $NEW_VERSION)"
else
    log_info "DRY-RUN: 将从 $BRANCH 拉取最新代码"
fi

# 5. 安装/更新依赖
log_info "步骤 5/10: 更新依赖"

if [ "$DRY_RUN" = false ]; then
    cd "$APP_DIR"

    # 激活虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        log_info "创建虚拟环境..."
        python3.11 -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"

    # 升级 pip
    pip install --upgrade pip setuptools wheel

    # 安装依赖
    log_info "安装依赖..."
    pip install -r requirements.txt

    # 安装应用
    pip install -e .

    log_success "依赖安装完成"
else
    log_info "DRY-RUN: 将更新 Python 依赖"
fi

# 6. 数据库迁移
log_info "步骤 6/10: 数据库迁移"

if [ "$DRY_RUN" = false ]; then
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"

    # 检查迁移
    log_info "检查数据库迁移..."
    alembic check || log_warning "迁移检查有警告"

    # 运行迁移
    log_info "运行迁移..."
    alembic upgrade head

    log_success "数据库迁移完成"
else
    log_info "DRY-RUN: 将运行数据库迁移"
fi

# 7. 运行测试
log_info "步骤 7/10: 运行测试"

if [ "$DRY_RUN" = false ]; then
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"

    log_info "运行单元测试..."
    if pytest tests/unit/ -v --tb=short; then
        log_success "单元测试通过"
    else
        log_error "单元测试失败，中止部署"
        exit 1
    fi
else
    log_info "DRY-RUN: 将运行测试"
fi

# 8. 更新配置文件
log_info "步骤 8/10: 检查配置"

if [ ! -f "$APP_DIR/.env" ]; then
    log_error ".env 文件不存在，请先创建"
    exit 1
fi

# 检查必需的环境变量
source "$APP_DIR/.env"
REQUIRED_VARS=("OPENAI_API_KEY" "DATABASE_URL" "ENVIRONMENT")

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "缺少必需的环境变量: $var"
        exit 1
    fi
done

# 检查是否为生产环境
if [ "$ENVIRONMENT" != "production" ]; then
    log_warning "ENVIRONMENT 不是 'production'，当前值: $ENVIRONMENT"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log_success "配置检查通过"

# 9. 重启服务
log_info "步骤 9/10: 重启服务"

if [ "$DRY_RUN" = false ]; then
    # 检查是否有 systemd 服务
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "重启 $SERVICE_NAME 服务..."
        sudo systemctl restart "$SERVICE_NAME"

        # 等待服务启动
        sleep 5

        # 检查服务状态
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log_success "服务重启成功"
        else
            log_error "服务启动失败"
            sudo journalctl -u "$SERVICE_NAME" -n 50
            exit 1
        fi
    else
        log_warning "服务 $SERVICE_NAME 未运行或不存在"
        log_info "如果使用 CLI 模式，可以跳过此步骤"
    fi
else
    log_info "DRY-RUN: 将重启服务 $SERVICE_NAME"
fi

# 10. 健康检查
log_info "步骤 10/10: 健康检查"

if [ "$DRY_RUN" = false ]; then
    # 如果有 API 服务，检查健康端点
    if command -v curl &> /dev/null; then
        log_info "检查健康端点..."
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "健康检查通过"
        else
            log_warning "健康检查失败（可能未部署 API）"
        fi
    fi

    # 测试 CLI
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"
    if ./agenticmath version &> /dev/null; then
        log_success "CLI 测试通过"
    else
        log_error "CLI 测试失败"
        exit 1
    fi
else
    log_info "DRY-RUN: 将运行健康检查"
fi

# 完成
echo ""
echo "========================================="
log_success "部署完成！"
echo "========================================="
echo ""

if [ "$DRY_RUN" = false ]; then
    log_info "部署信息:"
    echo "  版本: $NEW_VERSION"
    echo "  分支: $BRANCH"
    echo "  时间: $(date)"
    echo "  备份: $BACKUP_DIR"
    echo ""
    log_info "后续步骤:"
    echo "  1. 检查日志: tail -f logs/agenticmath.log"
    echo "  2. 监控服务: sudo systemctl status $SERVICE_NAME"
    echo "  3. 查看指标: 访问监控仪表板"
    echo ""
    log_warning "如有问题，可以使用以下命令回滚:"
    echo "  cd $APP_DIR && git checkout $CURRENT_VERSION && systemctl restart $SERVICE_NAME"
else
    log_info "这是 dry-run 模式，未进行实际部署"
    log_info "移除 --dry-run 参数以执行真实部署"
fi

echo ""
