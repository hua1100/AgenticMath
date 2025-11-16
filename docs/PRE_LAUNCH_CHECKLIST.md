# AgenticMath 上线前检查清单

完整的上线前测试和验证清单，确保生产环境部署顺利。

---

## 📋 检查清单总览

- [x] 表示已完成
- [ ] 表示待完成
- ⚠️ 表示需要注意

---

## 1. 代码质量检查

### 1.1 代码审查
- [ ] 所有代码已经过同行审查
- [ ] 没有 TODO 或 FIXME 注释
- [ ] 代码符合项目规范（PEP 8）
- [ ] 敏感信息已移除（API keys, passwords）

```bash
# 检查代码风格
black --check src/
ruff check src/

# 检查 TODO
grep -r "TODO\|FIXME" src/

# 检查敏感信息
grep -r "sk-\|password\|secret" src/ --exclude-dir=.git
```

### 1.2 类型检查
- [ ] MyPy 类型检查通过

```bash
mypy src/ --ignore-missing-imports
```

### 1.3 依赖安全
- [ ] 所有依赖已更新到安全版本
- [ ] 无已知安全漏洞

```bash
pip install safety pip-audit
safety check
pip-audit
```

---

## 2. 功能测试

### 2.1 单元测试
- [ ] 所有单元测试通过
- [ ] 代码覆盖率 ≥ 80%
- [ ] 无跳过的测试

```bash
# 运行单元测试
pytest tests/unit/ -v

# 检查覆盖率
pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

**预期结果**:
```
tests/unit/ ..................... [ 100% ]

Coverage: 85%
All tests passed
```

### 2.2 集成测试
- [ ] OCR 管道集成测试通过
- [ ] Rephrase 管道集成测试通过
- [ ] Solution 生成管道测试通过
- [ ] 数据库操作测试通过

```bash
# 运行集成测试
pytest tests/integration/ -v

# 测试 OCR 管道
pytest tests/integration/test_ocr_pipeline.py -v

# 测试 Solution 生成
pytest tests/integration/test_solution_generation.py -v
```

### 2.3 合约验证测试
- [ ] Solver Agent 合约测试通过
- [ ] Rephrase Agent 合约测试通过
- [ ] Review Agent 合约测试通过
- [ ] Revise Agent 合约测试通过

```bash
# 运行合约测试
pytest tests/contract/ -v
```

### 2.4 端到端测试（需要真实 API）
- [ ] 照片上传 → OCR → 生成题目流程正常
- [ ] 文本输入 → 生成题目流程正常
- [ ] 生成解答功能正常

```bash
# 设置 API key
export OPENAI_API_KEY=your-production-key

# 运行 E2E 测试
pytest tests/e2e/ -v

# 手动测试 CLI
./agenticmath upload test_images/triangle.jpg -d 3 -n 3
./agenticmath generate "Solve: 2x + 3 = 11" -s
```

**验收标准**:
- ✅ OCR 准确度 ≥ 85%
- ✅ 题目质量分数 ≥ 4.5
- ✅ 处理时间 < 60 秒

---

## 3. 性能测试

### 3.1 OCR 性能测试
- [ ] OCR 处理时间 < 3 秒
- [ ] 文字识别准确度 ≥ 85%
- [ ] 图表检测成功率 ≥ 80%

```bash
# 测试 OCR 性能
python test_ocr_auto.py

