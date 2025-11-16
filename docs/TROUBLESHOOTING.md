# AgenticMath 故障排除指南

本文檔幫助您解決 AgenticMath 部署和使用過程中遇到的常見問題。

## 目錄

1. [依賴安裝問題](#依賴安裝問題)
2. [PaddleOCR 問題](#paddleocr-問題)
3. [OpenCV 問題](#opencv-問題)
4. [數據庫問題](#數據庫問題)
5. [Docker 問題](#docker-問題)
6. [API 問題](#api-問題)
7. [性能問題](#性能問題)

---

## 依賴安裝問題

### 問題：pip install 失敗

#### 症狀
```bash
ERROR: Could not build wheels for opencv-python
ERROR: Failed building wheel for paddleocr
```

#### 解決方案

**方案 1: 使用快速安裝腳本**

```bash
./scripts/quick_install.sh
```

此腳本會自動安裝所有必要的系統依賴。

**方案 2: 手動安裝系統依賴**

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libatlas-base-dev \
    fonts-noto-cjk
```

macOS:
```bash
brew install libomp jpeg libpng libtiff webp
```

**方案 3: 使用預編譯的 wheel**

```bash
# 先安裝 numpy（某些包需要）
pip install numpy==1.24.4

# 再安裝其他依賴
pip install opencv-python==4.9.0.80
pip install paddleocr==2.7.0
```

### 問題：缺少系統庫

#### 症狀
```
ImportError: libGL.so.1: cannot open shared object file
ImportError: libgthread-2.0.so.0: cannot open shared object file
```

#### 解決方案

**檢查缺少的庫**

```bash
# 找到 OpenCV 的 .so 文件
find venv/lib -name "*.so" | grep cv2

# 檢查依賴
ldd venv/lib/python3.11/site-packages/cv2/cv2*.so
```

**安裝缺少的庫**

根據 ldd 輸出，安裝對應的包：

```bash
# libGL.so.1
sudo apt install libgl1-mesa-glx

# libgthread-2.0.so.0
sudo apt install libglib2.0-0

# libgomp.so.1
sudo apt install libgomp1

# libSM.so.6
sudo apt install libsm6

# libXrender.so.1
sudo apt install libxrender1

# libXext.so.6
sudo apt install libxext6
```

### 問題：Python 版本不匹配

#### 症狀
```
ERROR: Python 3.11+ required
```

#### 解決方案

**Ubuntu 20.04/22.04 安裝 Python 3.11**

```bash
# 添加 deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# 安裝 Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# 驗證安裝
python3.11 --version
```

**使用 pyenv**

```bash
# 安裝 pyenv
curl https://pyenv.run | bash

# 安裝 Python 3.11
pyenv install 3.11.7
pyenv local 3.11.7

# 創建虛擬環境
python -m venv venv
```

---

## PaddleOCR 問題

### 問題：PaddleOCR 導入失敗

#### 症狀
```python
ImportError: cannot import name 'PaddleOCR' from 'paddleocr'
```

#### 解決方案

**重新安裝 PaddleOCR 和 PaddlePaddle**

```bash
pip uninstall paddleocr paddlepaddle paddlepaddle-gpu -y
pip install paddlepaddle==2.5.2
pip install paddleocr==2.7.0
```

### 問題：PaddleOCR 模型下載失敗

#### 症狀
```
ConnectionError: Failed to download model
Timeout: Model download timeout
```

#### 解決方案

**方案 1: 手動下載模型**

```bash
# 創建模型目錄
mkdir -p ~/.paddleocr/whl/

# 下載檢測模型
wget https://paddleocr.bj.bcebos.com/PP-OCRv3/chinese/ch_PP-OCRv3_det_infer.tar \
  -O ~/.paddleocr/whl/ch_PP-OCRv3_det_infer.tar

# 下載識別模型
wget https://paddleocr.bj.bcebos.com/PP-OCRv3/chinese/ch_PP-OCRv3_rec_infer.tar \
  -O ~/.paddleocr/whl/ch_PP-OCRv3_rec_infer.tar

# 下載分類模型
wget https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar \
  -O ~/.paddleocr/whl/ch_ppocr_mobile_v2.0_cls_infer.tar

# 解壓
cd ~/.paddleocr/whl/
tar -xf ch_PP-OCRv3_det_infer.tar
tar -xf ch_PP-OCRv3_rec_infer.tar
tar -xf ch_ppocr_mobile_v2.0_cls_infer.tar
```

**方案 2: 使用鏡像源**

```bash
# 設置環境變量使用國內鏡像
export HUB_MIRROR=https://gitee.com/paddlepaddle/PaddleOCR

# 重新初始化 PaddleOCR
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR()"
```

### 問題：OCR 識別率低

#### 症狀
- 中文識別錯誤率高
- 數學公式無法識別

#### 解決方案

**調整 PaddleOCR 參數**

```python
from paddleocr import PaddleOCR

# 使用更高精度的模型
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch',
    det_db_thresh=0.3,      # 降低檢測閾值
    det_db_box_thresh=0.5,  # 降低框閾值
    rec_batch_num=6,        # 增加批次大小
    use_gpu=True            # 如果有 GPU
)
```

**使用更適合的語言模型**

```python
# 繁體中文
ocr = PaddleOCR(lang='chinese_cht')

# 英文
ocr = PaddleOCR(lang='en')

# 多語言
ocr = PaddleOCR(lang='ch')  # 中英混合
```

---

## OpenCV 問題

### 問題：OpenCV 無法顯示圖像

#### 症狀
```python
cv2.error: OpenCV(4.9.0) ... GTK+ 2.x or higher
```

#### 解決方案

**安裝 GTK 庫**

```bash
sudo apt install libgtk2.0-dev libgtk-3-dev
```

**使用無 GUI 版本**

```bash
pip uninstall opencv-python
pip install opencv-python-headless==4.9.0.80
```

### 問題：圖像讀取失敗

#### 症狀
```python
img = cv2.imread('test.jpg')
# img is None
```

#### 解決方案

**檢查文件路徑**

```python
from pathlib import Path

image_path = Path("test.jpg")
if not image_path.exists():
    raise FileNotFoundError(f"圖像不存在: {image_path}")

img = cv2.imread(str(image_path.absolute()))
```

**檢查圖像格式支持**

```python
# 檢查 OpenCV 支持的格式
import cv2
print(cv2.getBuildInformation())
```

---

## 數據庫問題

### 問題：無法連接 PostgreSQL

#### 症狀
```
psycopg2.OperationalError: could not connect to server
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
```

#### 解決方案

**檢查 PostgreSQL 服務狀態**

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

**檢查連接參數**

```bash
# 測試連接
psql -h localhost -U agenticmath_user -d agenticmath

# 如果失敗，檢查 .env 文件
cat .env | grep DATABASE_URL
```

**修復權限問題**

```bash
# 登入 PostgreSQL
sudo -u postgres psql

# 創建用戶和數據庫
CREATE USER agenticmath_user WITH PASSWORD 'your_password';
CREATE DATABASE agenticmath OWNER agenticmath_user;
GRANT ALL PRIVILEGES ON DATABASE agenticmath TO agenticmath_user;
```

### 問題：數據庫遷移失敗

#### 症狀
```
alembic.util.exc.CommandError: Can't locate revision identified by
```

#### 解決方案

**重置遷移歷史**

```bash
# 備份數據庫
pg_dump -U agenticmath_user agenticmath > backup.sql

# 刪除 alembic 版本表
psql -U agenticmath_user -d agenticmath -c "DROP TABLE IF EXISTS alembic_version;"

# 重新初始化
alembic stamp head
alembic upgrade head
```

**從頭開始**

```bash
# 刪除數據庫
dropdb -U postgres agenticmath

# 重新創建
createdb -U postgres agenticmath -O agenticmath_user

# 運行遷移
alembic upgrade head
```

---

## Docker 問題

### 問題：Docker 構建失敗

#### 症狀
```
ERROR: failed to solve: process "/bin/sh -c apt-get update..." did not complete successfully
```

#### 解決方案

**清理 Docker 緩存**

```bash
docker builder prune -a
docker system prune -a
```

**使用正確的 Dockerfile**

```bash
# 確保使用項目根目錄的 Dockerfile
docker build -t agenticmath:latest .

# 查看構建日誌
docker build --progress=plain -t agenticmath:latest .
```

### 問題：容器啟動失敗

#### 症狀
```
Error response from daemon: failed to create shim
Container exited with code 1
```

#### 解決方案

**查看容器日誌**

```bash
docker logs <container_id>
docker logs agenticmath_app
```

**檢查環境變量**

```bash
# 進入容器檢查
docker exec -it agenticmath_app bash
env | grep OPENAI
```

**使用 docker-compose 調試**

```bash
# 使用調試模式啟動
docker-compose up --no-start
docker-compose start
docker-compose logs -f app
```

### 問題：依賴缺失（在容器中）

#### 症狀
```
ImportError: libGL.so.1: cannot open shared object file
```

#### 解決方案

**更新 Dockerfile**

確保 Dockerfile 包含所有必要的系統庫（參考項目中的 Dockerfile）。

**重新構建鏡像**

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

---

## API 問題

### 問題：API 啟動失敗

#### 症狀
```
ERROR: [Errno 98] Address already in use
```

#### 解決方案

**查找佔用端口的進程**

```bash
lsof -i :8000
# 或
netstat -tulpn | grep 8000
```

**終止佔用端口的進程**

```bash
kill -9 <PID>
```

**使用不同端口**

```bash
uvicorn src.api.server:app --port 8001
```

### 問題：CORS 錯誤

#### 症狀
```
Access to fetch at 'http://api.example.com' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

#### 解決方案

**配置 CORS**

在 `src/api/server.py` 中添加：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 性能問題

### 問題：推理速度慢

#### 症狀
- 單次請求超過 30 秒
- CPU 使用率 100%

#### 解決方案

**使用 GPU 加速**

```bash
# 安裝 GPU 版本的 PaddlePaddle
pip uninstall paddlepaddle
pip install paddlepaddle-gpu==2.5.2

# 在代碼中啟用 GPU
ocr = PaddleOCR(use_gpu=True)
```

**調整並發數**

```python
# 在 settings.py 中
class APISettings(BaseModel):
    workers: int = 4  # Uvicorn workers
    max_concurrent_requests: int = 10
```

**使用批處理**

```python
# 批量處理圖像
results = ocr.ocr(image_list, batch_size=8)
```

### 問題：內存不足

#### 症狀
```
MemoryError
Killed (OOM)
```

#### 解決方案

**限制並發請求**

```python
# 使用信號量限制並發
from asyncio import Semaphore

semaphore = Semaphore(5)  # 最多 5 個並發請求

async def process_image(image):
    async with semaphore:
        return await ocr_service.process(image)
```

**增加 swap 空間**

```bash
# 創建 4GB swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**優化模型加載**

```python
# 使用單例模式，避免重複加載模型
class OCRService:
    _instance = None
    _ocr = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._ocr = PaddleOCR()  # 只加載一次
        return cls._instance
```

---

## 運行依賴檢查工具

在遇到問題時，首先運行依賴檢查工具診斷問題：

```bash
# 激活虛擬環境
source venv/bin/activate

# 運行檢查
python scripts/check_dependencies.py
```

此工具會檢查：
- Python 版本
- 核心包安裝
- OpenCV 功能
- PaddleOCR 功能
- 數據庫驅動

根據輸出結果，可以快速定位問題。

---

## 獲取幫助

如果以上方案都無法解決問題：

1. **查看日誌**
   ```bash
   # 應用日誌
   tail -f logs/agenticmath.log

   # 系統日誌
   journalctl -u agenticmath -n 100
   ```

2. **啟用調試模式**
   ```bash
   # 在 .env 中
   DEBUG=true
   LOG_LEVEL=debug
   ```

3. **收集診斷信息**
   ```bash
   # 系統信息
   uname -a
   python --version
   pip list

   # 依賴檢查
   python scripts/check_dependencies.py > diagnostics.txt
   ```

4. **提交 Issue**
   - GitHub: [AgenticMath Issues](https://github.com/your-org/AgenticMath/issues)
   - 包含診斷信息和錯誤日誌

---

## 預防措施

**開發環境**

1. 使用虛擬環境隔離依賴
2. 固定依賴版本（requirements.txt）
3. 定期運行依賴檢查
4. 使用 pre-commit hooks

**生產環境**

1. 使用 Docker 容器化
2. 自動化部署流程
3. 監控系統資源
4. 定期備份數據庫
5. 使用 CI/CD 測試變更

**最佳實踐**

1. 在部署前運行完整測試套件
2. 使用 `--dry-run` 測試部署腳本
3. 保持文檔更新
4. 記錄所有配置變更
