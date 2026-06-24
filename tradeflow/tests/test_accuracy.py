"""
Basic accuracy tests for PerfectDocAI.
Run with: python -m pytest tests/test_accuracy.py
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.ocr import get_ocr_instance
from utils.nlp_extract import get_extractor
from utils.validator import get_validator


def test_ocr_initialization():
    """Test OCR engine initialization."""
    ocr = get_ocr_instance()
    assert ocr is not None
    assert hasattr(ocr, 'extract_text')


def test_extractor_initialization():
    """Test NLP extractor initialization."""
    extractor = get_extractor()
    assert extractor is not None
    assert hasattr(extractor, 'extract_fields')


def test_validator_initialization():
    """Test validator initialization."""
    validator = get_validator()
    assert validator is not None
    assert hasattr(validator, 'validate')


def test_field_extraction_patterns():
    """Test regex patterns for field extraction."""
    extractor = get_extractor()
    
    # Test invoice number extraction
    test_text = "Invoice Number: INV-2024-001"
    result = extractor._extract_with_patterns(test_text, 'invoice_number')
    assert result is not None
    assert 'INV' in result or '2024' in result


def test_validation_logic():
    """Test validation logic."""
    validator = get_validator()
    
    # Test field validation
    is_valid, conf, msg = validator.validate_field('invoice_number', 'INV-001', 'string')
    assert is_valid is True
    assert conf > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
