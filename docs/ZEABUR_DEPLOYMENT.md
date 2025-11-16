# Zeabur 部署指南

本指南將引導您如何在 Zeabur 上部署 AgenticMath。

## 📋 目錄

1. [為什麼選擇 Zeabur](#為什麼選擇-zeabur)
2. [前置準備](#前置準備)
3. [快速部署](#快速部署)
4. [配置環境變量](#配置環境變量)
5. [數據庫設置](#數據庫設置)
6. [部署驗證](#部署驗證)
7. [成本估算](#成本估算)
8. [常見問題](#常見問題)

---

## 為什麼選擇 Zeabur

✅ **優勢：**
- 🚀 **自動化部署** - Git push 即自動部署
- 🐳 **原生支持 Docker** - 完美兼容我們的 Dockerfile
- 💰 **價格合理** - 比 AWS/GCP 更實惠
- 🇨🇳 **中文界面** - 友好的中文支持
- 📊 **內建監控** - 自動監控和日誌
- 🗄️ **託管數據庫** - PostgreSQL 一鍵部署
- 🌐 **免費域名** - 提供 .zeabur.app 子域名
- 🔒 **自動 HTTPS** - 免費 SSL 證書

---

## 前置準備

### 1. 註冊 Zeabur 帳號

訪問 [https://zeabur.com](https://zeabur.com) 並註冊帳號：
- 支持 GitHub 登入
- 支持 Google 登入
- 支持郵箱註冊

### 2. 準備代碼倉庫

確保您的代碼已推送到 GitHub：

```bash
# 檢查 Git 遠程倉庫
git remote -v

# 確保代碼已推送
git push origin main  # 或您的分支名
```

### 3. 準備環境變量

您需要以下環境變量：
- `OPENAI_API_KEY` - OpenAI API 密鑰（必需）
- `DATABASE_URL` - PostgreSQL 連接字符串（Zeabur 會自動提供）
- 其他可選配置（參考 `.env.example`）

---

## 快速部署

### 方法 1：使用 Zeabur 控制台（推薦）

#### 步驟 1：創建新項目

1. 登入 [Zeabur Dashboard](https://dash.zeabur.com)
2. 點擊 **"Create Project"**（創建項目）
3. 輸入項目名稱：`agenticmath`
4. 選擇區域：
   - 🇭🇰 Hong Kong（香港）- 推薦給中國用戶
   - 🇸🇬 Singapore（新加坡）
   - 🇺🇸 US（美國）

#### 步驟 2：部署應用

1. 在項目中點擊 **"Add Service"**（添加服務）
2. 選擇 **"Git"**
3. 選擇您的 GitHub 倉庫：`AgenticMath`
4. 選擇分支：`main` 或您的工作分支
5. Zeabur 會自動檢測到 `Dockerfile` 並開始構建

#### 步驟 3：添加 PostgreSQL 數據庫

1. 在同一項目中，再次點擊 **"Add Service"**
2. 選擇 **"Marketplace"**（服務市場）
3. 選擇 **"PostgreSQL"**
4. Zeabur 會自動部署 PostgreSQL 並提供連接信息

#### 步驟 4：連接數據庫到應用

Zeabur 會自動將數據庫連接信息注入到應用的環境變量中：

1. 進入應用服務設置
2. 在 **"Environment Variables"**（環境變量）中，Zeabur 已自動添加：
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DATABASE`

3. 添加一個新的環境變量 `DATABASE_URL`：
   ```
   postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE}
   ```

#### 步驟 5：配置應用環境變量

在 **"Environment Variables"** 中添加：

```env
# 必需
OPENAI_API_KEY=sk-your-openai-api-key

# 應用配置
ENVIRONMENT=production
DEBUG=false

# 日誌配置
LOG_LEVEL=info
LOG_FILE=/app/logs/agenticmath.log

# API 配置（如果需要）
API_HOST=0.0.0.0
API_PORT=8000
```

#### 步驟 6：運行數據庫遷移

在應用部署成功後，需要運行數據庫遷移：

**選項 A：使用 Zeabur 控制台**

1. 進入應用服務
2. 點擊 **"Console"**（控制台）標籤
3. 運行命令：
   ```bash
   alembic upgrade head
   ```

**選項 B：使用 Zeabur CLI**

```bash
# 安裝 Zeabur CLI
npm install -g @zeabur/cli

# 登入
zeabur auth login

# 連接到服務並運行命令
zeabur exec -s <service-id> -- alembic upgrade head
```

#### 步驟 7：獲取訪問 URL

1. 在應用服務頁面，點擊 **"Networking"**（網絡）
2. 點擊 **"Generate Domain"**（生成域名）
3. Zeabur 會提供一個免費域名：`https://your-app.zeabur.app`
4. 或者綁定自定義域名

---

### 方法 2：使用 Zeabur CLI

```bash
# 1. 安裝 Zeabur CLI
npm install -g @zeabur/cli

# 2. 登入
zeabur auth login

# 3. 創建項目
zeabur project create agenticmath

# 4. 部署應用
zeabur deploy

# 5. 添加 PostgreSQL
zeabur service create postgresql

# 6. 配置環境變量
zeabur env set OPENAI_API_KEY=sk-your-key
zeabur env set ENVIRONMENT=production

# 7. 查看部署狀態
zeabur status
```

---

## 配置環境變量

### 完整環境變量列表

在 Zeabur Dashboard 的 **Environment Variables** 中配置：

```env
# ==================== 必需配置 ====================

# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# 數據庫（Zeabur 自動注入，只需組合）
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE}

# 應用配置
ENVIRONMENT=production
DEBUG=false

# ==================== 可選配置 ====================

# OCR 配置
OCR_USE_GPU=false
OCR_LANG=ch

# 質量控制
QUALITY_THRESHOLD=4.0
MAX_ITERATIONS=3

# 日誌配置
LOG_LEVEL=info
LOG_FILE=/app/logs/agenticmath.log

# API 配置（如果啟用 API 模式）
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2
```

### 如何在 Zeabur 中設置環境變量

1. **通過 Dashboard：**
   - 進入服務頁面
   - 點擊 **"Variables"** 標籤
   - 點擊 **"Add Variable"**
   - 輸入變量名和值
   - 點擊保存

2. **通過 CLI：**
   ```bash
   zeabur env set KEY=VALUE
   ```

3. **批量導入：**
   - 準備 `.env` 文件
   - 在 Dashboard 中點擊 **"Import from .env"**
   - 粘貼內容並保存

---

## 數據庫設置

### 選項 1：使用 Zeabur PostgreSQL（推薦）

**優勢：**
- ✅ 自動備份
- ✅ 自動擴展
- ✅ 零配置連接
- ✅ 內建監控

**步驟：**

1. 在項目中添加 PostgreSQL 服務（如前所述）
2. Zeabur 自動提供連接信息
3. 運行遷移：
   ```bash
   zeabur exec -s <app-service-id> -- alembic upgrade head
   ```

### 選項 2：使用外部數據庫

如果您已有 PostgreSQL 數據庫：

1. 在環境變量中設置完整的 `DATABASE_URL`：
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```

2. 確保數據庫允許來自 Zeabur 的連接（查看 Zeabur IP 白名單）

---

## 部署驗證

### 1. 檢查部署狀態

在 Zeabur Dashboard：
- ✅ 查看構建日誌（Build Logs）
- ✅ 查看運行日誌（Runtime Logs）
- ✅ 檢查服務狀態（綠色表示運行中）

### 2. 測試健康檢查

```bash
# 替換為您的 Zeabur 域名
curl https://your-app.zeabur.app/health

# 預期響應
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### 3. 測試 API（如果啟用）

```bash
# 測試文件上傳
curl -X POST https://your-app.zeabur.app/api/upload \
  -F "file=@test_image.jpg" \
  -F "difficulty=3" \
  -F "num_questions=5"
```

### 4. 查看日誌

**在 Dashboard：**
- 進入服務頁面
- 點擊 **"Logs"** 標籤
- 實時查看應用日誌

**使用 CLI：**
```bash
zeabur logs -f
```

---

## Dockerfile 優化（針對 Zeabur）

我們的 Dockerfile 已經針對 Zeabur 進行了優化，但您可以進一步調整：

### 當前 Dockerfile 特點

✅ **已優化：**
- 多階段構建（減小鏡像大小）
- 包含所有必需依賴
- 健康檢查
- 非 root 用戶運行

### 可選優化

如果需要更快的構建速度，可以創建 `zeabur.Dockerfile`：

```dockerfile
# 使用預構建的基礎鏡像（更快）
FROM python:3.11-slim

# 安裝運行時依賴
RUN apt-get update && apt-get install -y \
    libpq5 libgomp1 libglib2.0-0 libgthread-2.0-0 \
    libsm6 libxext6 libxrender1 libfontconfig1 libice6 \
    libgl1-mesa-glx libglu1-mesa \
    libjpeg62-turbo libpng16-16 libtiff5 libwebp6 \
    libavcodec58 libavformat58 libswscale5 \
    libatlas3-base fonts-noto-cjk fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY . .

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s CMD python -c "import sys; sys.exit(0)"

# 暴露端口
EXPOSE 8000

# 默認命令（Zeabur 會自動檢測）
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

然後在 Zeabur 設置中指定使用此 Dockerfile。

---

## 成本估算

### Zeabur 定價（2024 年）

Zeabur 使用資源計費模式：

| 資源 | 開發者計劃 | 團隊計劃 | 企業計劃 |
|------|-----------|---------|---------|
| **月費** | $5 | $15 | 聯繫銷售 |
| **免費額度** | $5 額度 | $15 額度 | 自定義 |
| **CPU** | $0.042/vCPU/小時 | 同左 | 自定義 |
| **內存** | $0.0055/GB/小時 | 同左 | 自定義 |
| **存儲** | $0.15/GB/月 | 同左 | 自定義 |
| **流量** | 首 1GB 免費 | 首 10GB 免費 | 自定義 |

### AgenticMath 成本估算

**基礎配置（推薦）：**
- **應用服務**: 0.5 vCPU + 1GB RAM = ~$3/月
- **PostgreSQL**: 0.5 vCPU + 512MB RAM = ~$2/月
- **存儲**: 10GB = ~$1.5/月
- **流量**: < 1GB = $0/月

**總計：約 $6.5/月**（開發者計劃僅需 $5/月 + $1.5 超額）

**生產配置：**
- **應用服務**: 1 vCPU + 2GB RAM = ~$6/月
- **PostgreSQL**: 1 vCPU + 1GB RAM = ~$4/月
- **存儲**: 20GB = ~$3/月
- **流量**: ~5GB = ~$2/月

**總計：約 $15/月**（團隊計劃正好 $15/月）

### 與其他平台對比

| 平台 | 月成本 | 優勢 | 劣勢 |
|------|--------|------|------|
| **Zeabur** | $5-15 | 簡單、中文、自動化 | 較新平台 |
| **Railway** | $5-20 | 類似 Zeabur | 英文界面 |
| **Render** | $7-25 | 成熟穩定 | 較貴 |
| **AWS ECS** | $20-100 | 企業級 | 複雜、貴 |
| **GCP Cloud Run** | $10-50 | 彈性擴展 | 配置複雜 |
| **Heroku** | $25+ | 老牌 | 昂貴 |

**結論：Zeabur 性價比最高！**

---

## 自動部署（CI/CD）

### GitHub Actions 集成

Zeabur 支持自動部署，當您推送代碼到 GitHub 時自動觸發。

#### 方法 1：在 Zeabur 中啟用自動部署

1. 進入服務設置
2. 找到 **"Git"** 部分
3. 啟用 **"Auto Deploy"**（自動部署）
4. 選擇要監聽的分支（如 `main`）

#### 方法 2：使用 GitHub Actions

創建 `.github/workflows/deploy-zeabur.yml`：

```yaml
name: Deploy to Zeabur

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Zeabur
        uses: zeabur/deploy-action@v1
        with:
          service-id: ${{ secrets.ZEABUR_SERVICE_ID }}
          api-token: ${{ secrets.ZEABUR_API_TOKEN }}
```

**設置 GitHub Secrets：**
1. 在 GitHub 倉庫設置中，添加 Secrets：
   - `ZEABUR_SERVICE_ID`：在 Zeabur 服務頁面找到
   - `ZEABUR_API_TOKEN`：在 Zeabur 設置中生成

---

## 監控和日誌

### 內建監控

Zeabur 提供：
- ✅ CPU 使用率圖表
- ✅ 內存使用率圖表
- ✅ 網絡流量監控
- ✅ 請求數統計

訪問 Dashboard → 服務 → **"Metrics"** 查看。

### 日誌管理

**查看日誌：**

1. **實時日誌：**
   - Dashboard → 服務 → **"Logs"**
   - 或使用 CLI：`zeabur logs -f`

2. **日誌級別過濾：**
   ```bash
   # 只看錯誤
   zeabur logs --level error

   # 搜索關鍵字
   zeabur logs --grep "database"
   ```

3. **持久化日誌：**
   - 應用日誌會寫入 `/app/logs/agenticmath.log`
   - 可以在控制台中下載

### 告警設置

在 Zeabur Dashboard 中設置告警：

1. 進入項目設置
2. 點擊 **"Notifications"**
3. 添加通知渠道：
   - Email
   - Webhook
   - Discord
   - Slack

4. 設置告警規則：
   - CPU > 80%
   - 內存 > 90%
   - 服務宕機
   - 部署失敗

---

## 擴展和優化

### 水平擴展

當流量增加時，可以增加實例數量：

1. 進入服務設置
2. 找到 **"Scaling"**（擴展）
3. 增加 **"Replicas"**（副本數）
4. Zeabur 會自動負載均衡

### 垂直擴展

增加單個實例的資源：

1. 進入服務設置
2. 調整 **"Resources"**（資源）：
   - CPU：0.5 → 1 → 2 vCPU
   - Memory：512MB → 1GB → 2GB

### 性能優化建議

1. **使用 Redis 緩存：**
   - 在 Zeabur 中添加 Redis 服務
   - 緩存 OCR 結果和 LLM 響應

2. **啟用 CDN：**
   - 使用 Zeabur 的 CDN 功能
   - 加速靜態資源訪問

3. **優化數據庫查詢：**
   - 添加索引
   - 使用連接池
   - 定期清理舊數據

4. **使用環境變量優化：**
   ```env
   # 增加工作進程
   API_WORKERS=4

   # 啟用預加載
   PRELOAD_APP=true

   # 優化超時
   TIMEOUT=60
   ```

---

## 常見問題

### Q1: 構建失敗，提示依賴安裝錯誤

**A:** 這通常是因為 Dockerfile 中的系統依賴不完整。我們的 Dockerfile 已經包含所有必需依賴，但如果仍然失敗：

```bash
# 在 Zeabur Console 中運行
apt-get update
apt-get install -y <缺少的包>

# 或更新 Dockerfile 並重新部署
```

### Q2: 數據庫連接失敗

**A:** 檢查環境變量：

```bash
# 在 Zeabur Console 中
echo $DATABASE_URL

# 測試連接
psql $DATABASE_URL -c "SELECT 1"
```

確保 `DATABASE_URL` 格式正確：
```
postgresql://user:password@host:5432/dbname
```

### Q3: 內存不足（OOM）

**A:** 增加內存配置或優化代碼：

1. **增加內存：** 在服務設置中調整 RAM 到 2GB
2. **優化代碼：** 限制並發請求數
3. **使用 swap：** 聯繫 Zeabur 支持

### Q4: 如何查看 PaddleOCR 日誌？

**A:** PaddleOCR 日誌會輸出到標準輸出：

```bash
# 查看實時日誌
zeabur logs -f | grep "paddleocr"

# 或在 Dashboard 的 Logs 中搜索
```

### Q5: 如何重啟服務？

**A:** 兩種方法：

1. **Dashboard：** 服務頁面 → **"Restart"** 按鈕
2. **CLI：** `zeabur service restart <service-id>`

### Q6: 如何回滾到之前的版本？

**A:**

1. 進入服務頁面
2. 點擊 **"Deployments"**（部署歷史）
3. 找到要回滾的版本
4. 點擊 **"Redeploy"**（重新部署）

### Q7: 支持自定義域名嗎？

**A:** 支持！

1. 進入服務 → **"Networking"**
2. 點擊 **"Add Custom Domain"**
3. 輸入域名（如 `api.yourdomain.com`）
4. 在 DNS 設置中添加 CNAME 記錄：
   ```
   api.yourdomain.com → your-app.zeabur.app
   ```
5. Zeabur 會自動配置 SSL 證書

---

## 完整部署檢查清單

部署前請確認：

- [ ] 代碼已推送到 GitHub
- [ ] `.env.example` 已準備好
- [ ] Dockerfile 包含所有依賴
- [ ] `requirements.txt` 是最新的
- [ ] 數據庫遷移文件已提交
- [ ] 已註冊 Zeabur 帳號
- [ ] 已準備 OpenAI API 密鑰

部署時：

- [ ] 創建 Zeabur 項目
- [ ] 添加應用服務（從 Git）
- [ ] 添加 PostgreSQL 服務
- [ ] 配置環境變量
- [ ] 等待構建完成
- [ ] 運行數據庫遷移
- [ ] 生成訪問域名

部署後：

- [ ] 測試健康檢查 `/health`
- [ ] 測試 API 端點
- [ ] 查看日誌確認無錯誤
- [ ] 設置監控告警
- [ ] 配置自動部署
- [ ] （可選）綁定自定義域名

---

## 技術支持

### Zeabur 官方資源

- 📚 文檔：https://zeabur.com/docs
- 💬 Discord：https://discord.gg/zeabur
- 📧 郵箱：support@zeabur.com

### AgenticMath 資源

- 📘 部署文檔：`docs/DEPLOYMENT.md`
- 🔧 故障排除：`docs/TROUBLESHOOTING.md`
- 🧪 測試指南：`docs/PROMPT_TESTING_GUIDE.md`

---

## 總結

Zeabur 是部署 AgenticMath 的**最佳選擇之一**：

✅ **簡單** - 幾分鐘內完成部署
✅ **經濟** - 月費僅 $5-15
✅ **自動化** - Git push 即部署
✅ **中文** - 友好的中文界面
✅ **完整** - 數據庫、監控、日誌一應俱全

**立即開始：** 訪問 [https://zeabur.com](https://zeabur.com) 並開始部署！

---

**最後更新**: 2024-02-15
**版本**: 1.0
