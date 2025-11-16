# 🚀 Zeabur 快速開始指南

最快 5 分鐘部署 AgenticMath 到 Zeabur！

## 一鍵部署（推薦）

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates)

> 💡 **提示**: 點擊按鈕後，Zeabur 會自動：
> - 克隆代碼倉庫
> - 部署 PostgreSQL 數據庫
> - 構建並運行應用
> - 生成訪問域名

## 手動部署（5 步驟）

### 步驟 1：註冊 Zeabur

訪問 [https://zeabur.com](https://zeabur.com) 並註冊帳號（支持 GitHub 登入）

### 步驟 2：創建項目

1. 登入 [Zeabur Dashboard](https://dash.zeabur.com)
2. 點擊 **"Create Project"**
3. 輸入項目名稱：`agenticmath`
4. 選擇區域：**Hong Kong**（香港）

### 步驟 3：部署應用

1. 點擊 **"Add Service"** → **"Git"**
2. 選擇您的 GitHub 倉庫（需要先 fork 本項目）
3. 選擇分支：`main`
4. 等待構建完成（約 3-5 分鐘）

### 步驟 4：添加數據庫

1. 點擊 **"Add Service"** → **"Marketplace"**
2. 選擇 **"PostgreSQL"**
3. 等待部署完成

### 步驟 5：配置環境變量

1. 進入應用服務 → **"Variables"**
2. 添加以下變量：

```env
# 必需
OPENAI_API_KEY=sk-your-openai-api-key

# 數據庫（自動組合）
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE}

# 應用配置
ENVIRONMENT=production
DEBUG=false
```

3. 保存並重啟服務

### 步驟 6：運行數據庫遷移

1. 進入應用服務 → **"Console"**
2. 運行命令：
   ```bash
   alembic upgrade head
   ```

### 步驟 7：獲取訪問 URL

1. 進入應用服務 → **"Networking"**
2. 點擊 **"Generate Domain"**
3. 複製生成的 URL（例如：`https://your-app.zeabur.app`）

## 驗證部署

測試健康檢查：

```bash
curl https://your-app.zeabur.app/health
```

預期響應：

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

## 使用 CLI 快速部署

如果您熟悉命令行，可以使用我們的快速部署腳本：

```bash
# 1. 安裝 Zeabur CLI
npm install -g @zeabur/cli

# 2. 運行快速部署腳本
./scripts/deploy_zeabur.sh
```

腳本會引導您完成所有步驟。

## 成本估算

**開發/測試環境：** 約 $5-7/月
- 應用服務：0.5 vCPU + 1GB RAM = ~$3/月
- PostgreSQL：0.5 vCPU + 512MB RAM = ~$2/月
- 存儲：10GB = ~$1.5/月

**生產環境：** 約 $15/月
- 應用服務：1 vCPU + 2GB RAM = ~$6/月
- PostgreSQL：1 vCPU + 1GB RAM = ~$4/月
- 存儲：20GB = ~$3/月
- 流量：~5GB = ~$2/月

> 💡 **提示**: Zeabur 提供 $5 免費額度（開發者計劃），足夠測試使用！

## 下一步

部署完成後：

1. **閱讀完整文檔**：[docs/ZEABUR_DEPLOYMENT.md](docs/ZEABUR_DEPLOYMENT.md)
2. **配置監控**：在 Zeabur Dashboard 中設置告警
3. **測試 API**：參考 API 文檔測試端點
4. **綁定域名**：（可選）使用自定義域名

## 常見問題

### Q: 構建失敗怎麼辦？

A: 查看構建日誌（Build Logs），通常是依賴安裝問題。我們的 Dockerfile 已包含所有必需依賴。

### Q: 如何查看應用日誌？

A: Dashboard → 應用服務 → **"Logs"** 標籤

### Q: 如何重啟服務？

A: Dashboard → 應用服務 → **"Restart"** 按鈕

### Q: 支持自定義域名嗎？

A: 支持！在 **"Networking"** 中添加自定義域名，Zeabur 會自動配置 SSL。

## 獲取幫助

- 📘 完整文檔：[docs/ZEABUR_DEPLOYMENT.md](docs/ZEABUR_DEPLOYMENT.md)
- 🔧 故障排除：[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- 💬 Zeabur Discord：https://discord.gg/zeabur
- 📧 Zeabur 支持：support@zeabur.com

---

**🎉 開始部署吧！只需 5 分鐘！**

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/templates)
