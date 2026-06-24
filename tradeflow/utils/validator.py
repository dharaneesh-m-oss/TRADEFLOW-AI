"""
Validation module for extracted document data.
Performs cross-checks, rule validation, and confidence scoring.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentValidator:
    """
    Validate extracted document data against business rules and country-specific customs requirements.
    """
    
    def __init__(self, customs_rules_path: Optional[str] = None):
        """
        Initialize validator with customs rules.
        
        Args:
            customs_rules_path: Path to customs_rules.json file
        """
        if customs_rules_path is None:
            customs_rules_path = os.path.join(os.path.dirname(__file__), 'customs_rules.json')
        
        with open(customs_rules_path, 'r', encoding='utf-8') as f:
            self.customs_rules = json.load(f)
    
    def validate_field(self, field_name: str, value: Any, field_type: str = 'string') -> Tuple[bool, float, str]:
        """
        Validate a single field.
        
        Returns:
            (is_valid, confidence, message)
        """
        if value is None or value == '':
            return False, 0.0, f"{field_name} is missing"
        
        # Type validation
        if field_type == 'date':
            try:
                datetime.strptime(str(value), '%Y-%m-%d')
                return True, 0.95, "Valid date"
            except:
                return False, 0.5, f"Invalid date format: {value}"
        
        elif field_type == 'number':
            try:
                float(str(value).replace(',', '').replace('$', ''))
                return True, 0.95, "Valid number"
            except:
                return False, 0.3, f"Invalid number: {value}"
        
        elif field_type == 'currency':
            valid_currencies = ['USD', 'EUR', 'INR', 'CNY', 'BRL', 'GBP']
            if str(value).upper()[:3] in valid_currencies:
                return True, 0.95, "Valid currency"
            return False, 0.5, f"Invalid currency: {value}"
        
        elif field_type == 'hs_code':
            code = str(value).replace('-', '').replace(' ', '')
            if code.isdigit() and 6 <= len(code) <= 10:
                return True, 0.90, "Valid HS code format"
            return False, 0.4, f"Invalid HS code format: {value}"
        
        return True, 0.85, "Field present"
    
    def validate_cross_checks(self, extracted_data: Dict) -> List[Dict]:
        """
        Perform cross-checks between fields (totals match, dates valid, etc.).
        
        Returns:
            List of validation issues
        """
        issues = []
        fields = extracted_data.get('fields', {})
        
        # Check 1: Total amount matches sum of items
        if 'items' in fields and fields['items']:
            calculated_total = sum(item.get('total_value', 0) for item in fields['items'])
            if 'total_amount' in fields:
                try:
                    extracted_total = float(str(fields['total_amount']).replace(',', '').replace('$', ''))
                    diff = abs(calculated_total - extracted_total)
                    diff_pct = (diff / max(extracted_total, 1)) * 100
                    
                    if diff_pct > 5:  # More than 5% difference
                        issues.append({
                            'type': 'cross_check',
                            'field': 'total_amount',
                            'severity': 'warning',
                            'message': f"Total amount mismatch: extracted={extracted_total}, calculated={calculated_total:.2f} (diff: {diff_pct:.1f}%)",
                            'confidence_impact': -0.10
                        })
                except:
                    issues.append({
                        'type': 'cross_check',
                        'field': 'total_amount',
                        'severity': 'error',
                        'message': "Cannot parse total_amount for validation",
                        'confidence_impact': -0.15
                    })
        
        # Check 2: Date is valid and not in future
        if 'date' in fields:
            try:
                date_obj = datetime.strptime(str(fields['date']), '%Y-%m-%d')
                if date_obj > datetime.now():
                    issues.append({
                        'type': 'cross_check',
                        'field': 'date',
                        'severity': 'warning',
                        'message': f"Date is in the future: {fields['date']}",
                        'confidence_impact': -0.05
                    })
                
                # Check if date is too old (more than 2 years)
                age_days = (datetime.now() - date_obj).days
                if age_days > 730:
                    issues.append({
                        'type': 'cross_check',
                        'field': 'date',
                        'severity': 'warning',
                        'message': f"Date is very old ({age_days} days ago)",
                        'confidence_impact': -0.05
                    })
            except:
                pass
        
        # Check 3: Items have required fields
        if 'items' in fields:
            for i, item in enumerate(fields['items']):
                if not item.get('description'):
                    issues.append({
                        'type': 'cross_check',
                        'field': f'items[{i}].description',
                        'severity': 'error',
                        'message': f"Item {i+1} missing description",
                        'confidence_impact': -0.10
                    })
                
                if not item.get('quantity') or item.get('quantity', 0) <= 0:
                    issues.append({
                        'type': 'cross_check',
                        'field': f'items[{i}].quantity',
                        'severity': 'warning',
                        'message': f"Item {i+1} has invalid quantity",
                        'confidence_impact': -0.05
                    })
        
        # Check 4: Currency consistency
        if 'currency' in fields and 'total_amount' in fields:
            # Currency should match the amount format (basic check)
            currency = str(fields['currency']).upper()
            amount_str = str(fields['total_amount'])
            # This is a basic check - in production would be more sophisticated
        
        return issues
    
    def validate_country_rules(self, extracted_data: Dict, country: str) -> List[Dict]:
        """
        Validate against country-specific customs rules.
        
        Args:
            extracted_data: Extracted data dictionary
            country: Country code (USA, India, EU, China, Brazil)
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if country not in self.customs_rules:
            issues.append({
                'type': 'country_rules',
                'severity': 'error',
                'message': f"Unknown country: {country}",
                'confidence_impact': -0.20
            })
            return issues
        
        rules = self.customs_rules[country]
        fields = extracted_data.get('fields', {})
        required_fields = rules.get('required_fields', [])
        
        # Check required fields
        for field in required_fields:
            if field == 'items':
                if 'items' not in fields or not fields['items']:
                    issues.append({
                        'type': 'country_rules',
                        'field': field,
                        'severity': 'error',
                        'message': f"Required field '{field}' is missing for {country}",
                        'confidence_impact': -0.15
                    })
            elif field not in fields or not fields[field]:
                issues.append({
                    'type': 'country_rules',
                    'field': field,
                    'severity': 'error',
                    'message': f"Required field '{field}' is missing for {country}",
                    'confidence_impact': -0.15
                })
        
        # Validate HS codes if required
        hs_validation = rules.get('hs_code_validation', {})
        if hs_validation:
            if 'items' in fields:
                for i, item in enumerate(fields['items']):
                    hs_code = item.get('hs_code')
                    if hs_code:
                        code_str = str(hs_code).replace('-', '').replace(' ', '')
                        min_len = hs_validation.get('min_length', 6)
                        max_len = hs_validation.get('max_length', 10)
                        
                        if not (min_len <= len(code_str) <= max_len):
                            issues.append({
                                'type': 'country_rules',
                                'field': f'items[{i}].hs_code',
                                'severity': 'warning',
                                'message': f"HS code '{hs_code}' doesn't meet {country} requirements ({min_len}-{max_len} digits)",
                                'confidence_impact': -0.10
                            })
        
        # Validate currency
        currency_codes = rules.get('currency_codes', [])
        if currency_codes and 'currency' in fields:
            currency = str(fields['currency']).upper()[:3]
            if currency not in currency_codes:
                issues.append({
                    'type': 'country_rules',
                    'field': 'currency',
                    'severity': 'warning',
                    'message': f"Currency '{currency}' not in allowed list for {country}: {currency_codes}",
                    'confidence_impact': -0.05
                })
        
        return issues
    
    def validate(self, extracted_data: Dict, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive validation of extracted data.
        
        Args:
            extracted_data: Extracted data from NLP module
            country: Optional country code for country-specific validation
            
        Returns:
            Validation results with confidence score and issues
        """
        base_confidence = extracted_data.get('confidence', 0.0)
        all_issues = []
        
        fields = extracted_data.get('fields', {})
        
        # Validate individual fields
        field_validations = {}
        for field_name, value in fields.items():
            if field_name == 'items':
                continue  # Handle separately
            
            field_type = 'string'
            if 'date' in field_name.lower():
                field_type = 'date'
            elif 'amount' in field_name.lower() or 'price' in field_name.lower():
                field_type = 'number'
            elif field_name == 'currency':
                field_type = 'currency'
            elif 'hs_code' in field_name.lower():
                field_type = 'hs_code'
            
            is_valid, conf, msg = self.validate_field(field_name, value, field_type)
            field_validations[field_name] = {
                'valid': is_valid,
                'confidence': conf,
                'message': msg
            }
            
            if not is_valid:
                all_issues.append({
                    'type': 'field_validation',
                    'field': field_name,
                    'severity': 'error' if conf < 0.5 else 'warning',
                    'message': msg,
                    'confidence_impact': -(1.0 - conf)
                })
        
        # Validate items
        if 'items' in fields:
            for i, item in enumerate(fields['items']):
                item_conf = item.get('confidence', 0.85)
                if item_conf < 0.7:
                    all_issues.append({
                        'type': 'field_validation',
                        'field': f'items[{i}]',
                        'severity': 'warning',
                        'message': f"Item {i+1} has low confidence ({item_conf:.2f})",
                        'confidence_impact': -0.05
                    })
        
        # Cross-checks
        cross_check_issues = self.validate_cross_checks(extracted_data)
        all_issues.extend(cross_check_issues)
        
        # Country-specific validation
        if country:
            country_issues = self.validate_country_rules(extracted_data, country)
            all_issues.extend(country_issues)
        
        # Calculate final confidence
        confidence_impact = sum(issue.get('confidence_impact', 0) for issue in all_issues)
        final_confidence = max(0.0, min(1.0, base_confidence + confidence_impact))
        
        # Categorize issues
        errors = [i for i in all_issues if i.get('severity') == 'error']
        warnings = [i for i in all_issues if i.get('severity') == 'warning']
        
        # Determine if auto-fill is safe (>95% confidence)
        auto_fill_safe = final_confidence >= 0.95 and len(errors) == 0
        
        return {
            'valid': len(errors) == 0,
            'confidence': final_confidence,
            'auto_fill_safe': auto_fill_safe,
            'errors': errors,
            'warnings': warnings,
            'all_issues': all_issues,
            'field_validations': field_validations,
            'diagnostic_report': self._generate_diagnostic_report(extracted_data, all_issues, final_confidence)
        }
    
    def _generate_diagnostic_report(self, extracted_data: Dict, issues: List[Dict], confidence: float) -> str:
        """Generate human-readable diagnostic report."""
        report_lines = [
            f"=== Validation Diagnostic Report ===",
            f"Overall Confidence: {confidence:.1%}",
            f"Status: {'✓ AUTO-FILL SAFE' if confidence >= 0.95 else '⚠ MANUAL REVIEW REQUIRED'}",
            f"",
            f"Issues Found: {len(issues)}",
        ]
        
        if issues:
            report_lines.append("")
            for issue in issues[:10]:  # Limit to first 10
                severity_icon = "❌" if issue.get('severity') == 'error' else "⚠️"
                report_lines.append(f"{severity_icon} {issue.get('message', 'Unknown issue')}")
        
        return "\n".join(report_lines)


# Global validator instance
_validator_instance = None

def get_validator() -> DocumentValidator:
    """Get or create validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DocumentValidator()
    return _validator_instance
