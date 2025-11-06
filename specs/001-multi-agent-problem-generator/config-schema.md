# Configuration Schema: AgenticMath System

**版本**: 1.0.0
**最後更新**: 2025-11-06
**相關文件**: [spec.md](./spec.md), [plan.md](./plan.md)

## 概述

本文件定義 AgenticMath 系統的完整配置結構，包含 LLM 設定、OCR 設定、品質控制參數、資料庫連線等所有可配置項目。所有設定均支援透過環境變數 (`.env`) 或程式碼進行配置。

## 配置來源優先順序

```
命令列參數 > 環境變數 (.env) > 預設值 (代碼中定義)
```

範例：
```bash
# 1. 預設值：quality_threshold = 4.5 (代碼中定義)
# 2. .env 檔案覆寫：QUALITY_THRESHOLD=4.7
# 3. 命令列最高優先：--threshold 4.3
python -m src.cli.main process-photo photo.jpg --threshold 4.3  # 最終使用 4.3
```

## Configuration Schema (Pydantic)

### Settings 類別定義

```python
# src/config/settings.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class LLMProvider(str, Enum):
    """LLM 提供者"""
    OPENAI = "openai"

class LogLevel(str, Enum):
    """日誌級別"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class OCRLanguage(str, Enum):
    """OCR 支援的語言"""
    CHINESE_CHT = "chinese_cht"  # 繁體中文
    CHINESE_CHS = "chinese_chs"  # 簡體中文
    ENGLISH = "en"

class ImageFormat(str, Enum):
    """支援的圖片格式"""
    JPEG = "jpeg"
    PNG = "png"

# ============================================================================
# LLM Configuration
# ============================================================================

class LLMConfig(BaseModel):
    """LLM 配置"""

    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM 提供者"
    )

    model: str = Field(
        default="gpt-4o",
        description="模型名稱 (e.g., gpt-4o, gpt-4-turbo)"
    )

    api_key: str = Field(
        ...,
        description="API 金鑰（必填）"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成溫度 (0.0-2.0)，越高越有創意"
    )

    max_tokens: int = Field(
        default=4096,
        ge=512,
        le=128000,
        description="每次請求最大 token 數"
    )

    timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="API 請求超時時間（秒）"
    )

    request_timeout: int = Field(
        default=120,
        ge=30,
        le=600,
        description="總請求超時時間（秒）"
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="API 失敗重試次數"
    )

    @validator("api_key")
    def validate_api_key(cls, v):
        if not v or v == "your-api-key-here":
            raise ValueError("OPENAI_API_KEY must be set in .env file")
        return v

# ============================================================================
# OCR Configuration
# ============================================================================

class OCRConfig(BaseModel):
    """OCR (PaddleOCR) 配置"""

    language: OCRLanguage = Field(
        default=OCRLanguage.CHINESE_CHT,
        description="OCR 辨識語言"
    )

    use_gpu: bool = Field(
        default=False,
        description="是否使用 GPU 加速（需要 CUDA 支援）"
    )

    use_angle_cls: bool = Field(
        default=True,
        description="是否使用角度分類器（自動旋轉校正）"
    )

    confidence_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="最低信心度門檻（低於此值將拒絕 OCR 結果）"
    )

    auto_rotation: bool = Field(
        default=True,
        description="自動偵測並校正圖片旋轉"
    )

    noise_reduction: bool = Field(
        default=True,
        description="執行降噪處理"
    )

    contrast_enhancement: bool = Field(
        default=True,
        description="增強對比度"
    )

    enable_diagram_detection: bool = Field(
        default=True,
        description="啟用圖表檢測功能"
    )

    max_image_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="允許的最大圖片大小（MB）"
    )

    allowed_formats: List[ImageFormat] = Field(
        default=[ImageFormat.JPEG, ImageFormat.PNG],
        description="允許的圖片格式"
    )

    processing_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="OCR 處理超時時間（秒）"
    )

# ============================================================================
# File Upload Configuration
# ============================================================================

class UploadConfig(BaseModel):
    """檔案上傳配置"""

    upload_dir: str = Field(
        default="./uploads",
        description="上傳檔案儲存目錄"
    )

    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="最大上傳檔案大小（MB）"
    )

    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png"],
        description="允許的檔案副檔名"
    )

    cleanup_after_processing: bool = Field(
        default=False,
        description="處理完成後是否刪除原始檔案"
    )

    retain_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="檔案保留天數（過期自動刪除）"
    )

# ============================================================================
# Quality Control Configuration
# ============================================================================

class QualityConfig(BaseModel):
    """品質控制配置"""

    threshold: float = Field(
        default=4.5,
        ge=3.0,
        le=5.0,
        description="品質門檻（1.0-5.0），低於此分數需要修訂"
    )

    max_revise_iterations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Review-Revise 循環的最大迭代次數"
    )

    enable_auto_revision: bool = Field(
        default=True,
        description="是否啟用自動修訂（若為 False，低分題目將直接通過）"
    )

    min_clarity_score: float = Field(
        default=4.0,
        ge=1.0,
        le=5.0,
        description="最低清晰度分數（低於此值強制修訂）"
    )

    min_math_validity_score: float = Field(
        default=4.5,
        ge=1.0,
        le=5.0,
        description="最低數學有效性分數（低於此值拒絕題目）"
    )

# ============================================================================
# Escalation Dimensions Configuration
# ============================================================================

class EscalationDimension(str, Enum):
    """可用的升級維度"""
    MULTI_STAGE = "Multi-stage Transformation"
    CROSS_DOMAIN = "Cross-domain Integration"
    REAL_WORLD = "Real-world Parameterization"
    CONDITIONAL = "Conditional Branching"
    INVERSE = "Inverse Problem Design"
    UNCERTAINTY = "Uncertainty Integration"
    OPTIMIZATION = "Optimization Extension"

class EscalationConfig(BaseModel):
    """題目升級配置"""

    default_dimensions: List[EscalationDimension] = Field(
        default=[
            EscalationDimension.MULTI_STAGE,
            EscalationDimension.CROSS_DOMAIN,
            EscalationDimension.REAL_WORLD
        ],
        description="預設使用的升級維度（至少 3 個）"
    )

    min_dimensions: int = Field(
        default=3,
        ge=1,
        le=7,
        description="最少必須應用的升級維度數量"
    )

    max_dimensions: int = Field(
        default=5,
        ge=3,
        le=7,
        description="最多可應用的升級維度數量"
    )

    @validator("default_dimensions")
    def validate_dimensions(cls, v, values):
        min_dim = values.get("min_dimensions", 3)
        if len(v) < min_dim:
            raise ValueError(f"At least {min_dim} escalation dimensions required")
        return v

# ============================================================================
# Database Configuration
# ============================================================================

class DatabaseConfig(BaseModel):
    """資料庫配置"""

    url: str = Field(
        default="sqlite:///./agenticmath.db",
        description="資料庫連線 URL"
    )

    echo: bool = Field(
        default=False,
        description="是否輸出 SQL 語句（除錯用）"
    )

    pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="連線池大小"
    )

    max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="連線池溢出大小"
    )

    pool_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="連線池超時時間（秒）"
    )

# ============================================================================
# Logging Configuration
# ============================================================================

class LoggingConfig(BaseModel):
    """日誌配置"""

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="日誌級別"
    )

    log_file: Optional[str] = Field(
        default="logs/agenticmath.log",
        description="日誌檔案路徑（None 表示只輸出到 console）"
    )

    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="單個日誌檔案最大大小（MB）"
    )

    backup_count: int = Field(
        default=5,
        ge=1,
        le=100,
        description="保留的日誌檔案備份數量"
    )

    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日誌格式"
    )

    enable_agent_logging: bool = Field(
        default=True,
        description="是否記錄 Agent 執行詳細日誌"
    )

    enable_llm_logging: bool = Field(
        default=True,
        description="是否記錄 LLM API 請求/回應"
    )

# ============================================================================
# Performance Configuration
# ============================================================================

class PerformanceConfig(BaseModel):
    """效能配置"""

    enable_caching: bool = Field(
        default=True,
        description="是否啟用 LLM 回應快取"
    )

    cache_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="快取過期時間（秒）"
    )

    enable_parallel_processing: bool = Field(
        default=True,
        description="是否啟用並行處理（批次模式）"
    )

    max_concurrent_tasks: int = Field(
        default=5,
        ge=1,
        le=50,
        description="最大並行任務數量"
    )

# ============================================================================
# Main Settings Class
# ============================================================================

class Settings(BaseModel):
    """
    AgenticMath 系統完整配置

    從環境變數載入，支援 .env 檔案
    """

    # 子配置
    llm: LLMConfig
    ocr: OCRConfig
    upload: UploadConfig
    quality: QualityConfig
    escalation: EscalationConfig
    database: DatabaseConfig
    logging: LoggingConfig
    performance: PerformanceConfig

    # 全域設定
    environment: str = Field(
        default="development",
        description="執行環境 (development, staging, production)"
    )

    debug: bool = Field(
        default=False,
        description="是否啟用除錯模式"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"  # 支援巢狀環境變數，例如：LLM__MODEL=gpt-4o

    @classmethod
    def from_env(cls) -> "Settings":
        """從環境變數載入配置"""
        import os
        from dotenv import load_dotenv

        load_dotenv()

        return cls(
            llm=LLMConfig(
                provider=LLMProvider(os.getenv("LLM_PROVIDER", "openai")),
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
                timeout=int(os.getenv("OPENAI_TIMEOUT", "60")),
                max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3"))
            ),
            ocr=OCRConfig(
                language=OCRLanguage(os.getenv("OCR_LANGUAGE", "chinese_cht")),
                use_gpu=os.getenv("OCR_USE_GPU", "false").lower() == "true",
                use_angle_cls=os.getenv("OCR_USE_ANGLE_CLS", "true").lower() == "true",
                confidence_threshold=float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.70")),
                auto_rotation=os.getenv("OCR_AUTO_ROTATION", "true").lower() == "true",
                noise_reduction=os.getenv("OCR_NOISE_REDUCTION", "true").lower() == "true",
                contrast_enhancement=os.getenv("OCR_CONTRAST_ENHANCEMENT", "true").lower() == "true",
                enable_diagram_detection=os.getenv("OCR_ENABLE_DIAGRAM_DETECTION", "true").lower() == "true",
                max_image_size_mb=int(os.getenv("OCR_MAX_IMAGE_SIZE_MB", "10")),
                processing_timeout=int(os.getenv("OCR_PROCESSING_TIMEOUT", "30"))
            ),
            upload=UploadConfig(
                upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
                max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
                cleanup_after_processing=os.getenv("CLEANUP_AFTER_PROCESSING", "false").lower() == "true",
                retain_days=int(os.getenv("RETAIN_DAYS", "30"))
            ),
            quality=QualityConfig(
                threshold=float(os.getenv("QUALITY_THRESHOLD", "4.5")),
                max_revise_iterations=int(os.getenv("MAX_REVISE_ITERATIONS", "5")),
                enable_auto_revision=os.getenv("ENABLE_AUTO_REVISION", "true").lower() == "true",
                min_clarity_score=float(os.getenv("MIN_CLARITY_SCORE", "4.0")),
                min_math_validity_score=float(os.getenv("MIN_MATH_VALIDITY_SCORE", "4.5"))
            ),
            escalation=EscalationConfig(
                default_dimensions=cls._parse_dimensions(os.getenv("DEFAULT_ESCALATION_DIMENSIONS", "")),
                min_dimensions=int(os.getenv("MIN_ESCALATION_DIMENSIONS", "3")),
                max_dimensions=int(os.getenv("MAX_ESCALATION_DIMENSIONS", "5"))
            ),
            database=DatabaseConfig(
                url=os.getenv("DATABASE_URL", "sqlite:///./agenticmath.db"),
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
                pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
                max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
                pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
            ),
            logging=LoggingConfig(
                level=LogLevel(os.getenv("LOG_LEVEL", "info")),
                log_file=os.getenv("LOG_FILE", "logs/agenticmath.log"),
                max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB", "10")),
                backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
                enable_agent_logging=os.getenv("ENABLE_AGENT_LOGGING", "true").lower() == "true",
                enable_llm_logging=os.getenv("ENABLE_LLM_LOGGING", "true").lower() == "true"
            ),
            performance=PerformanceConfig(
                enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
                cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
                enable_parallel_processing=os.getenv("ENABLE_PARALLEL_PROCESSING", "true").lower() == "true",
                max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
            ),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )

    @staticmethod
    def _parse_dimensions(dimensions_str: str) -> List[EscalationDimension]:
        """解析逗號分隔的升級維度字串"""
        if not dimensions_str:
            return [
                EscalationDimension.MULTI_STAGE,
                EscalationDimension.CROSS_DOMAIN,
                EscalationDimension.REAL_WORLD
            ]

        dims = [d.strip() for d in dimensions_str.split(",")]
        return [EscalationDimension(d) for d in dims if d]
```

