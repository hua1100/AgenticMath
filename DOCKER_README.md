# Docker 部署指南

## 快速开始

### 1. 设置环境变量

创建 `.env` 文件（或导出环境变量）：

```bash
# 在 Mac 上
export OPENAI_API_KEY="your-api-key-here"

# 或创建 .env 文件
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 2. 构建并运行

```bash
# 构建 Docker 镜像
docker-compose build

# 运行完整测试（包含 OCR）
docker-compose up agenticmath
```

### 3. 交互式使用

如果您想进入容器手动运行命令：

```bash
# 启动容器（保持运行）
docker-compose run --rm agenticmath bash

# 在容器内：
# 运行完整流程测试
python test_full_pipeline.py /app/tests/fixtures/diagrams/triangle.jpg 3 3

# 运行 OCR 调试工具
python test_ocr_debug.py /app/tests/fixtures/diagrams/triangle.jpg

# 运行单元测试
pytest tests/

# 退出容器
exit
```

### 4. 使用自己的图片

将图片复制到项目目录，然后：

```bash
# 在 Mac 上复制图片到 tests/fixtures/diagrams/
cp ~/Desktop/my_math_problem.png tests/fixtures/diagrams/

# 运行 Docker 容器
docker-compose run --rm agenticmath python test_full_pipeline.py /app/tests/fixtures/diagrams/my_math_problem.png 3 3
```

## 常用命令

### 运行特定测试

```bash
# 只测试 OCR
docker-compose run --rm agenticmath pytest tests/integration/test_ocr_pipeline.py -v

# 运行题目生成测试（跳过 OCR）
docker-compose run --rm agenticmath python test_generation_only.py 3 3
```

### 清理

```bash
# 停止并删除容器
docker-compose down

# 删除容器和数据卷（包括 PaddleOCR 模型）
docker-compose down -v

# 删除镜像
docker-compose down --rmi all
```

### 查看日志

```bash
# 实时查看日志
docker-compose logs -f agenticmath

# 查看最后 100 行
docker-compose logs --tail=100 agenticmath
```

## 性能优化

### 持久化 PaddleOCR 模型

Docker volume `paddleocr-models` 会保存下载的模型，避免每次都重新下载。

如果需要清理：
```bash
docker volume rm agenticmath_paddleocr-models
```

### 使用 GPU（如果可用）

修改 `Dockerfile`，使用 CUDA 基础镜像并安装 GPU 版本的 PaddlePaddle：

```dockerfile
FROM nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04
# ... 然后在 requirements.txt 中使用 paddlepaddle-gpu
```

## 故障排除

### PaddleOCR 仍然卡住

如果在 Docker 中仍然遇到问题，检查：
1. Docker 分配的内存是否足够（至少 4GB）
2. 尝试使用不同的 PaddleOCR 语言模型：`lang='en'` 或 `lang='ch'`

### 权限问题

如果遇到文件权限问题：
```bash
# 修改所有权
sudo chown -R $USER:$USER .
```

### 网络问题（无法下载模型）

如果 PaddleOCR 无法下载模型：
```bash
# 手动下载模型到 .paddleocr/ 目录
# 或使用国内镜像
```

## 生产部署

对于生产环境，建议：

1. **使用多阶段构建**优化镜像大小
2. **添加健康检查**
3. **配置日志聚合**
4. **使用 Kubernetes** 进行编排

示例 docker-compose 生产配置见 `docker-compose.prod.yml`
