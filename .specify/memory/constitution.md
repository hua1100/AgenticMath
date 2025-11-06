<!--
Sync Impact Report:
- Version: 1.0.0 → 1.1.0
- Last Amended: 2025-11-06
- Modified Principles:
  * Added Principle 7: Chinese-First Documentation
  * Added Principle 8: Open Source Technology Preference
- Added Sections: Language Policy, Technology Selection Guidelines
- Removed Sections: None
- Templates Status:
  ✅ plan-template.md - aligned with constitution
  ✅ spec-template.md - aligned with constitution
  ✅ tasks-template.md - aligned with constitution
- Follow-up TODOs:
  * Update all future specifications to use Traditional Chinese
  * Evaluate open-source OCR solutions (DeepSeek OCR, PaddleOCR)
-->

# AgenticMath 專案憲章

**版本**: 1.1.0
**批准日期**: 2025-11-06
**最後修訂**: 2025-11-06

## Purpose

AgenticMath is an intelligent agent system designed to generate high-quality mathematics problems that help students improve their understanding. Students can upload problems they find confusing or have made mistakes on, and the system generates conceptually similar problems that help learners discover concepts, strategies, and patterns through clear, logically consistent, and error-free questions.

## Core Principles

### Principle 1: Educational Value First

**Statement**: All generated problems MUST prioritize pedagogical effectiveness over technical complexity. Every problem must have a clear learning objective and help students build conceptual understanding.

**Rationale**: The system's primary purpose is to aid learning. Problems that are technically correct but pedagogically ineffective fail the core mission. Problems must scaffold learning progression and target specific misconceptions.

**Rules**:
- Problems MUST include clear learning objectives
- Generated problems MUST be aligned with the source problem's conceptual domain
- Problems MUST target specific skills, concepts, or common misconceptions
- Difficulty progression MUST be appropriate for the learner's level

### Principle 2: Mathematical Correctness and Clarity

**Statement**: All generated problems MUST be mathematically correct, logically consistent, and free from ambiguity. Problems MUST have well-defined solutions and clear problem statements.

**Rationale**: Incorrect or ambiguous problems damage student confidence and understanding. Mathematical rigor is non-negotiable in an educational context.

**Rules**:
- All problems MUST be verified for mathematical correctness before delivery
- Problem statements MUST be unambiguous and use precise mathematical language
- Solutions MUST be unique or explicitly state when multiple solutions exist
- Edge cases and boundary conditions MUST be clearly defined

### Principle 3: Conceptual Consistency

**Statement**: Generated problems MUST maintain conceptual similarity to the source problem while varying surface features. The underlying mathematical concept, strategy, or pattern MUST be preserved or clearly related.

**Rationale**: For effective learning transfer, students need to practice the same concept in varied contexts. Problems that drift conceptually fail to reinforce the target learning objective.

**Rules**:
- Generated problems MUST share the same core mathematical concept as the source
- Surface features (numbers, context, presentation) SHOULD vary to encourage generalization
- The required problem-solving strategy MUST be comparable in complexity
- Concept drift MUST be detected and prevented in the generation process

### Principle 4: Testability and Validation

**Statement**: All system components MUST be testable with automated verification. Problem generation quality MUST be measurable through defined metrics.

**Rationale**: Given the critical nature of educational content, we cannot rely on subjective assessment alone. Automated testing ensures consistency and catches regressions.

**Rules**:
- Problem generation pipelines MUST have unit tests for each component
- Generated problems MUST be validated against quality criteria automatically
- Integration tests MUST verify end-to-end generation workflows
- Quality metrics (correctness, clarity, conceptual alignment) MUST be measurable

### Principle 5: Simplicity and Maintainability

**Statement**: System architecture MUST favor simple, composable components over complex monolithic solutions. Code MUST be readable and well-documented.

**Rationale**: Educational systems evolve as pedagogical understanding improves. Complex architectures resist change and accumulate technical debt that impedes educational improvements.

**Rules**:
- Components MUST have single, well-defined responsibilities
- Dependencies MUST be explicit and minimized
- Each module MUST have clear documentation explaining its educational purpose
- New abstractions MUST be justified by concrete complexity reduction

### Principle 6: Explainability and Transparency

**Statement**: The system MUST be able to explain why specific problems were generated and how they relate to the source problem. Generation decisions MUST be traceable.

**Rationale**: Educators and students benefit from understanding the system's reasoning. Transparency builds trust and enables pedagogical refinement.