## Environment Variables Reference

### `.env` 檔案範例

```ini
# ============================================================================
# LLM Configuration
# ============================================================================
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4096
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3

# ============================================================================
# OCR Configuration
# ============================================================================
OCR_LANGUAGE=chinese_cht
OCR_USE_GPU=false
OCR_USE_ANGLE_CLS=true
OCR_CONFIDENCE_THRESHOLD=0.70
OCR_AUTO_ROTATION=true
OCR_NOISE_REDUCTION=true
OCR_CONTRAST_ENHANCEMENT=true
OCR_ENABLE_DIAGRAM_DETECTION=true
OCR_MAX_IMAGE_SIZE_MB=10
OCR_PROCESSING_TIMEOUT=30

# ============================================================================
# File Upload Configuration
# ============================================================================
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10
CLEANUP_AFTER_PROCESSING=false
RETAIN_DAYS=30

# ============================================================================
# Quality Control Configuration
# ============================================================================
QUALITY_THRESHOLD=4.5
MAX_REVISE_ITERATIONS=5
ENABLE_AUTO_REVISION=true
MIN_CLARITY_SCORE=4.0
MIN_MATH_VALIDITY_SCORE=4.5

# ============================================================================
# Escalation Dimensions Configuration
# ============================================================================
DEFAULT_ESCALATION_DIMENSIONS=Multi-stage Transformation,Cross-domain Integration,Real-world Parameterization
MIN_ESCALATION_DIMENSIONS=3
MAX_ESCALATION_DIMENSIONS=5

# ============================================================================
# Database Configuration
# ============================================================================
DATABASE_URL=sqlite:///./agenticmath.db
# DATABASE_URL=postgresql://user:password@localhost:5432/agenticmath  # Production
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL=info
LOG_FILE=logs/agenticmath.log
LOG_MAX_FILE_SIZE_MB=10
LOG_BACKUP_COUNT=5
ENABLE_AGENT_LOGGING=true
ENABLE_LLM_LOGGING=true

# ============================================================================
# Performance Configuration
# ============================================================================
ENABLE_CACHING=true
CACHE_TTL=3600
ENABLE_PARALLEL_PROCESSING=true
MAX_CONCURRENT_TASKS=5

# ============================================================================
# Global Settings
# ============================================================================
ENVIRONMENT=development
DEBUG=false
```

