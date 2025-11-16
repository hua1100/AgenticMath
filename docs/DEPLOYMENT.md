# AgenticMath 部署指南

完整的生产环境部署指南，包括多种部署方案和上线前准备工作。

## 目录

- [系统架构概览](#系统架构概览)
- [部署方案](#部署方案)
- [上线前检查清单](#上线前检查清单)
- [部署步骤](#部署步骤)
- [监控和日志](#监控和日志)
- [安全配置](#安全配置)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

---

## 系统架构概览

### 技术栈

```
Frontend (CLI)
    ↓
AgenticMath Application
    ├── OCR Engine (PaddleOCR)
    ├── LLM Client (OpenAI GPT-4)
    ├── Agent System (CrewAI)
    ├── Database (PostgreSQL/SQLite)
    └── Configuration (Pydantic Settings)
```

### 系统依赖

- **Python**: 3.11+
- **数据库**: PostgreSQL 14+ (生产) / SQLite (开发)
- **OCR**: PaddleOCR 2.7.0
- **LLM**: OpenAI GPT-4 API
- **其他**: 详见 `requirements.txt`

### 资源需求

**最低配置**:
- CPU: 2 核心
- RAM: 4GB
- 存储: 10GB
- 网络: 稳定的外网连接（访问 OpenAI API）

**推荐配置**:
- CPU: 4 核心（或 GPU for OCR）
- RAM: 8GB
- 存储: 20GB SSD
- 网络: 低延迟连接

---

## 部署方案

### 方案 1: Docker 容器化部署 ⭐ 推荐

**优点**:
- 环境一致性
- 快速部署
- 易于扩展
- 隔离性好

**缺点**:
- 需要 Docker 知识
- 资源开销稍高

**适用场景**: 云服务器、本地服务器、CI/CD

### 方案 2: 云服务部署

#### 2.1 AWS 部署

**服务选择**:
- **EC2**: 运行应用
- **RDS**: PostgreSQL 数据库
- **S3**: 存储上传的图片
- **CloudWatch**: 监控和日志

**预估成本**:
- EC2 t3.medium: $30-50/月
- RDS db.t3.micro: $15-25/月
- S3: $5-10/月
- **总计**: ~$50-85/月

#### 2.2 Google Cloud Platform (GCP)

**服务选择**:
- **Compute Engine**: 运行应用
- **Cloud SQL**: PostgreSQL
- **Cloud Storage**: 图片存储
- **Cloud Logging**: 日志

**预估成本**: 类似 AWS

#### 2.3 Azure 部署

**服务选择**:
- **Virtual Machines**: 运行应用
- **Azure Database**: PostgreSQL
- **Blob Storage**: 图片存储
- **Application Insights**: 监控

### 方案 3: VPS 部署

**推荐提供商**:
- DigitalOcean ($20-40/月)
- Linode ($20-40/月)
- Vultr ($20-40/月)
- 阿里云 ECS ($20-50/月)
- 腾讯云 CVM ($20-50/月)

**优点**:
- 成本可控
- 完全控制
- 简单直接

**缺点**:
- 需要自己管理
- 扩展性有限

### 方案 4: Serverless 部署

**选项**:
- AWS Lambda + API Gateway
- Google Cloud Functions
- Azure Functions

**限制**:
- 冷启动延迟
- 执行时间限制
- OCR 可能较慢

**不推荐**: 因为 PaddleOCR 和 LLM 调用需要较长时间

---

## 上线前检查清单

### ✅ 功能测试

#### 1. 单元测试
```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 检查覆盖率
pytest tests/unit/ --cov=src --cov-report=html
```

**要求**: ≥80% 覆盖率

#### 2. 集成测试
```bash
# 运行集成测试
pytest tests/integration/ -v
```

**测试项**:
- [ ] OCR 管道完整流程
- [ ] Rephrase + Review/Revise 循环
- [ ] Solution 生成管道
- [ ] 数据库读写操作

#### 3. 端到端测试
```bash
# 需要真实 API key
export OPENAI_API_KEY=your-key
pytest tests/e2e/ -v
```

**测试项**:
- [ ] 照片上传 → OCR → 生成题目
- [ ] 文本输入 → 生成题目 + 解答
- [ ] CLI 所有命令正常工作

#### 4. 性能测试

**OCR 性能**:
```bash
# 测试 OCR 处理时间
python -m pytest tests/integration/test_ocr_pipeline.py -v -s
```

**要求**:
- [ ] OCR 处理时间 < 3 秒
- [ ] 文字识别准确度 ≥ 85%

**LLM 调用性能**:
```bash
# 测试题目生成时间
python test_full_pipeline.py
```

**要求**:
- [ ] 单题生成时间 < 60 秒
- [ ] 质量分数 ≥ 4.5

#### 5. 负载测试

创建负载测试脚本 `tests/load/test_concurrent.py`:

```python
import concurrent.futures
import time

def test_concurrent_requests(num_requests=10):
    """测试并发请求"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(generate_problem, f"Problem {i}")
            for i in range(num_requests)
        ]
        results = [f.result() for f in futures]
    return results

# 运行测试
results = test_concurrent_requests(10)
assert len(results) == 10
```

**要求**:
- [ ] 支持至少 5 个并发请求
- [ ] 无数据库死锁
- [ ] 无内存泄漏

### ✅ 安全检查

#### 1. 密钥管理
- [ ] API keys 存储在环境变量中
- [ ] `.env` 文件不在版本控制中
- [ ] 生产环境使用密钥管理服务（AWS Secrets Manager / HashiCorp Vault）

#### 2. 依赖安全
```bash
# 检查依赖漏洞
pip install safety
safety check

# 或使用
pip-audit
```

**要求**:
- [ ] 无已知高危漏洞
- [ ] 依赖版本都是最新稳定版

#### 3. 输入验证
- [ ] 文件上传大小限制（10MB）
- [ ] 文件类型验证（只允许 JPG/PNG）
- [ ] 文本输入长度限制（< 5000 字符）
- [ ] SQL 注入防护（使用 SQLAlchemy ORM）

#### 4. API 访问控制
- [ ] Rate limiting（限制请求频率）
- [ ] API key 轮换机制
- [ ] 使用 HTTPS（生产环境）

### ✅ 数据库准备

#### 1. 数据库迁移
```bash
# 检查迁移脚本
alembic check

# 运行迁移
alembic upgrade head

# 验证表结构
python -c "from src.storage.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

**要求**:
- [ ] 所有迁移脚本正常运行
- [ ] 表结构正确
- [ ] 索引已创建

#### 2. 数据备份策略
- [ ] 设置自动备份（每日）
- [ ] 测试恢复流程
- [ ] 异地备份（可选）

#### 3. 数据库性能
```bash
# PostgreSQL 性能优化
# 在 postgresql.conf 中设置：
# shared_buffers = 256MB
# effective_cache_size = 1GB
# max_connections = 100
```

### ✅ 配置检查

#### 1. 环境变量
```bash
# 检查所有必需的环境变量
cat .env.example
```

**必需变量**:
- [ ] `OPENAI_API_KEY`
- [ ] `DATABASE_URL`
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=info`

#### 2. 日志配置
```bash
# 创建日志目录
mkdir -p logs

# 设置日志轮转
# 配置 logrotate 或使用 Python logging handlers
```

#### 3. 存储配置
```bash
# 创建上传目录
mkdir -p uploads

# 设置权限
chmod 755 uploads
```

### ✅ 监控设置

#### 1. 应用监控
- [ ] 设置健康检查端点
- [ ] 配置错误追踪（Sentry）
- [ ] 设置性能监控（New Relic / DataDog）

#### 2. 系统监控
- [ ] CPU 使用率监控
- [ ] 内存使用率监控
- [ ] 磁盘空间监控
- [ ] 网络流量监控

#### 3. 数据库监控
- [ ] 连接池监控
- [ ] 查询性能监控
- [ ] 慢查询日志

#### 4. 告警设置
- [ ] CPU > 80% 告警
- [ ] 内存 > 90% 告警
- [ ] 磁盘 > 85% 告警
- [ ] 错误率 > 5% 告警
- [ ] API 调用失败告警

### ✅ 文档准备

- [ ] API 文档完整
- [ ] 部署文档完整
- [ ] 运维手册完整
- [ ] 用户使用指南完整
- [ ] 故障排查指南完整

### ✅ 备份和恢复

#### 1. 数据备份
```bash
# PostgreSQL 备份
pg_dump -U username -d agenticmath > backup_$(date +%Y%m%d).sql

# 恢复
psql -U username -d agenticmath < backup_20250116.sql
```

#### 2. 配置备份
- [ ] 备份 `.env` 文件（加密存储）
- [ ] 备份数据库配置
- [ ] 备份 nginx/apache 配置

#### 3. 代码版本
- [ ] Git tag 标记版本
- [ ] 记录部署的 commit hash

---

## 部署步骤

### 步骤 1: 服务器准备

#### 1.1 系统更新
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### 1.2 安装依赖
```bash
# Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 其他依赖
sudo apt install build-essential libpq-dev git -y
```

#### 1.3 创建用户
```bash
# 创建应用用户
sudo useradd -m -s /bin/bash agenticmath
sudo usermod -aG sudo agenticmath

# 切换用户
sudo su - agenticmath
```

### 步骤 2: 代码部署

#### 2.1 克隆代码
```bash
cd /home/agenticmath
git clone https://github.com/your-org/AgenticMath.git
cd AgenticMath

# 切换到生产分支
git checkout main  # 或 production tag
```

#### 2.2 创建虚拟环境
```bash
python3.11 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel
```

#### 2.3 安装依赖
```bash
# 生产环境依赖
pip install -r requirements.txt

# 安装应用
pip install -e .
```

### 步骤 3: 数据库设置

#### 3.1 创建数据库
```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 PostgreSQL 中
CREATE DATABASE agenticmath;
CREATE USER agenticmath_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE agenticmath TO agenticmath_user;
\q
```

#### 3.2 运行迁移
```bash
# 配置数据库 URL
export DATABASE_URL="postgresql://agenticmath_user:your-secure-password@localhost:5432/agenticmath"

# 运行迁移
alembic upgrade head
```

#### 3.3 验证
```bash
# 验证表已创建
python -c "from src.storage.database import get_db; from src.models import Problem; print('Database OK')"
```

### 步骤 4: 环境配置

#### 4.1 创建 .env 文件
```bash
cp .env.example .env
nano .env
```

**生产配置示例**:
```env
# LLM Configuration
OPENAI_API_KEY=sk-your-production-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

# Database
DATABASE_URL=postgresql://agenticmath_user:password@localhost:5432/agenticmath
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Quality Control
QUALITY_THRESHOLD=4.5
MAX_REVISE_ITERATIONS=5

# Logging
LOG_LEVEL=info
LOG_FILE=logs/agenticmath.log

# Environment
ENVIRONMENT=production
DEBUG=false
```

#### 4.2 创建必要目录
```bash
mkdir -p logs uploads
chmod 755 logs uploads
```

### 步骤 5: 服务配置

#### 5.1 创建 systemd 服务（CLI模式）

如果只运行 CLI，可以跳过此步骤。

#### 5.2 创建 API 服务（可选）

如果要提供 HTTP API，创建 FastAPI 应用：

`src/api/server.py`:
```python
from fastapi import FastAPI, UploadFile, File
from src.orchestration.photo_to_problems import PhotoToProblemsOrchestrator

app = FastAPI(title="AgenticMath API")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/generate-from-photo")
async def generate_from_photo(file: UploadFile = File(...)):
    # 实现逻辑
    pass
```

创建 systemd 服务文件 `/etc/systemd/system/agenticmath.service`:
```ini
[Unit]
Description=AgenticMath API Service
After=network.target postgresql.service

[Service]
Type=simple
User=agenticmath
Group=agenticmath
WorkingDirectory=/home/agenticmath/AgenticMath
Environment="PATH=/home/agenticmath/AgenticMath/venv/bin"
EnvironmentFile=/home/agenticmath/AgenticMath/.env
ExecStart=/home/agenticmath/AgenticMath/venv/bin/uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable agenticmath
sudo systemctl start agenticmath
sudo systemctl status agenticmath
```

#### 5.3 Nginx 反向代理（可选）

`/etc/nginx/sites-available/agenticmath`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置（LLM 调用可能较慢）
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/agenticmath /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 步骤 6: 测试部署

#### 6.1 CLI 测试
```bash
source venv/bin/activate
./agenticmath version
./agenticmath config

# 测试生成（需要 API key）
./agenticmath generate "测试题目" -d 3
```

#### 6.2 API 测试（如果部署了 API）
```bash
# 健康检查
curl http://localhost:8000/health

# 测试上传
curl -X POST -F "file=@test_image.jpg" http://localhost:8000/generate-from-photo
```

---

## 监控和日志

### 应用日志

#### 日志配置

已在 `src/config/settings.py` 中配置：
```python
LOG_LEVEL=info
LOG_FILE=logs/agenticmath.log
LOG_MAX_FILE_SIZE_MB=10
LOG_BACKUP_COUNT=5
```

#### 查看日志
```bash
# 实时查看
tail -f logs/agenticmath.log

# 搜索错误
grep ERROR logs/agenticmath.log

# 分析最近错误
tail -100 logs/agenticmath.log | grep ERROR
```

#### 日志轮转

配置 logrotate `/etc/logrotate.d/agenticmath`:
```
/home/agenticmath/AgenticMath/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 agenticmath agenticmath
    sharedscripts
    postrotate
        systemctl reload agenticmath >/dev/null 2>&1 || true
    endscript
}
```

### 系统监控

#### 使用 Prometheus + Grafana

1. **安装 Prometheus**
2. **配置指标收集**
3. **设置 Grafana 仪表板**

#### 使用云服务监控

- **AWS CloudWatch**
- **Google Cloud Monitoring**
- **Azure Monitor**
- **Datadog**
- **New Relic**

### 错误追踪

#### 集成 Sentry

```bash
pip install sentry-sdk
```

在 `src/cli/main.py` 中添加:
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
    traces_sample_rate=0.1,
)
```

---

## 安全配置

### 1. 防火墙设置

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 2. SSL/TLS 证书

使用 Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. API Key 安全

- 使用环境变量存储
- 定期轮换 API keys
- 实施 rate limiting
- 监控异常使用

### 4. 数据库安全

```bash
# PostgreSQL 配置 (/etc/postgresql/14/main/pg_hba.conf)
# 只允许本地连接
local   all             all                                     peer
host    all             all             127.0.0.1/32            scram-sha-256
```

### 5. 文件上传安全

- 验证文件类型
- 限制文件大小
- 扫描恶意文件
- 隔离存储

---

## 性能优化

### 1. OCR 优化

```python
# 使用 GPU（如果可用）
OCR_USE_GPU=true

# 调整线程数
export OMP_NUM_THREADS=4
```

### 2. LLM 调用优化

- 实施缓存（重复问题）
- 批量处理请求
- 使用连接池
- 设置合理超时

### 3. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_problems_created_at ON problems(created_at);
CREATE INDEX idx_solutions_problem_id ON solutions(problem_id);

-- 定期 VACUUM
VACUUM ANALYZE;
```

### 4. 应用优化

```python
# 连接池配置
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30

# 并发控制
MAX_CONCURRENT_TASKS=5
```

---

## 故障排查

### 常见问题

#### 1. OCR 失败
```bash
# 检查 PaddleOCR 安装
python -c "import paddleocr; print('OK')"

# 检查图片文件
file uploaded_image.jpg

# 查看 OCR 日志
grep OCR logs/agenticmath.log
```

#### 2. LLM API 错误
```bash
# 测试 API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 检查网络连接
ping api.openai.com

# 查看错误日志
grep OpenAI logs/agenticmath.log
```

#### 3. 数据库连接失败
```bash
# 测试数据库连接
psql -U agenticmath_user -d agenticmath -h localhost

# 检查数据库状态
sudo systemctl status postgresql

# 查看数据库日志
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 4. 内存不足
```bash
# 查看内存使用
free -h

# 查看进程内存
ps aux --sort=-%mem | head

# 重启服务
sudo systemctl restart agenticmath
```

### 应急响应

#### 1. 服务宕机
```bash
# 检查服务状态
sudo systemctl status agenticmath

# 查看最近日志
sudo journalctl -u agenticmath -n 100

# 重启服务
sudo systemctl restart agenticmath
```

#### 2. 数据库异常
```bash
# 检查数据库连接
psql -U postgres

# 检查锁
SELECT * FROM pg_locks WHERE NOT granted;

# 终止长时间查询
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';
```

#### 3. 磁盘满
```bash
# 查看磁盘使用
df -h

# 清理日志
find logs/ -name "*.log.*" -mtime +30 -delete

# 清理旧备份
find backups/ -name "*.sql" -mtime +7 -delete
```

---

## 回滚策略

### 代码回滚
```bash
# 回到上一个版本
git checkout <previous-tag>
pip install -r requirements.txt
sudo systemctl restart agenticmath
```

### 数据库回滚
```bash
# 回滚迁移
alembic downgrade -1

# 恢复备份
psql -U agenticmath_user -d agenticmath < backup_previous.sql
```

---

## 成本估算

### 基础部署（VPS）

| 项目 | 成本 |
|------|------|
| VPS (4核8GB) | $40/月 |
| OpenAI API | $50-200/月（取决于使用量）|
| 域名 | $10/年 |
| SSL 证书 | 免费 (Let's Encrypt) |
| 备份存储 | $5/月 |
| **总计** | **$95-245/月** |

### 云服务部署（AWS）

| 项目 | 成本 |
|------|------|
| EC2 t3.medium | $35/月 |
| RDS db.t3.small | $25/月 |
| S3 存储 | $5/月 |
| CloudWatch | $10/月 |
| OpenAI API | $50-200/月 |
| **总计** | **$125-275/月** |

---

## 扩展方案

### 水平扩展

1. **负载均衡**: 使用 Nginx/HAProxy
2. **多实例部署**: 运行多个应用实例
3. **数据库主从复制**: 读写分离

### 垂直扩展

1. **升级服务器**: 更多 CPU/内存
2. **GPU 加速**: OCR 性能提升
3. **SSD 存储**: 数据库性能提升

---

## 参考资源

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/current/admin.html)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Docker Documentation](https://docs.docker.com/)

---

**最后更新**: 2025-01-16
**版本**: 1.0
**维护者**: AgenticMath Team
