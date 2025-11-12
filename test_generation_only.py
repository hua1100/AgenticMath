#!/usr/bin/env python3
"""
測試題目生成流程（跳過 OCR）

這個腳本直接使用文字內容測試題目生成，繞過 OCR 步驟。
"""

import sys
from src.orchestration.user_driven_generator import (
    ProblemGenerator,
    UserRequest,
)
from src.agents.llm_client import LLMClient
from src.agents.rephrase_agent import RephraseAgent
from src.agents.review_agent import ReviewAgent
from src.agents.revise_agent import ReviseAgent
from src.orchestration.iteration_manager import IterationManager


def main():
    """測試題目生成流程"""

    # 模擬從 OCR 提取的文字
    original_content = """
    三角形 ABC 中，AB = 8 公分，BC = 6 公分，角 B = 90度。
    求斜邊 AC 的長度。
    """

    target_difficulty = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    num_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print("=" * 80)
    print("  🚀 題目生成測試（跳過 OCR）")
    print("=" * 80)
    print()
    print(f"📋 配置信息:")
    print(f"   原始內容: {original_content.strip()[:50]}...")
    print(f"   目標難度: {target_difficulty}/5")
    print(f"   題目數量: {num_questions}")
    print()

    print("🔧 初始化系統...")
    llm_client = LLMClient()
    rephrase_agent = RephraseAgent(llm_client=llm_client)
    review_agent = ReviewAgent(llm_client=llm_client)
    revise_agent = ReviseAgent(llm_client=llm_client)
    iteration_manager = IterationManager(
        review_agent=review_agent,
        revise_agent=revise_agent
    )

    generator = ProblemGenerator(
        rephrase_agent=rephrase_agent,
        review_agent=review_agent,
        iteration_manager=iteration_manager
    )
    print("✅ 系統初始化完成")
    print()

    print("=" * 80)
    print("  ⚙️  開始生成題目")
    print("=" * 80)
    print()

    request = UserRequest(
        original_content=original_content.strip(),
        target_difficulty=target_difficulty,
        num_questions=num_questions
    )

    try:
        result = generator.generate(request)

        print("=" * 80)
        print("  ✅ 生成完成")
        print("=" * 80)
        print()

        print(f"📊 生成結果:")
        print(f"   成功生成: {len(result.questions)} 題")
        print(f"   處理時間: {result.metadata.get('total_time_ms', 0)} ms")
        print()

        for i, question in enumerate(result.questions, 1):
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  題目 {i}")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print()
            print(f"📝 內容:")
            print(question['content'])
            print()
            print(f"📊 品質分數: {question.get('quality_score', 'N/A')}/5.0")
            print(f"📈 難度: {question.get('difficulty', 'N/A')}/5")
            print(f"🔄 迭代次數: {question.get('iterations', 'N/A')}")
            print()

        print("=" * 80)
        print("  🎉 測試成功完成！")
        print("=" * 80)

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