## Usage Examples

### 載入配置

```python
from src.config.settings import Settings

# 從環境變數載入
settings = Settings.from_env()

# 訪問配置
print(f"Using LLM: {settings.llm.model}")
print(f"OCR Language: {settings.ocr.language}")
print(f"Quality Threshold: {settings.quality.threshold}")
```

### 程式碼中覆寫配置

```python
from src.config.settings import Settings, OCRConfig

# 載入預設配置
settings = Settings.from_env()

# 覆寫特定配置
settings.ocr.use_gpu = True
settings.ocr.confidence_threshold = 0.80
settings.quality.threshold = 4.8

# 使用修改後的配置
pipeline = MathProblemPipeline(settings)
```

### 不同環境的配置

```bash
# 開發環境
cp .env.development .env

# 測試環境
cp .env.testing .env

# 生產環境
cp .env.production .env
```

**.env.development** (寬鬆設定，快速測試)
```ini
QUALITY_THRESHOLD=4.0
MAX_REVISE_ITERATIONS=3
OCR_CONFIDENCE_THRESHOLD=0.60
LOG_LEVEL=debug
DEBUG=true
```

**.env.production** (嚴格設定，高品質)
```ini
QUALITY_THRESHOLD=4.7
MAX_REVISE_ITERATIONS=5
OCR_CONFIDENCE_THRESHOLD=0.75
LOG_LEVEL=info
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/agenticmath
```