# 批量测试
for img in test_images/*.jpg; do
    time python -c "from src.ocr import process_image; process_image('$img')"
done
```

### 3.2 LLM 调用性能测试
- [ ] 单题生成时间 < 60 秒
- [ ] 解答生成时间 < 30 秒
- [ ] API 调用成功率 ≥ 99%

```bash
# 测试题目生成性能
time ./agenticmath generate "Solve: x^2 - 5x + 6 = 0" -d 3

# 测试解答生成性能
time ./agenticmath generate "Solve: x^2 - 5x + 6 = 0" -s
```

### 3.3 并发测试
- [ ] 支持 5 个并发请求
- [ ] 无数据库死锁
- [ ] 无内存泄漏

创建并发测试脚本 `tests/load/test_concurrent.py`:
```python
import concurrent.futures
import time
from src.cli.main import cli

def generate_problem(problem_text):
    """生成单个题目"""
    # 实现生成逻辑
    pass

def test_concurrent_requests(num_requests=10):
    """测试并发请求"""
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(generate_problem, f"Problem {i}")
            for i in range(num_requests)
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    end_time = time.time()

    print(f"处理 {num_requests} 个请求耗时: {end_time - start_time:.2f} 秒")
    print(f"成功: {len([r for r in results if r])} / {num_requests}")

    return results

if __name__ == "__main__":
    results = test_concurrent_requests(10)
    assert len(results) == 10, "部分请求失败"
    print("✅ 并发测试通过")
```

运行测试:
```bash
python tests/load/test_concurrent.py
```

### 3.4 负载测试
- [ ] 在预期负载下系统稳定
- [ ] CPU 使用率 < 80%
- [ ] 内存使用率 < 90%

使用压力测试工具（如 Locust）:
```python
# locustfile.py
from locust import HttpUser, task, between

class AgenticMathUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def generate_problem(self):
        self.client.post("/api/generate", json={
            "problem": "Solve: 2x + 3 = 11",
            "difficulty": 3
        })
```

运行负载测试:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

---

## 4. 数据库测试

### 4.1 数据库迁移测试
- [ ] 迁移脚本无错误
- [ ] 所有表正确创建
- [ ] 索引已创建
- [ ] 外键约束正确

```bash
# 测试迁移（干净数据库）
rm agenticmath.db  # 如果使用 SQLite
alembic upgrade head

# 验证表结构
python -c "
from src.storage.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', tables)

for table in tables:
    columns = [c['name'] for c in inspector.get_columns(table)]
    indexes = inspector.get_indexes(table)
    print(f'\nTable: {table}')
    print(f'Columns: {columns}')
    print(f'Indexes: {len(indexes)}')
"
```

**预期输出**:
```
Tables: ['problems', 'solutions', 'quality_assessments', 'rephrase_sessions', 'agent_executions', 'uploaded_images']

Table: problems
Columns: ['id', 'content', 'domain', 'competencies', ...]
Indexes: 3
```

### 4.2 数据完整性测试
- [ ] 外键约束生效
- [ ] 级联删除正常
- [ ] 唯一约束生效

```python
# tests/integration/test_database_integrity.py
def test_foreign_key_constraint(test_db):
    """测试外键约束"""
    from src.models import Problem, Solution
    from uuid import uuid4

    # 尝试创建引用不存在问题的解答
    solution = Solution(
        id=uuid4(),
        problem_id=uuid4(),  # 不存在的 problem_id
        thought_process="Test",
        final_answer="Test"
    )
    test_db.add(solution)

    with pytest.raises(IntegrityError):
        test_db.commit()
```

### 4.3 数据库性能测试
- [ ] 查询响应时间 < 100ms
- [ ] 插入操作 < 50ms
- [ ] 批量操作正常

```python
import time
from src.models import Problem

def test_database_performance(test_db):
    """测试数据库性能"""
    # 批量插入
    start = time.time()
    problems = [
        Problem(id=uuid4(), content=f"Problem {i}", ...)
        for i in range(1000)
    ]
    test_db.bulk_save_objects(problems)
    test_db.commit()
    insert_time = time.time() - start

    # 查询
    start = time.time()
    result = test_db.query(Problem).limit(100).all()
    query_time = time.time() - start

    print(f"插入 1000 条记录: {insert_time:.2f}s")
    print(f"查询 100 条记录: {query_time*1000:.2f}ms")

    assert insert_time < 5, "插入太慢"
    assert query_time < 0.1, "查询太慢"
```

### 4.4 备份和恢复测试
- [ ] 备份脚本正常工作
- [ ] 恢复流程测试成功
- [ ] 数据完整性验证

```bash
# 创建备份
pg_dump -U agenticmath_user -d agenticmath > backup_test.sql

# 创建测试数据库
createdb -U postgres agenticmath_test

# 恢复备份
psql -U agenticmath_user -d agenticmath_test < backup_test.sql

# 验证数据
psql -U agenticmath_user -d agenticmath_test -c "SELECT COUNT(*) FROM problems;"

# 清理
dropdb -U postgres agenticmath_test
rm backup_test.sql
```

---

## 5. 安全测试

### 5.1 输入验证测试
- [ ] 文件上传大小限制生效
- [ ] 文件类型验证生效
- [ ] SQL 注入防护有效
- [ ] XSS 防护有效（如有 Web 界面）

```python
def test_file_upload_size_limit():
    """测试文件大小限制"""
    large_file = create_large_file(15 * 1024 * 1024)  # 15MB

    with pytest.raises(ValueError, match="文件太大"):
        upload_image(large_file)

def test_file_type_validation():
    """测试文件类型验证"""
    exe_file = "test.exe"

    with pytest.raises(ValueError, match="不支持的文件类型"):
        upload_image(exe_file)

def test_sql_injection_protection(test_db):
    """测试 SQL 注入防护"""
    malicious_input = "'; DROP TABLE problems; --"

    # 使用 SQLAlchemy ORM，应该自动防护
    problem = test_db.query(Problem).filter(
        Problem.content == malicious_input
    ).first()

    # 表应该仍然存在
    assert problem is None
    assert test_db.query(Problem).count() >= 0  # 表未被删除
```

### 5.2 API Key 安全测试
- [ ] API Key 从环境变量读取
- [ ] API Key 不出现在日志中
- [ ] API Key 不出现在错误消息中

```bash
# 检查代码中是否有硬编码的 API key
grep -r "sk-" src/ --exclude-dir=.git

# 检查日志中是否泄露 API key
grep "sk-" logs/*.log
```

### 5.3 权限测试
- [ ] 文件权限正确设置
- [ ] 数据库访问权限正确
- [ ] 日志文件权限安全

```bash
# 检查文件权限
ls -la logs/ uploads/

# 上传目录应该只有应用可写
chmod 755 uploads/

# 日志目录权限
chmod 750 logs/

# .env 文件权限
chmod 600 .env
```

---

## 6. 配置验证

### 6.1 环境变量检查
- [ ] 所有必需的环境变量已设置
- [ ] 环境变量格式正确
- [ ] 生产配置已启用

```bash
# 检查必需的环境变量
python -c "
import os
required_vars = [
    'OPENAI_API_KEY',
    'DATABASE_URL',
    'ENVIRONMENT',
]

missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'❌ 缺少环境变量: {missing}')
    exit(1)
else:
    print('✅ 所有必需环境变量已设置')
"

# 验证配置加载
python -c "
from src.config import get_settings

settings = get_settings()
print(f'Environment: {settings.environment}')
print(f'LLM Model: {settings.llm.model}')
print(f'Database: {settings.database.url}')
print(f'Quality Threshold: {settings.quality_control.quality_threshold}')

assert settings.environment == 'production', '未使用生产环境配置'
print('✅ 配置验证通过')
"
```

### 6.2 日志配置检查
- [ ] 日志级别设置为 INFO
- [ ] 日志文件路径正确
- [ ] 日志轮转配置正确

```bash
# 测试日志写入
python -c "
import logging
from src.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=settings.logging.level.upper(),
    filename=str(settings.logging.file)
)

logger = logging.getLogger(__name__)
logger.info('测试日志写入')
print('✅ 日志配置正常')
"

# 检查日志文件
cat logs/agenticmath.log | grep "测试日志写入"
```

---

## 7. 监控和告警

### 7.1 监控配置
- [ ] 健康检查端点配置
- [ ] 应用指标收集配置
- [ ] 错误追踪配置（Sentry等）

```bash
# 测试健康检查端点（如果有 API）
curl http://localhost:8000/health

# 预期响应
# {"status": "healthy", "timestamp": "2025-01-16T..."}
```

### 7.2 告警设置
- [ ] CPU 使用率告警（> 80%）
- [ ] 内存使用率告警（> 90%）
- [ ] 磁盘空间告警（> 85%）
- [ ] 错误率告警（> 5%）
- [ ] API 调用失败告警

### 7.3 日志聚合
- [ ] 集中式日志收集配置
- [ ] 日志搜索功能可用
- [ ] 日志保留策略设置

---

## 8. 文档检查

### 8.1 技术文档
- [ ] README.md 完整准确
- [ ] API 文档（如有）完整
- [ ] 部署文档完整
- [ ] 配置文档完整

```bash
# 检查文档文件
ls -la docs/

# 应该包含:
# - DEPLOYMENT.md (部署指南)
# - CLI_GUIDE.md (CLI 使用指南)
# - TESTING.md (测试指南)
# - PRE_LAUNCH_CHECKLIST.md (上线检查清单)
```

### 8.2 运维文档
- [ ] 监控指南完整
- [ ] 故障排查指南完整
- [ ] 备份恢复流程文档完整
- [ ] 应急响应流程文档完整

---

## 9. 基础设施检查

### 9.1 服务器配置
- [ ] 服务器资源满足要求
- [ ] 防火墙规则配置正确
- [ ] SSL/TLS 证书配置（生产环境）
- [ ] 域名解析正确

```bash
# 检查服务器资源
free -h
df -h
nproc

# 检查防火墙
sudo ufw status

# 检查 SSL 证书（如有）
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### 9.2 数据库服务器
- [ ] PostgreSQL 正常运行
- [ ] 数据库备份配置
- [ ] 连接池配置合理
- [ ] 性能参数优化

```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查连接数
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 检查数据库大小
psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('agenticmath'));"
```

---

## 10. 最终验收测试

### 10.1 完整用户流程测试
- [ ] 新用户首次使用流程顺畅
- [ ] 常见使用场景全部测试
- [ ] 错误处理用户友好

**测试场景 1: 照片上传生成题目**
```bash
# 1. 准备测试照片
cp test_images/trigonometry.jpg /tmp/test.jpg

# 2. 运行 CLI
./agenticmath upload /tmp/test.jpg -d 3 -n 3

# 3. 验证输出
# - OCR 结果准确
# - 生成 3 个题目
# - 质量分数 ≥ 4.5
# - 显示成本统计
```

**测试场景 2: 文本生成题目和解答**
```bash
# 1. 生成题目
./agenticmath generate "在直角三角形ABC中，AB=10，BC=6，求AC" -d 3 -s

# 2. 验证输出
# - 生成高质量题目
# - 包含详细解答
# - 推理过程完整
```

### 10.2 边界情况测试
- [ ] 超大图片处理
- [ ] 模糊图片处理
- [ ] 网络中断恢复
- [ ] 数据库连接失败恢复

### 10.3 性能基准测试
- [ ] 记录基准性能数据
- [ ] 建立性能监控基线
- [ ] 设置性能告警阈值

```bash
# 性能基准测试脚本
python scripts/benchmark.py

# 预期输出示例:
# OCR 平均处理时间: 2.3秒
# 题目生成平均时间: 45秒
# 解答生成平均时间: 25秒
# 数据库查询平均时间: 15ms
```

---

## 11. 上线检查

### 11.1 上线前最后检查
- [ ] 所有测试通过
- [ ] 代码已合并到主分支
- [ ] 版本号已更新
- [ ] Git tag 已创建
- [ ] 部署脚本测试通过

```bash
# 创建发布 tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 验证部署脚本
bash scripts/deploy.sh --dry-run
```

### 11.2 回滚计划
- [ ] 回滚步骤文档化
- [ ] 回滚脚本测试
- [ ] 数据库快照创建

```bash
# 创建部署前快照
pg_dump -U agenticmath_user -d agenticmath > backup_pre_deployment.sql

# 记录当前版本
git rev-parse HEAD > DEPLOYED_VERSION.txt
```

### 11.3 上线通知
- [ ] 团队成员已通知
- [ ] 用户（如有）已通知
- [ ] 监控值班已安排

---

## 12. 上线后验证

### 12.1 立即验证（上线后 5 分钟内）
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] 数据库连接正常
- [ ] 日志正常写入

```bash
# 检查服务状态
sudo systemctl status agenticmath

# 检查健康
curl http://localhost:8000/health

# 检查日志
tail -f logs/agenticmath.log
```

### 12.2 短期验证（上线后 1 小时内）
- [ ] 无错误日志
- [ ] CPU/内存使用正常
- [ ] 响应时间正常
- [ ] 用户功能正常

### 12.3 持续监控（上线后 24 小时）
- [ ] 监控所有指标
- [ ] 收集用户反馈
- [ ] 记录性能数据
- [ ] 准备优化计划

---

## 检查清单总结

### 关键指标

| 指标 | 目标 | 当前值 | 状态 |
|------|------|--------|------|
| 单元测试通过率 | 100% | ___ | ☐ |
| 代码覆盖率 | ≥80% | ___ | ☐ |
| OCR 准确度 | ≥85% | ___ | ☐ |
| 题目质量分数 | ≥4.5 | ___ | ☐ |
| 处理时间 | <60s | ___ | ☐ |
| 安全漏洞 | 0 | ___ | ☐ |
| 文档完整性 | 100% | ___ | ☐ |

### 签名确认

- [ ] 开发负责人: ____________ 日期: ______
- [ ] 测试负责人: ____________ 日期: ______
- [ ] 运维负责人: ____________ 日期: ______
- [ ] 项目经理: ______________ 日期: ______

---

**最后更新**: 2025-01-16
**版本**: 1.0
**下次审查日期**: ______
