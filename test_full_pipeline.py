#!/usr/bin/env python3
"""
完整流程测试：照片 → OCR → 生成 N 题

测试完整的用户体验：
1. 上传题目照片
2. OCR 提取文字
3. 指定难度和题数
4. 生成多个高质量题目
5. 查看结果

使用方法：
    python test_full_pipeline.py [照片路径] [难度] [题数]

示例：
    python test_full_pipeline.py test_images/triangle.jpg 3 3
    python test_full_pipeline.py my_problem.png 4 2
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 载入环境变量
load_dotenv()

from src.orchestration.photo_to_problems import (
    PhotoToProblemsOrchestrator,
    PhotoToProblemsRequest
)
from src.storage.database import get_db
from src.utils.latex_formatter import format_math_for_terminal


def print_separator(char="=", length=80):
    """打印分隔线"""
    print(char * length)


def print_section(title: str):
    """打印区段标题"""
    print_separator()
    print(f"  {title}")
    print_separator()
    print()


def validate_inputs(image_path: str, difficulty: int, num_questions: int) -> tuple[bool, str]:
    """
    验证输入参数

    Returns:
        (is_valid, error_message)
    """
    # 验证照片路径
    if not Path(image_path).exists():
        return False, f"❌ 照片不存在: {image_path}"

    # 验证文件类型
    valid_extensions = {'.jpg', '.jpeg', '.png'}
    if Path(image_path).suffix.lower() not in valid_extensions:
        return False, f"❌ 不支持的文件格式。请使用: {', '.join(valid_extensions)}"

    # 验证难度
    if not (1 <= difficulty <= 5):
        return False, f"❌ 难度必须在 1-5 之间，当前值: {difficulty}"

    # 验证题数
    if not (1 <= num_questions <= 5):
        return False, f"❌ 题数必须在 1-5 之间，当前值: {num_questions}"

    return True, ""


def display_results(result):
    """显示结果"""
    print_section("📊 结果总览")

    if not result.success:
        print(f"❌ 处理失败: {result.error_message}")
        return

    # OCR 结果
    print("📸 OCR 提取结果:")
    print(f"   提取文字: {result.extracted_text[:100]}{'...' if len(result.extracted_text) > 100 else ''}")
    print(f"   完整文字长度: {len(result.extracted_text)} 字符")
    print(f"   信心分数: {result.ocr_result.get('confidence_score', 0):.2f}")
    print(f"   包含图表: {'是' if result.ocr_result.get('contains_diagram') else '否'}")
    print(f"   处理时间: {result.ocr_result.get('processing_time_ms', 0)} ms")
    print()

    # 生成统计
    gen_result = result.generation_result
    print(f"🤖 生成统计:")
    print(f"   总生成: {gen_result.total_generated} 题")
    print(f"   通过质检: {gen_result.passed_quality} 题")
    print(f"   最终选择: {gen_result.selected} 题")
    print()

    # 显示题目
    print_section("📝 生成的题目")

    for i, question in enumerate(result.questions, 1):
        print(f"【题目 {i}】{question.get('variant_type', '未知类型')}")
        print(f"难度: {question.get('difficulty', '?')}/5")
        print(f"质量: {question.get('score', 0):.1f}/5")
        print(f"核心概念: {question.get('core_concept', 'Unknown')}")
        print()

        # 格式化数学符号
        content = question.get('content', '')
        formatted_content = format_math_for_terminal(content)
        print(formatted_content)
        print()

        # 显示评审详情（可选）
        review = question.get('review_details', {})
        if review:
            print(f"   💬 评审反馈:")
            print(f"      清晰度: {review.get('clarity', 0):.1f}/5")
            print(f"      连贯性: {review.get('coherence', 0):.1f}/5")
            print(f"      有效性: {review.get('validity', 0):.1f}/5")
            if review.get('feedback'):
                print(f"      建议: {review['feedback'][:100]}...")
        print()
        print_separator("-", 80)
        print()

    # 显示完整的原始文字
    print_section("📄 OCR 提取的完整文字")
    formatted_text = format_math_for_terminal(result.extracted_text)
    print(formatted_text)
    print()


def main():
    """主函数"""
    print_section("🚀 完整流程测试：照片 → OCR → 生成题目")

    # 解析命令行参数
    if len(sys.argv) < 4:
        print("使用方法:")
        print("  python test_full_pipeline.py [照片路径] [难度 1-5] [题数 1-5]")
        print()
        print("示例:")
        print("  python test_full_pipeline.py test_images/triangle.jpg 3 3")
        print("  python test_full_pipeline.py my_problem.png 4 2")
        print()
        print("📌 提示:")
        print("  - 照片格式: JPG, JPEG, PNG")
        print("  - 难度范围: 1 (简单) 到 5 (困难)")
        print("  - 题数范围: 1 到 5 题")
        print()
        sys.exit(1)

    image_path = sys.argv[1]
    try:
        difficulty = int(sys.argv[2])
        num_questions = int(sys.argv[3])
    except ValueError:
        print("❌ 难度和题数必须是整数")
        sys.exit(1)

    # 验证输入
    is_valid, error_msg = validate_inputs(image_path, difficulty, num_questions)
    if not is_valid:
        print(error_msg)
        sys.exit(1)

    # 显示配置
    print("📋 配置信息:")
    print(f"   照片路径: {image_path}")
    print(f"   目标难度: {difficulty}/5")
    print(f"   题目数量: {num_questions}")
    print(f"   最低质量分数: 4.5/5")
    print()

    # 检查环境
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未设置 OPENAI_API_KEY 环境变量")
        print("   请在 .env 文件中配置 API key")
        print()

    # 创建编排器
    print("🔧 初始化系统...")
    db = next(get_db())
    orchestrator = PhotoToProblemsOrchestrator(db_session=db)
    print("✅ 系统初始化完成")
    print()

    # 创建请求
    request = PhotoToProblemsRequest(
        image_path=image_path,
        target_difficulty=difficulty,
        num_questions=num_questions,
        min_quality_score=4.5,
        difficulty_tolerance=0.5
    )

    # 执行处理
    print_section("⚙️  开始处理")
    try:
        result = orchestrator.process(request)

        # 显示结果
        display_results(result)

        # 保存结果到文件（可选）
        if result.success and result.questions:
            output_file = Path("output_questions.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(f"生成时间: {Path(image_path).name}\n")
                f.write(f"难度: {difficulty}/5 | 题数: {len(result.questions)}\n")
                f.write("=" * 80 + "\n\n")

                for i, q in enumerate(result.questions, 1):
                    f.write(f"【题目 {i}】\n")
                    f.write(f"类型: {q.get('variant_type', '未知')}\n")
                    f.write(f"难度: {q.get('difficulty', '?')}/5\n")
                    f.write(f"质量: {q.get('score', 0):.1f}/5\n")
                    f.write(f"\n{q.get('content', '')}\n\n")
                    f.write("-" * 80 + "\n\n")

            print(f"💾 结果已保存到: {output_file}")
            print()

        print_section("✨ 测试完成")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