## Configuration Validation

系統啟動時會自動驗證所有配置：

```python
from src.config.settings import Settings
from pydantic import ValidationError

try:
    settings = Settings.from_env()
    print("✅ Configuration is valid")
except ValidationError as e:
    print("❌ Configuration error:")
    for error in e.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        print(f"  {field}: {message}")
    exit(1)
```

驗證範例輸出：
```
❌ Configuration error:
  llm -> api_key: OPENAI_API_KEY must be set in .env file
  quality -> threshold: ensure this value is less than or equal to 5.0
  ocr -> confidence_threshold: ensure this value is greater than or equal to 0.0
```

## Best Practices

### 1. 敏感資訊保護

```bash
# 永遠不要提交 .env 到版本控制
echo ".env" >> .gitignore

# 提供 .env.example 作為範本
cp .env .env.example
# 手動移除 .env.example 中的敏感資訊
```

### 2. 環境特定配置

```python
# 根據環境自動選擇配置
import os

env = os.getenv("ENVIRONMENT", "development")
env_file = f".env.{env}"

if os.path.exists(env_file):
    settings = Settings.from_env(env_file)
else:
    settings = Settings.from_env()  # 使用預設 .env
```

### 3. 配置驗證測試

```python
# tests/test_config.py
import pytest
from src.config.settings import Settings, OCRConfig

def test_ocr_config_validation():
    """測試 OCR 配置驗證"""

    # 有效配置
    config = OCRConfig(confidence_threshold=0.70)
    assert config.confidence_threshold == 0.70

    # 無效配置應該拋出錯誤
    with pytest.raises(ValueError):
        OCRConfig(confidence_threshold=1.5)  # 超過 1.0

    with pytest.raises(ValueError):
        OCRConfig(confidence_threshold=-0.1)  # 小於 0.0

def test_quality_threshold_validation():
    """測試品質門檻驗證"""
    from src.config.settings import QualityConfig

    # 有效範圍
    config = QualityConfig(threshold=4.5)
    assert 3.0 <= config.threshold <= 5.0

    # 超出範圍
    with pytest.raises(ValueError):
        QualityConfig(threshold=5.5)
```

