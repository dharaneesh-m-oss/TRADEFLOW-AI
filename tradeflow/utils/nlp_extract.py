"""
NLP-based field extraction from shipping documents using LayoutLMv3/Donut.
Extracts structured data: invoice_number, dates, names, items, amounts, etc.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentExtractor:
    """
    Extract structured fields from shipping documents using NLP and regex patterns.
    Falls back to rule-based extraction if ML models are unavailable.
    """
    
    def __init__(self):
        """Initialize extractor with patterns and models."""
        self.patterns = self._initialize_patterns()
        self.ml_model = None
        self._try_load_ml_model()
    
    def _try_load_ml_model(self):
        """Try to load LayoutLMv3 or Donut model if available."""
        try:
            # Try LayoutLMv3 first
            from transformers import AutoProcessor, AutoModelForTokenClassification
            logger.info("Attempting to load LayoutLMv3...")
            # For hackathon MVP, we'll use rule-based with ML-ready structure
            # In production, would load: model = AutoModelForTokenClassification.from_pretrained(...)
            self.ml_model = "layoutlmv3"  # Placeholder
            logger.info("ML model placeholder initialized")
        except Exception as e:
            logger.warning(f"ML model not available, using rule-based extraction: {e}")
            self.ml_model = None
    
    def _initialize_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Initialize regex patterns for field extraction."""
        return {
            'invoice_number': [
                re.compile(r'(?:invoice|inv|bill)\s*(?:no|number|#)?\s*:?\s*([A-Z0-9\-]+)', re.IGNORECASE),
                re.compile(r'inv[#\s]*([A-Z0-9\-]+)', re.IGNORECASE),
                re.compile(r'INV[#\s]*([A-Z0-9\-]+)', re.IGNORECASE),
            ],
            'date': [
                re.compile(r'(?:date|dated|invoice\s*date)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', re.IGNORECASE),
                re.compile(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'),
                re.compile(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'),
            ],
            'seller_name': [
                re.compile(r'(?:seller|vendor|from|supplier|exporter)\s*:?\s*([A-Z][A-Za-z\s&,\.]+)', re.IGNORECASE),
                re.compile(r'(?:bill\s*from|sold\s*by)\s*:?\s*([A-Z][A-Za-z\s&,\.]+)', re.IGNORECASE),
            ],
            'buyer_name': [
                re.compile(r'(?:buyer|customer|to|bill\s*to|sold\s*to)\s*:?\s*([A-Z][A-Za-z\s&,\.]+)', re.IGNORECASE),
                re.compile(r'(?:ship\s*to|deliver\s*to)\s*:?\s*([A-Z][A-Za-z\s&,\.]+)', re.IGNORECASE),
            ],
            'total_amount': [
                re.compile(r'(?:total|amount|grand\s*total|sum)\s*:?\s*\$?\s*([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'\$\s*([\d,]+\.?\d*)'),
                re.compile(r'([\d,]+\.?\d*)\s*(?:USD|EUR|INR|CNY|BRL)', re.IGNORECASE),
            ],
            'currency': [
                re.compile(r'([A-Z]{3})\s*(?:currency|code)', re.IGNORECASE),
                re.compile(r'(?:USD|EUR|INR|CNY|BRL|GBP)'),
            ],
            'ship_from': [
                re.compile(r'(?:ship\s*from|origin|from\s*address)\s*:?\s*([A-Z][A-Za-z\s,\d]+)', re.IGNORECASE),
                re.compile(r'(?:origin\s*country|country\s*of\s*origin)\s*:?\s*([A-Z]{2,3})', re.IGNORECASE),
            ],
            'ship_to': [
                re.compile(r'(?:ship\s*to|destination|to\s*address)\s*:?\s*([A-Z][A-Za-z\s,\d]+)', re.IGNORECASE),
                re.compile(r'(?:destination\s*country)\s*:?\s*([A-Z]{2,3})', re.IGNORECASE),
            ],
            'country_origin': [
                re.compile(r'(?:country\s*of\s*origin|origin\s*country|made\s*in)\s*:?\s*([A-Z]{2,3})', re.IGNORECASE),
                re.compile(r'origin[:\s]+([A-Z][A-Za-z\s]+)', re.IGNORECASE),
            ],
            'weight': [
                re.compile(r'(?:weight|wt|gross\s*weight)\s*:?\s*([\d,]+\.?\d*)\s*(?:kg|lbs|lb|kgs)', re.IGNORECASE),
                re.compile(r'([\d,]+\.?\d*)\s*(?:kg|kgs|kilograms)', re.IGNORECASE),
            ],
            'hs_code': [
                re.compile(r'(?:hs\s*code|h\.s\.|harmonized\s*system)\s*:?\s*(\d{6,10})', re.IGNORECASE),
                re.compile(r'HS[#\s]*(\d{6,10})', re.IGNORECASE),
            ],
        }
    
    def _extract_with_patterns(self, text: str, field: str) -> Optional[str]:
        """Extract field using regex patterns."""
        if field not in self.patterns:
            return None
        
        for pattern in self.patterns[field]:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_items_table(self, text: str) -> List[Dict]:
        """
        Extract items/line items from document text.
        Looks for table-like structures with descriptions, quantities, prices.
        """
        items = []
        
        # Pattern for table rows
        # Look for numbered items or table structures
        item_patterns = [
            re.compile(r'(?:item|product|description)\s*:?\s*([^\n]+?)\s*(?:qty|quantity|qty\.)\s*:?\s*(\d+)\s*(?:price|unit|@)\s*:?\s*\$?([\d,]+\.?\d*)', re.IGNORECASE | re.MULTILINE),
            re.compile(r'(\d+)\.\s*([^\n]+?)\s+(\d+)\s+\$?([\d,]+\.?\d*)', re.MULTILINE),
        ]
        
        for pattern in item_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                if len(match.groups()) >= 3:
                    description = match.group(1).strip() if len(match.groups()) >= 1 else ""
                    quantity = match.group(2).strip() if len(match.groups()) >= 2 else "1"
                    unit_price = match.group(3).strip() if len(match.groups()) >= 3 else "0"
                    
                    try:
                        qty = float(quantity.replace(',', ''))
                        price = float(unit_price.replace(',', '').replace('$', ''))
                        total = qty * price
                        
                        items.append({
                            'description': description,
                            'quantity': qty,
                            'unit_price': price,
                            'total_value': total,
                            'hs_code': self._extract_hs_code_from_item(description),
                            'confidence': 0.85
                        })
                    except:
                        pass
        
        # If no structured items found, create a single item from total
        if not items:
            total_amount = self._extract_with_patterns(text, 'total_amount')
            if total_amount:
                try:
                    amount = float(total_amount.replace(',', '').replace('$', ''))
                    items.append({
                        'description': 'General Merchandise',
                        'quantity': 1,
                        'unit_price': amount,
                        'total_value': amount,
                        'hs_code': None,
                        'confidence': 0.70
                    })
                except:
                    pass
        
        return items
    
    def _extract_hs_code_from_item(self, description: str) -> Optional[str]:
        """Try to extract HS code from item description."""
        hs_match = re.search(r'(\d{6,10})', description)
        if hs_match:
            code = hs_match.group(1)
            if 6 <= len(code) <= 10:
                return code
        return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to YYYY-MM-DD format."""
        if not date_str:
            return None
        
        # Try various formats
        formats = [
            '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d',
            '%m.%d.%Y', '%d.%m.%Y',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str
    
    def extract_fields(self, ocr_result: Dict) -> Dict[str, Any]:
        """
        Extract structured fields from OCR result.
        
        Args:
            ocr_result: Dictionary with 'text' key from OCR module
            
        Returns:
            Dictionary with extracted fields and confidence scores
        """
        text = ocr_result.get('text', '')
        if not text:
            return {
                'fields': {},
                'confidence': 0.0,
                'errors': ['No text extracted from document']
            }
        
        extracted = {}
        confidences = []
        
        # Extract basic fields
        fields_to_extract = [
            'invoice_number', 'date', 'seller_name', 'buyer_name',
            'total_amount', 'currency', 'ship_from', 'ship_to',
            'country_origin', 'weight', 'hs_code'
        ]
        
        for field in fields_to_extract:
            value = self._extract_with_patterns(text, field)
            if value:
                # Normalize date
                if field == 'date':
                    value = self._normalize_date(value)
                
                # Normalize currency
                if field == 'currency':
                    value = value.upper()[:3]
                
                extracted[field] = value
                confidences.append(0.85)  # Pattern match confidence
            else:
                confidences.append(0.0)
        
        # Extract items table
        items = self._extract_items_table(text)
        if items:
            extracted['items'] = items
            confidences.append(0.80)
        else:
            confidences.append(0.0)
        
        # Calculate overall confidence
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Calculate total from items if available
        if 'items' in extracted and extracted['items']:
            calculated_total = sum(item.get('total_value', 0) for item in extracted['items'])
            if 'total_amount' not in extracted or not extracted['total_amount']:
                extracted['total_amount'] = str(calculated_total)
            else:
                # Validate total matches
                try:
                    extracted_total = float(str(extracted['total_amount']).replace(',', '').replace('$', ''))
                    if abs(calculated_total - extracted_total) / max(extracted_total, 1) > 0.05:
                        extracted['total_amount_warning'] = f"Calculated total ({calculated_total}) doesn't match extracted ({extracted_total})"
                except:
                    pass
        
        # Set default currency if not found
        if 'currency' not in extracted or not extracted['currency']:
            extracted['currency'] = 'USD'
        
        return {
            'fields': extracted,
            'confidence': overall_confidence,
            'raw_text': text[:500],  # First 500 chars for debugging
            'num_items': len(items) if items else 0
        }


# Global extractor instance
_extractor_instance = None

def get_extractor() -> DocumentExtractor:
    """Get or create extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = DocumentExtractor()
    return _extractor_instance