**Rules**:
- Problem generation MUST log key decision points and rationales
- The relationship between source and generated problems MUST be explicitly documented
- Generation parameters and their effects MUST be understandable by educators
- System behavior MUST be reproducible for debugging and improvement

### Principle 7: Chinese-First Documentation

**Statement**: All project documentation, specifications, user interfaces, and communications MUST be written in Traditional Chinese as the primary language. English may be used as a secondary reference language for technical terms or external library documentation.

**Rationale**: The target users are Chinese-speaking students and educators. Chinese-first documentation ensures clarity, accessibility, and cultural relevance. This reduces cognitive load for users and developers, enabling better understanding of educational context and pedagogical nuances that may be lost in translation.

**Rules**:
- All specifications (spec.md, plan.md, data-model.md, etc.) MUST be written in Traditional Chinese
- User-facing content (UI text, error messages, help documentation) MUST be in Traditional Chinese
- Code comments SHOULD be in Traditional Chinese where possible, English acceptable for technical clarity
- Variable and function names SHOULD use English for code compatibility and conventions
- Technical terms without clear Chinese equivalents MAY retain English with Chinese explanation
- Commit messages SHOULD be in Traditional Chinese with English summary for international contributors
- Mathematical notation and formulas use international standards (language-agnostic)

### Principle 8: Open Source Technology Preference

**Statement**: The system SHOULD prefer open-source solutions over proprietary alternatives when functionality, reliability, and maintainability are comparable. This applies especially to core dependencies and infrastructure components.

**Rationale**: Open-source technologies provide transparency, community support, cost-effectiveness, and freedom from vendor lock-in. For educational software, open-source aligns with knowledge-sharing values and enables customization for specific pedagogical needs. It also ensures long-term sustainability and allows for community contributions.

**Rules**:
- Core technologies (OCR, agent frameworks, databases) SHOULD be open-source when suitable
- Proprietary solutions MAY be used when open-source alternatives lack critical features or maturity
- Technology selection MUST document comparison between open-source and proprietary options
- Cost-benefit analysis MUST consider total cost of ownership (licensing, support, maintenance)
- Open-source solutions MUST be evaluated for:
  * Active maintenance and community support
  * Documentation quality (especially Chinese documentation)
  * Performance and scalability characteristics
  * Integration complexity and learning curve
- For OCR specifically: Evaluate DeepSeek OCR, PaddleOCR, Tesseract before considering commercial APIs
- For agent frameworks: Evaluate open-source options (AutoGen, CrewAI) before proprietary SDKs

## Language Policy

### Documentation Languages

**Primary Language**: Traditional Chinese (繁體中文)
- All specifications, design documents, user documentation
- User interface text, error messages, help content
- Internal communications, meeting notes, decision records

**Secondary Language**: English
- Technical terms without clear Chinese equivalents (with Chinese explanation)
- References to external libraries and frameworks
- International collaboration and open-source contributions
- Variable/function names for code compatibility

### Code Language Conventions

```python
# ✅ Recommended: English names with Chinese comments
class ProblemRephraser:
    """問題改寫器 - 將原始問題轉換為高難度版本"""

    def rephrase(self, original_problem: str) -> str:
        """改寫問題

        Args:
            original_problem: 原始問題文字

        Returns:
            改寫後的問題文字
        """
        # 識別數學領域
        domain = self._identify_domain(original_problem)

        # 應用升級策略
        escalated = self._apply_escalation(original_problem, domain)

        return escalated
```

### Documentation Structure

- **規格文件 (Specifications)**: 100% Traditional Chinese
- **技術文件 (Technical Docs)**: Traditional Chinese with English technical terms in parentheses
- **API 文件 (API Docs)**: Bilingual - Chinese descriptions with English code examples
- **README**: Traditional Chinese with English summary section

## Technology Selection Guidelines

### Evaluation Criteria

When choosing between technologies, evaluate in this order:

1. **功能完整性 (Functional Completeness)**
   - Does it meet all requirements?
   - Are there critical missing features?

2. **開源優先 (Open Source Priority)**
   - Open source preferred over proprietary (Principle 8)
   - Consider license compatibility (MIT, Apache 2.0 preferred)

3. **社群支援 (Community Support)**
   - Active development and maintenance?
   - Chinese language documentation and community?
   - Issue response time and community size?

4. **效能與擴展性 (Performance & Scalability)**
   - Meets performance requirements?
   - Scales to expected user load?

5. **整合複雜度 (Integration Complexity)**
   - Learning curve for team?
   - Integration effort with existing stack?
   - Quality of documentation and examples?

