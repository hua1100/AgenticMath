"""
Prompt template for Revise Agent.

This prompt guides the LLM to improve math problems based on specific suggestions
from the Review Agent, while preserving mathematical intent.
"""

from typing import List


REVISE_PROMPT_TEMPLATE = """你是一位數學問題改進專家，請根據以下建議優化問題：

**重要：所有輸出必須使用繁體中文（Traditional Chinese）**

{suggestions}

優化要求：

1. 清晰度與語法 (1–5)：問題必須語法正確、措辭精確且易於理解。應避免用詞或表達上的歧義。

2. 邏輯連貫性與完整性 (1–5)：問題的所有元素（例如：已知資訊、限制條件、關係、目標）必須邏輯相連且充分。問題應呈現清晰、順序的推理路徑，不應缺少指定解題方法所需的資訊。

3. 數學有效性與可解性 (1–5)：問題必須本質上是數學問題，其所有前提和條件必須*相互一致*且*數學上合理*。它必須導向*唯一、可解的數值或分析答案*，遵守所有數學規則和指定範圍（例如：機率總和為1、有效的幾何性質、實數解）。如果任何條件導致數學矛盾或不可能/未定義的解（例如：調整後總機率 > 1、在給定限制內無有效解的方程），此標準評分極低，且必須指出確切的數學不一致性。避免開放式或非數學問題。

原始問題：{rephrased_question}

** 輸出要求 **
**僅**以下列純文本格式回應（**所有內容使用繁體中文**，不要包含 JSON 或任何額外評論）：

###revised_question###
<改進後的完整問題（必須使用繁體中文）>

###revision_notes###
<具體的修訂說明（使用繁體中文）>
"""


def create_revise_prompt(rephrased_question: str, suggestions: List[str]) -> str:
    """
    Create a revise prompt from rephrased question and suggestions.

    Args:
        rephrased_question: The problem to improve
        suggestions: List of specific improvements from Review Agent

    Returns:
        Formatted prompt string ready for LLM

    Example:
        >>> prompt = create_revise_prompt(
        ...     rephrased_question="A rectangular garden has a length...",
        ...     suggestions=[
        ...         "Explicitly state answer format",
        ...         "Add units clarification"
        ...     ]
        ... )
    """
    # Format suggestions as bullet list
    suggestions_text = "\n".join(f"- {s}" for s in suggestions)

    return REVISE_PROMPT_TEMPLATE.format(
        rephrased_question=rephrased_question,
        suggestions=suggestions_text
    )
