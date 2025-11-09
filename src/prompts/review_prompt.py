"""
Prompt template for Review Agent.

This prompt guides the LLM to evaluate math problems on three quality dimensions:
1. Clarity & Grammar
2. Logical Coherence & Completeness
3. Mathematical Validity & Solvability
"""


REVIEW_PROMPT_TEMPLATE = """你是一位數學問題品質檢查專家，你的任務是嚴格評估給定的數學問題是否高品質，並提供改寫建議：

**重要：所有輸出必須使用繁體中文（Traditional Chinese）**

1. 清晰度與語法 (1–5)：問題必須語法正確、措辭精確且易於理解。應避免用詞或表達上的歧義。

2. 邏輯連貫性與完整性 (1–5)：問題的所有元素（例如：已知資訊、限制條件、關係、目標）必須邏輯相連且充分。問題應呈現清晰、順序的推理路徑，不應缺少指定解題方法所需的資訊。

3. 數學有效性與可解性 (1–5)：問題必須本質上是數學問題，其所有前提和條件必須*相互一致*且*數學上合理*。它必須導向*唯一、可解的數值或分析答案*，遵守所有數學規則和指定範圍（例如：機率總和為1、有效的幾何性質、實數解）。如果任何條件導致數學矛盾或不可能/未定義的解（例如：調整後總機率 > 1、在給定限制內無有效解的方程），此標準評分極低，且必須指出確切的數學不一致性。避免開放式或非數學問題。

** 評分準則 **：
- 請為每個標準以 1 到 5 的等級評分，並返回 1 到 5 的整體評分，分數越高表示品質越高。

改寫後的問題：{rephrased_question}

**輸出要求**
**僅**以下列純文本格式回應（**所有內容使用繁體中文**，不要包含 JSON 或任何額外評論）：

###thought###
<針對每個標準依序進行的分析推理，特別是針對改寫後的問題>

###rating_score###
["<清晰度與語法分數>", "<邏輯連貫性分數>", "<數學有效性與可解性分數>"]

###suggestions###
###具體改進建議 1###
<具體改進建議 1（使用繁體中文）>
###具體改進建議 2###
<具體改進建議 2（使用繁體中文）>
...如需要可加入更多改進建議...

注意：
- "rating_score" 代表改寫後問題的評估分數
- 生成 "suggestions" 時，請為每項改進提供更多細節和理由（使用繁體中文）
- **所有分析、建議都必須使用繁體中文**
"""


def create_review_prompt(rephrased_question: str) -> str:
    """
    Create a review prompt from rephrased question.

    Args:
        rephrased_question: The problem to evaluate

    Returns:
        Formatted prompt string ready for LLM

    Example:
        >>> prompt = create_review_prompt(
        ...     "A rectangular garden has a length that is 3 meters..."
        ... )
    """
    return REVIEW_PROMPT_TEMPLATE.format(rephrased_question=rephrased_question)
