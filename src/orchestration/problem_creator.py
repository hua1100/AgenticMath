"""
Problem Creator for creating Problem entities from OCR results.

This module provides functionality to:
1. Create Problem entity from OCR-extracted text
2. Identify domain using keyword matching (placeholder for ML-based approach)
3. Set baseline competencies and difficulty (placeholder for advanced analysis)
4. Link Problem to UploadedImage
5. Store in database
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from src.models.problem import (
    Problem,
    MathDomain,
    ProblemSource,
    SourceType,
)
from src.models.uploaded_image import UploadedImage
from src.storage.database import get_db


class ProblemCreator:
    """
    Creates Problem entities from OCR results.

    This is a basic implementation that uses keyword matching for domain identification.
    In Phase 2 (P1), this will be enhanced with ML-based classification and proper
    competency extraction.
    """

    # Domain keyword mapping (繁體中文)
    DOMAIN_KEYWORDS = {
        MathDomain.ALGEBRA: [
            "方程式",
            "等式",
            "不等式",
            "解",
            "變數",
            "代數",
            "x",
            "y",
            "一元",
            "二元",
            "聯立",
            "多項式",
            "因式分解",
        ],
        MathDomain.GEOMETRY: [
            "三角形",
            "圓",
            "矩形",
            "正方形",
            "角度",
            "面積",
            "體積",
            "幾何",
            "平行",
            "垂直",
            "對稱",
            "相似",
            "全等",
            "畢氏定理",
            "勾股定理",
            "直角",
            "邊長",
            "周長",
        ],
        MathDomain.CALCULUS: [
            "微分",
            "積分",
            "導數",
            "導函數",
            "極限",
            "微積分",
            "連續",
            "斜率",
            "切線",
            "面積",
            "曲線",
        ],
        MathDomain.PROBABILITY: [
            "機率",
            "統計",
            "期望值",
            "隨機",
            "分布",
            "抽樣",
            "平均",
            "標準差",
            "變異數",
            "事件",
            "獨立",
        ],
        MathDomain.NUMBER_THEORY: [
            "質數",
            "因數",
            "倍數",
            "整除",
            "最大公因數",
            "最小公倍數",
            "餘數",
            "模",
            "同餘",
            "互質",
        ],
        MathDomain.COMBINATORICS: [
            "排列",
            "組合",
            "計數",
            "配對",
            "分組",
            "選擇",
            "安排",
            "方法數",
        ],
    }

    # Default baseline competencies by domain (placeholder)
    DEFAULT_COMPETENCIES = {
        MathDomain.ALGEBRA: ["algebraic_manipulation", "equation_solving"],
        MathDomain.GEOMETRY: ["geometric_reasoning", "spatial_visualization"],
        MathDomain.CALCULUS: ["differentiation", "integration"],
        MathDomain.PROBABILITY: ["probability_calculation", "statistical_reasoning"],
        MathDomain.NUMBER_THEORY: ["number_properties", "divisibility"],
        MathDomain.COMBINATORICS: ["counting_principles", "combinatorial_reasoning"],
        MathDomain.OTHER: ["mathematical_reasoning"],
    }

    def __init__(self):
        """Initialize ProblemCreator."""
        pass

    def create_from_ocr(
        self,
        ocr_result: Dict[str, Any],
        image_id: UUID,
        db: Optional[Session] = None,
    ) -> Problem:
        """
        Create a Problem entity from OCR result.

        Args:
            ocr_result: OCR result dictionary from OCRPipeline.process()
            image_id: UUID of the UploadedImage
            db: Optional database session (if None, creates one)

        Returns:
            Problem: Created Problem entity with ID

        Raises:
            ValueError: If OCR result is invalid or image not found
        """
        # Validate OCR result
        if not ocr_result.get("success"):
            raise ValueError(
                f"Cannot create problem from failed OCR result: "
                f"{ocr_result.get('error_code', 'UNKNOWN_ERROR')}"
            )

        extracted_text = ocr_result.get("extracted_text", "").strip()
        if not extracted_text:
            raise ValueError("Cannot create problem from empty extracted text")

        # Manage database session
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            # Verify UploadedImage exists
            uploaded_image = (
                db.query(UploadedImage).filter_by(id=image_id).first()
            )
            if not uploaded_image:
                raise ValueError(f"UploadedImage not found: {image_id}")

            # Identify domain using keyword matching
            domain = self._identify_domain(extracted_text)

            # Get baseline competencies for domain
            competencies = self.DEFAULT_COMPETENCIES.get(domain, ["mathematical_reasoning"])

            # Estimate baseline difficulty (placeholder - always returns 3 for now)
            baseline_difficulty = self._estimate_difficulty(
                extracted_text, ocr_result
            )

            # Prepare extra metadata
            extra_metadata = {
                "ocr_confidence": ocr_result.get("confidence_score"),
                "contains_diagram": ocr_result.get("contains_diagram", False),
                "diagram_description": ocr_result.get("diagram_description"),
            }

            # Add diagram analysis if available
            if ocr_result.get("diagram_analysis"):
                extra_metadata["diagram_analysis"] = ocr_result["diagram_analysis"]

            # Create Problem entity
            problem = Problem(
                content=extracted_text,
                domain=domain,
                competencies=competencies,
                baseline_difficulty=baseline_difficulty,
                source=ProblemSource.ORIGINAL,
                source_type=SourceType.OCR,
                parent_id=None,  # Original problems have no parent
                uploaded_image_id=image_id,
                extra_metadata=extra_metadata,
            )

            # Save to database
            db.add(problem)

            # Update UploadedImage with problem_id
            uploaded_image.problem_id = problem.id

            # Commit if we created the session
            if should_close_db:
                db.commit()
                # Refresh to get the committed ID
                db.refresh(problem)

            return problem

        finally:
            if should_close_db:
                db.close()

    def _identify_domain(self, text: str) -> MathDomain:
        """
        Identify mathematical domain using keyword matching.

        This is a placeholder implementation. In Phase 2 (P1), this will be
        replaced with ML-based classification.

        Args:
            text: Problem text

        Returns:
            MathDomain: Identified domain (defaults to OTHER if unclear)
        """
        text_lower = text.lower()

        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            domain_scores[domain] = score

        # Find domain with highest score
        max_score = max(domain_scores.values())

        if max_score == 0:
            # No keywords matched - default to OTHER
            return MathDomain.OTHER

        # Return domain with highest score
        # If tie, prefer geometry > algebra > other domains
        preference_order = [
            MathDomain.GEOMETRY,
            MathDomain.ALGEBRA,
            MathDomain.CALCULUS,
            MathDomain.PROBABILITY,
            MathDomain.NUMBER_THEORY,
            MathDomain.COMBINATORICS,
            MathDomain.OTHER,
        ]

        for domain in preference_order:
            if domain_scores[domain] == max_score:
                return domain

        return MathDomain.OTHER

    def _estimate_difficulty(
        self, text: str, ocr_result: Dict[str, Any]
    ) -> int:
        """
        Estimate baseline difficulty level.

        This is a placeholder implementation. In Phase 2 (P1), this will be
        enhanced with proper difficulty estimation.

        Args:
            text: Problem text
            ocr_result: Full OCR result

        Returns:
            int: Difficulty level 1-5 (currently always returns 3)
        """
        # Placeholder: Always return medium difficulty
        # In P1, this will analyze:
        # - Text complexity
        # - Diagram complexity
        # - Number of unknowns
        # - Required competencies
        return 3


# Convenience function
def create_problem_from_ocr(
    ocr_result: Dict[str, Any],
    image_id: UUID,
    db: Optional[Session] = None,
) -> Problem:
    """
    Create a Problem from OCR result (convenience function).

    Args:
        ocr_result: OCR result dictionary
        image_id: UUID of the UploadedImage
        db: Optional database session

    Returns:
        Problem: Created Problem entity

    Example:
        >>> from src.ocr import process_image
        >>> from src.orchestration import create_problem_from_ocr
        >>>
        >>> # Process image with OCR
        >>> ocr_result = process_image(image_id, file_path)
        >>>
        >>> # Create problem from OCR result
        >>> if ocr_result["success"]:
        >>>     problem = create_problem_from_ocr(ocr_result, image_id)
        >>>     print(f"Created problem: {problem.id}")
    """
    creator = ProblemCreator()
    return creator.create_from_ocr(ocr_result, image_id, db)
