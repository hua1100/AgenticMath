#!/bin/bash
# 快速安装脚本 - 完整流程所需依赖

echo "================================================"
echo "  安装完整流程所需依赖"
echo "================================================"
echo ""

# 检查 Python 版本
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $python_version"
echo ""

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  建议在虚拟环境中安装依赖"
    echo "   创建虚拟环境: python -m venv venv"
    echo "   激活虚拟环境: source venv/bin/activate  (macOS/Linux)"
    echo "                  venv\\Scripts\\activate  (Windows)"
    echo ""
    read -p "是否继续安装？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ 虚拟环境: $VIRTUAL_ENV"
    echo ""
fi

# 安装依赖
echo "📦 安装核心依赖..."
pip install -U pip setuptools wheel

echo ""
echo "📦 安装 AgenticMath 依赖..."
pip install -r requirements.txt

echo ""
echo "================================================"
echo "  ✅ 安装完成！"
echo "================================================"
echo ""
echo "现在可以运行："
echo "  python test_full_pipeline.py [照片路径] [难度] [题数]"
echo ""
echo "示例："
echo "  python test_full_pipeline.py my_problem.jpg 3 3"
echo ""
