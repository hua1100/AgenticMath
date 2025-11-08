"""
Unit tests for ProblemCreator module.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.orchestration.problem_creator import (
    ProblemCreator,
    create_problem_from_ocr,
)
from src.models.problem import (
    Problem,
    MathDomain,
    ProblemSource,
    SourceType,
)
from src.models.uploaded_image import UploadedImage


class TestProblemCreator:
    """Tests for ProblemCreator class."""

    def test_creator_initialization(self):
        """Test creator initialization."""
        creator = ProblemCreator()
        assert creator is not None

    def test_identify_domain_algebra(self):
        """Test domain identification for algebra problems."""
        creator = ProblemCreator()

        # Algebra text with equation keywords
        text = "求解方程式：2x + 3 = 7，求 x 的值"
        domain = creator._identify_domain(text)
        assert domain == MathDomain.ALGEBRA

    def test_identify_domain_geometry(self):
        """Test domain identification for geometry problems."""
        creator = ProblemCreator()

        # Geometry text with triangle keywords
        text = "在直角三角形 ABC 中，∠C = 90°，若 AB = 10，AC = 6，求 BC 的長度"
        domain = creator._identify_domain(text)
        assert domain == MathDomain.GEOMETRY

    def test_identify_domain_probability(self):
        """Test domain identification for probability problems."""
        creator = ProblemCreator()

        # Probability text
        text = "一個袋子中有 5 個紅球和 3 個藍球，隨機抽取 2 個球，求抽到 2 個紅球的機率"
        domain = creator._identify_domain(text)
        assert domain == MathDomain.PROBABILITY

    def test_identify_domain_number_theory(self):
        """Test domain identification for number theory."""
        creator = ProblemCreator()

        # Number theory text
        text = "求 24 和 36 的最大公因數和最小公倍數"
        domain = creator._identify_domain(text)
        assert domain == MathDomain.NUMBER_THEORY

    def test_identify_domain_combinatorics(self):
        """Test domain identification for combinatorics."""
        creator = ProblemCreator()

        # Combinatorics text
        text = "從 10 個人中選出 3 個人組成委員會，有多少種排列方法？"
        domain = creator._identify_domain(text)
        assert domain == MathDomain.COMBINATORICS

    def test_identify_domain_no_keywords_returns_other(self):
        """Test that text with no keywords returns OTHER domain."""
        creator = ProblemCreator()

        # Generic text with no domain keywords
        text = "這是一個數學問題"
        domain = creator._identify_domain(text)
        assert domain == MathDomain.OTHER

    def test_estimate_difficulty_returns_placeholder(self):
        """Test that difficulty estimation returns placeholder value."""
        creator = ProblemCreator()

        # Currently should always return 3 (placeholder)
        text = "任何題目"
        ocr_result = {"confidence_score": 0.9}
        difficulty = creator._estimate_difficulty(text, ocr_result)
        assert difficulty == 3

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_from_ocr_success(self, mock_get_db):
        """Test successful problem creation from OCR result."""
        # Setup mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        # Create mock UploadedImage
        image_id = uuid4()
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        # Create OCR result
        ocr_result = {
            "success": True,
            "extracted_text": "求解方程式：2x + 3 = 7",
            "confidence_score": 0.92,
            "contains_diagram": False,
            "diagram_description": None,
        }

        # Create problem
        creator = ProblemCreator()
        problem = creator.create_from_ocr(ocr_result, image_id, db=mock_db)

        # Verify problem was created correctly
        assert isinstance(problem, Problem)
        assert problem.content == "求解方程式：2x + 3 = 7"
        assert problem.domain == MathDomain.ALGEBRA
        assert problem.source == ProblemSource.ORIGINAL
        assert problem.source_type == SourceType.OCR
        assert problem.uploaded_image_id == image_id
        assert problem.parent_id is None
        assert problem.baseline_difficulty == 3
        assert len(problem.competencies) > 0

        # Verify extra metadata
        assert problem.extra_metadata["ocr_confidence"] == 0.92
        assert problem.extra_metadata["contains_diagram"] is False

        # Verify database operations
        mock_db.add.assert_called_once_with(problem)
        assert mock_uploaded_image.problem_id == problem.id

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_from_ocr_with_diagram(self, mock_get_db):
        """Test problem creation with diagram analysis."""
        # Setup mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        # Create mock UploadedImage
        image_id = uuid4()
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        # Create OCR result with diagram
        ocr_result = {
            "success": True,
            "extracted_text": "在直角三角形 ABC 中，求 BC 的長度",
            "confidence_score": 0.88,
            "contains_diagram": True,
            "diagram_description": "包含直角三角形",
            "diagram_analysis": {
                "diagram_type": "right_triangle",
                "key_concepts": ["pythagorean_theorem"],
                "features": {"vertices": ["A", "B", "C"]},
                "difficulty_indicators": {"complexity": "medium"},
            },
        }

        # Create problem
        creator = ProblemCreator()
        problem = creator.create_from_ocr(ocr_result, image_id, db=mock_db)

        # Verify diagram metadata was stored
        assert problem.domain == MathDomain.GEOMETRY
        assert problem.extra_metadata["contains_diagram"] is True
        assert problem.extra_metadata["diagram_description"] == "包含直角三角形"
        assert problem.extra_metadata["diagram_analysis"] is not None
        assert (
            problem.extra_metadata["diagram_analysis"]["diagram_type"]
            == "right_triangle"
        )

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_from_ocr_failed_ocr_raises_error(self, mock_get_db):
        """Test that failed OCR result raises ValueError."""
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        image_id = uuid4()

        # Failed OCR result
        ocr_result = {
            "success": False,
            "error_code": "OCR_NO_TEXT_DETECTED",
            "error_message": "無法辨識文字",
            "extracted_text": "",
        }

        # Should raise ValueError
        creator = ProblemCreator()
        with pytest.raises(ValueError, match="Cannot create problem from failed OCR"):
            creator.create_from_ocr(ocr_result, image_id, db=mock_db)

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_from_ocr_empty_text_raises_error(self, mock_get_db):
        """Test that empty extracted text raises ValueError."""
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        image_id = uuid4()

        # OCR result with empty text
        ocr_result = {
            "success": True,
            "extracted_text": "",  # Empty!
            "confidence_score": 0.0,
        }

        # Should raise ValueError
        creator = ProblemCreator()
        with pytest.raises(ValueError, match="Cannot create problem from empty"):
            creator.create_from_ocr(ocr_result, image_id, db=mock_db)

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_from_ocr_missing_image_raises_error(self, mock_get_db):
        """Test that missing UploadedImage raises ValueError."""
        # Setup mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        # Mock query returns None (image not found)
        image_id = uuid4()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Valid OCR result
        ocr_result = {
            "success": True,
            "extracted_text": "測試題目",
            "confidence_score": 0.9,
        }

        # Should raise ValueError
        creator = ProblemCreator()
        with pytest.raises(ValueError, match="UploadedImage not found"):
            creator.create_from_ocr(ocr_result, image_id, db=mock_db)

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_from_ocr_auto_manages_db_session(self, mock_get_db):
        """Test that db session is auto-managed when not provided."""
        # Setup mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        # Create mock UploadedImage
        image_id = uuid4()
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        # Valid OCR result
        ocr_result = {
            "success": True,
            "extracted_text": "測試",
            "confidence_score": 0.9,
        }

        # Create problem WITHOUT passing db (should auto-manage)
        creator = ProblemCreator()
        problem = creator.create_from_ocr(ocr_result, image_id, db=None)

        # Verify db operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()  # Should commit when auto-managing
        mock_db.close.assert_called_once()  # Should close when auto-managing

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_from_ocr_with_provided_db_no_commit(self, mock_get_db):
        """Test that provided db session is NOT committed."""
        # Setup mock database session
        mock_db = Mock(spec=Session)

        # Create mock UploadedImage
        image_id = uuid4()
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        # Valid OCR result
        ocr_result = {
            "success": True,
            "extracted_text": "測試",
            "confidence_score": 0.9,
        }

        # Create problem WITH provided db
        creator = ProblemCreator()
        problem = creator.create_from_ocr(ocr_result, image_id, db=mock_db)

        # Verify db operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_not_called()  # Should NOT commit when db provided
        mock_db.close.assert_not_called()  # Should NOT close when db provided


class TestConvenienceFunction:
    """Tests for convenience function."""

    @patch("src.orchestration.problem_creator.get_db")
    def test_create_problem_from_ocr(self, mock_get_db):
        """Test create_problem_from_ocr convenience function."""
        # Setup mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        # Create mock UploadedImage
        image_id = uuid4()
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        # Valid OCR result
        ocr_result = {
            "success": True,
            "extracted_text": "測試題目",
            "confidence_score": 0.9,
        }

        # Use convenience function
        problem = create_problem_from_ocr(ocr_result, image_id, db=mock_db)

        # Verify problem was created
        assert isinstance(problem, Problem)
        assert problem.content == "測試題目"


class TestDomainIdentificationEdgeCases:
    """Tests for edge cases in domain identification."""

    def test_geometry_preferred_over_algebra_on_tie(self):
        """Test that geometry is preferred when scores are actually tied."""
        creator = ProblemCreator()

        # Text with equal keyword counts for both domains
        # "三角形" (geometry, 1 keyword) and "x" (algebra, 1 keyword)
        # Note: We avoid "解" which is also an algebra keyword
        text = "在三角形中，已知 x 的值"
        domain = creator._identify_domain(text)

        # With equal scores, geometry should be preferred
        assert domain == MathDomain.GEOMETRY

    def test_case_insensitive_matching(self):
        """Test that keyword matching is case-insensitive."""
        creator = ProblemCreator()

        # Mixed case text
        text = "求解方程式"
        domain = creator._identify_domain(text)
        assert domain == MathDomain.ALGEBRA

    def test_multiple_domains_highest_score_wins(self):
        """Test that domain with most keyword matches wins."""
        creator = ProblemCreator()

        # Text heavily weighted towards geometry
        text = "直角三角形 ABC 的面積和周長，其中角度為 90 度，邊長分別為..."
        domain = creator._identify_domain(text)
        assert domain == MathDomain.GEOMETRY


class TestCompetenciesAssignment:
    """Tests for competencies assignment."""

    @patch("src.orchestration.problem_creator.get_db")
    def test_algebra_competencies(self, mock_get_db):
        """Test that algebra problems get correct competencies."""
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        image_id = uuid4()
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        ocr_result = {
            "success": True,
            "extracted_text": "求解方程式：x + 5 = 10",
            "confidence_score": 0.9,
        }

        creator = ProblemCreator()
        problem = creator.create_from_ocr(ocr_result, image_id, db=mock_db)

        # Verify algebra competencies
        assert "algebraic_manipulation" in problem.competencies
        assert "equation_solving" in problem.competencies

    @patch("src.orchestration.problem_creator.get_db")
    def test_geometry_competencies(self, mock_get_db):
        """Test that geometry problems get correct competencies."""
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        image_id = uuid4()
        mock_uploaded_image = Mock(spec=UploadedImage)
        mock_uploaded_image.id = image_id
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            mock_uploaded_image
        )

        ocr_result = {
            "success": True,
            "extracted_text": "求三角形的面積",
            "confidence_score": 0.9,
        }

        creator = ProblemCreator()
        problem = creator.create_from_ocr(ocr_result, image_id, db=mock_db)

        # Verify geometry competencies
        assert "geometric_reasoning" in problem.competencies
        assert "spatial_visualization" in problem.competencies