6. **總體擁有成本 (Total Cost of Ownership)**
   - Licensing costs (if proprietary)
   - Hosting and infrastructure costs
   - Maintenance and support costs
   - Training and onboarding costs

### OCR Technology Selection (Specific Guidance)

For photo-to-text extraction, evaluate in this order:

1. **開源 OCR 解決方案 (Open Source OCR)**:
   - **PaddleOCR** (Baidu, 百度飛槳OCR)
     * Pros: Excellent Chinese support, multiple models, active development, good documentation
     * Cons: Requires GPU for best performance, model size large
   - **DeepSeek OCR** (if available as open source)
     * Pros: Potentially better accuracy, modern architecture
     * Cons: Evaluate availability, documentation, community support
   - **Tesseract OCR** (Google)
     * Pros: Mature, widely used, multi-language
     * Cons: Lower accuracy for handwriting, older technology

2. **商業 OCR API (Commercial OCR APIs)** - Only if open source insufficient:
   - Google Cloud Vision API
   - Azure Computer Vision
   - Alibaba Cloud OCR (阿里雲文字識別)

**決策流程 (Decision Flow)**:
1. 測試 PaddleOCR 準確度 (Test PaddleOCR accuracy)
2. 如果手寫識別不足，測試 DeepSeek OCR (If handwriting insufficient, test DeepSeek)
3. 如果準確度仍 <80%，考慮商業 API (If accuracy still <80%, consider commercial)
4. 記錄決策理由和測試結果 (Document decision rationale and test results)

### Agent Framework Selection (Specific Guidance)

For multi-agent orchestration, evaluate:

1. **開源 Agent 框架 (Open Source Frameworks)**:
   - **AutoGen** (Microsoft, but open source)
   - **CrewAI**
   - **LangGraph** (LangChain ecosystem)
   - **Pydantic AI**

2. **商業 Agent SDK (Commercial SDKs)**:
   - OpenAI Agent SDK (Swarm)
   - Microsoft Agent Framework
   - Anthropic SDK (minimal agent support)

**評估重點 (Evaluation Focus)**:
- 多代理協調能力 (Multi-agent coordination)
- 狀態管理 (State management)
- 錯誤處理和重試 (Error handling and retry)
- 可觀察性 (Observability/tracing)
- 中文文檔品質 (Chinese documentation quality)

## Governance

### Amendment Procedure

1. **Proposal**: Any team member may propose an amendment by creating a document outlining:
   - The proposed change
   - Rationale for the change
   - Impact on existing principles and system components
   - Alternative approaches considered

2. **Review**: The proposal must be reviewed by at least one other team member who assesses:
   - Alignment with project purpose
   - Impact on existing codebase
   - Necessity vs. complexity tradeoff

3. **Adoption**: Amendments are adopted when consensus is reached among active contributors

4. **Propagation**: Upon adoption, the constitution version is incremented and dependent templates are updated

### Versioning Policy

- **MAJOR** (X.0.0): Backward-incompatible changes to principles; principle removal or fundamental redefinition
- **MINOR** (0.X.0): New principles added; material expansion of existing principles
- **PATCH** (0.0.X): Clarifications, wording improvements, typo fixes

### Compliance Review

- Each feature specification MUST include a Constitution Check section
- Pull requests MUST reference relevant principles in their description
- Violations of principles MUST be explicitly justified in design documents
- Quarterly reviews assess codebase alignment with constitutional principles

## Principle Application Guidelines

### When Principles Conflict

1. **Educational Value** takes precedence in all cases - technical elegance never justifies pedagogical ineffectiveness
2. **Mathematical Correctness** cannot be compromised - an educationally valuable but incorrect problem is unacceptable
3. **Simplicity** yields to **Testability** when verification is critical for correctness

### Justifying Principle Violations

If a design must violate a principle, document:
1. Which principle is being violated and how
2. Why the violation is necessary for the feature
3. What simpler alternatives were considered and why they were insufficient
4. How the violation will be contained and prevented from spreading

### Review Questions

Before finalizing any design, ask:
- Does this help students learn more effectively? (Principle 1)
- Is this mathematically rigorous and unambiguous? (Principle 2)
- Does this maintain conceptual coherence? (Principle 3)
- Can we automatically verify this works correctly? (Principle 4)
- Is this the simplest approach that could work? (Principle 5)
- Can we explain why the system behaves this way? (Principle 6)
- Is documentation in Traditional Chinese with clear technical terms? (Principle 7)
- Have we evaluated open-source alternatives? (Principle 8)

---

**憲章結束 (End of Constitution)**
