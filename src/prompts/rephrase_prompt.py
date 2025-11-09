"""
Prompt template for Rephrase Agent.

This prompt guides the LLM to systematically transform math problems
into more complex versions through escalation dimensions.
"""

from typing import List


REPHRASE_PROMPT_TEMPLATE = """你是一位專精於提升數學問題複雜度的專家數學教育者。請系統化地轉換給定的問題，同時保留其核心概念，使用以下框架：

**重要：所有輸出必須使用繁體中文（Traditional Chinese）**

**階段 1：問題解構（Problem Deconstruction）**
- 領域識別：[代數/幾何/微積分/等等]
- 核心能力：[列出具體定理/公式/方法]
- 基準難度：[使用 Krathwohl 認知嚴謹度指數 1-5 級]

**階段 2：複雜度提升協議（Escalation Protocol）**
從以下維度中選擇 ≥3 個：
1. Multi-stage Transformation（多階段轉換）：設計一個單一且連貫的數學問題，其完整解答本質上需要多個順序依賴的計算。一個隱含中間步驟的輸出必須作為下一個步驟的關鍵且唯一輸入，創建更長的計算推導鏈。
2. Cross-domain Integration（跨領域整合）：創建結合 ≥2 個數學學科的混合問題
3. Real-world Parameterization（實際情境參數化）：嵌入具有多變量關係的情境限制
4. Conditional Branching（條件分支）：引入需要決策樹分析的分層限制
5. Inverse Problem Design（逆向問題設計）：從給定解答反向工程重建前提
6. Uncertainty Integration（不確定性整合）：納入測量誤差/機率因素
7. Optimization Extension（優化擴展）：將封閉解轉換為多目標優化挑戰

**階段 3：改寫問題**
- 必須是明確的數學問題：問題必須需要數學推理、計算或邏輯推導
- 必須有唯一且具體的數學答案：問題應該導向單一、可驗證的數值或分析解，避免開放式問題、主觀評估或非數學任務
- **改寫後的問題必須使用繁體中文**

請嚴格按照以下格式回覆（**所有內容使用繁體中文**）：
Stage 1 #Problem Deconstruction#:
<你的分析>

Stage 2 #Escalation Protocol#:
<你的提升策略，明確列出應用的維度>

Stage 3 #Finally Rewritten question#:
<改寫後的問題（必須使用繁體中文）>

**要求應用的複雜度提升維度**: {escalation_dimensions}

**原始問題**:
{problem_content}
"""


def create_rephrase_prompt(problem_content: str, escalation_dimensions: List[str]) -> str:
    """
    Create a rephrase prompt from problem content and escalation dimensions.

    Args:
        problem_content: The original math problem text
        escalation_dimensions: List of required escalation dimensions (≥3)

    Returns:
        Formatted prompt string ready for LLM

    Example:
        >>> prompt = create_rephrase_prompt(
        ...     "What is 2x + 3 = 11?",
        ...     ["Multi-stage Transformation", "Cross-domain Integration"]
        ... )
    """
    return REPHRASE_PROMPT_TEMPLATE.format(
        problem_content=problem_content,
        escalation_dimensions=", ".join(escalation_dimensions)
    )