## Troubleshooting

### 問題：配置無法載入

**症狀**: `FileNotFoundError: .env file not found`

**解決方案**:
```bash
# 確認 .env 檔案存在
ls -la .env

# 如果不存在，從範例創建
cp .env.example .env

# 編輯並填入必要的值
nano .env
```

### 問題：環境變數未生效

**症狀**: 修改 `.env` 後配置沒有改變

**解決方案**:
1. **重啟程式**: 環境變數只在程式啟動時載入
2. **檢查語法**: 確保 `.env` 格式正確（無空格、正確的等號）
3. **檢查優先順序**: 命令列參數會覆寫環境變數

```bash
# 正確格式
QUALITY_THRESHOLD=4.5

# 錯誤格式（有空格）
QUALITY_THRESHOLD = 4.5

# 錯誤格式（引號不必要）
QUALITY_THRESHOLD="4.5"
```

### 問題：資料庫連線失敗

**症狀**: `OperationalError: unable to open database file`

**解決方案**:
```bash
# SQLite: 確保目錄存在
mkdir -p $(dirname $DATABASE_URL)

# PostgreSQL: 檢查連線字串格式
# postgresql://username:password@host:port/database
DATABASE_URL=postgresql://agenticmath:password@localhost:5432/agenticmath
```

---

**版本歷史**:
- v1.0.0 (2025-11-06): 初始版本，包含完整配置 schema 和 OCR 設定
