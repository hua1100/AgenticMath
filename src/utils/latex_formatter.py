"""
LaTeX 数学符号格式化工具

将 LaTeX 格式的数学表达式转换为终端友好的显示格式。
支持常见的数学符号和希腊字母。
"""

import re


def latex_to_unicode(text: str) -> str:
    """
    将 LaTeX 格式的数学表达式转换为 Unicode 文本。

    处理：
    - LaTeX 内联公式 \(...\) 和 $...$
    - 常见希腊字母
    - 上标和下标
    - 数学运算符

    Args:
        text: 包含 LaTeX 格式的文本

    Returns:
        转换后的 Unicode 文本

    Example:
        >>> latex_to_unicode(r"\(2\sin^2 x + 3\cos x - 3 = 0\)")
        "2sin²x + 3cosx - 3 = 0"
    """
    if not text:
        return text

    # LaTeX 符号到 Unicode 的映射
    replacements = {
        # 希腊字母（小写）
        r'\alpha': 'α',
        r'\beta': 'β',
        r'\gamma': 'γ',
        r'\delta': 'δ',
        r'\epsilon': 'ε',
        r'\theta': 'θ',
        r'\lambda': 'λ',
        r'\mu': 'μ',
        r'\pi': 'π',
        r'\sigma': 'σ',
        r'\phi': 'φ',
        r'\omega': 'ω',

        # 希腊字母（大写）
        r'\Gamma': 'Γ',
        r'\Delta': 'Δ',
        r'\Theta': 'Θ',
        r'\Lambda': 'Λ',
        r'\Pi': 'Π',
        r'\Sigma': 'Σ',
        r'\Phi': 'Φ',
        r'\Omega': 'Ω',

        # 三角函数
        r'\sin': 'sin',
        r'\cos': 'cos',
        r'\tan': 'tan',
        r'\cot': 'cot',
        r'\sec': 'sec',
        r'\csc': 'csc',

        # 运算符和符号
        r'\leq': '≤',
        r'\geq': '≥',
        r'\neq': '≠',
        r'\approx': '≈',
        r'\times': '×',
        r'\div': '÷',
        r'\pm': '±',
        r'\infty': '∞',
        r'\sqrt': '√',
        r'\sum': '∑',
        r'\prod': '∏',
        r'\int': '∫',

        # 其他常用符号
        r'\in': '∈',
        r'\notin': '∉',
        r'\subset': '⊂',
        r'\supset': '⊃',
        r'\cap': '∩',
        r'\cup': '∪',
        r'\emptyset': '∅',
        r'\forall': '∀',
        r'\exists': '∃',

        # 度数符号
        r'^\circ': '°',
        r'\circ': '°',
    }

    result = text

    # 先处理内联公式标记 \(...\) 和 $...$
    # 暂时保留内容，只移除标记
    result = re.sub(r'\\\(', '', result)
    result = re.sub(r'\\\)', '', result)
    result = re.sub(r'\$', '', result)

    # 先处理度数符号（需要在通用上标处理之前）
    # 匹配 ^\ 后跟 circ
    result = re.sub(r'\^\\circ', '°', result)
    result = result.replace(r'\circ', '°')

    # 应用其他符号替换（在处理上下标之前）
    for latex_cmd, unicode_char in replacements.items():
        if latex_cmd not in [r'^\circ', r'\circ']:  # 已经处理过了
            result = result.replace(latex_cmd, unicode_char)

    # 处理上标 (^{...} 和 ^x)
    # 上标数字映射
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
        'n': 'ⁿ',
    }

    # 处理 ^{...} 格式
    def replace_superscript_braces(match):
        content = match.group(1)
        return ''.join(superscript_map.get(c, c) for c in content)

    result = re.sub(r'\^\{([^}]+)\}', replace_superscript_braces, result)

    # 处理 ^x 格式（单字符上标）
    def replace_superscript_single(match):
        char = match.group(1)
        return superscript_map.get(char, f'^{char}')

    result = re.sub(r'\^([0-9n])', replace_superscript_single, result)

    # 处理下标 (_{...} 和 _x)
    subscript_map = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
        'n': 'ₙ', 'i': 'ᵢ', 'j': 'ⱼ',
    }

    # 处理 _{...} 格式
    def replace_subscript_braces(match):
        content = match.group(1)
        return ''.join(subscript_map.get(c, c) for c in content)

    result = re.sub(r'_\{([^}]+)\}', replace_subscript_braces, result)

    # 处理 _x 格式（单字符下标）
    def replace_subscript_single(match):
        char = match.group(1)
        return subscript_map.get(char, f'_{char}')

    result = re.sub(r'_([0-9inj])', replace_subscript_single, result)

    # 处理花括号（移除空的花括号）
    result = re.sub(r'\{\}', '', result)

    # 处理 \frac{a}{b} 为 a/b
    result = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', result)

    # 移除剩余的反斜杠（对于未映射的命令）
    result = re.sub(r'\\([a-zA-Z]+)', r'\1', result)

    # 清理多余的空格
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def format_math_for_terminal(text: str, preserve_latex: bool = False) -> str:
    """
    为终端显示格式化数学文本。

    Args:
        text: 原始文本（可能包含 LaTeX）
        preserve_latex: 是否保留原始 LaTeX 格式（默认 False）

    Returns:
        格式化后的文本
    """
    if preserve_latex:
        return text

    return latex_to_unicode(text)


if __name__ == "__main__":
    # 测试示例
    test_cases = [
        r"\(2\sin^2 x + 3\cos x - 3 = 0\)",
        r"\(0^\circ \leq x \leq 360^\circ\)",
        r"$\alpha + \beta = \gamma$",
        r"\frac{a}{b} + \frac{c}{d}",
        r"x_1 + x_2 + ... + x_n",
        r"E = mc^2",
    ]

    print("LaTeX 格式化测试：\n")
    for test in test_cases:
        formatted = latex_to_unicode(test)
        print(f"原始: {test}")
        print(f"格式化: {formatted}")
        print()
