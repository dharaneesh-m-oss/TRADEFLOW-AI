"""
One-click demo script for PerfectDocAI.
Run this to test the system with synthetic data.
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.nlp_extract import get_extractor
from utils.validator import get_validator
from utils.form_generator import get_form_generator
import tempfile
import os


def create_demo_document():
    """Create a synthetic document text for demo."""
    return """
    INVOICE
    
    Invoice Number: INV-2024-001
    Date: 2024-01-15
    
    Seller: ABC Export Company Ltd.
    123 Export Street, Mumbai, India
    
    Buyer: XYZ Import Inc.
    456 Import Avenue, New York, USA
    
    Ship From: Mumbai, India
    Ship To: New York, USA
    Country of Origin: India
    
    Items:
    1. Electronic Components - HS Code: 85414000
       Quantity: 100
       Unit Price: $25.00
       Total: $2,500.00
    
    2. Machinery Parts - HS Code: 84798990
       Quantity: 50
       Unit Price: $150.00
       Total: $7,500.00
    
    Total Amount: $10,000.00
    Currency: USD
    Weight: 500 kg
    """


def run_demo():
    """Run a quick demo of the system."""
    print("🚀 PerfectDocAI Demo Script")
    print("=" * 50)
    
    # Create synthetic OCR result
    demo_text = create_demo_document()
    ocr_result = {
        'text': demo_text,
        'confidence': 0.95,
        'num_pages': 1,
        'num_text_blocks': 20
    }
    
    print("\n1️⃣ OCR Result (simulated)")
    print(f"   Text extracted: {len(demo_text)} characters")
    print(f"   Confidence: {ocr_result['confidence']:.1%}")
    
    # Extract fields
    print("\n2️⃣ NLP Field Extraction")
    extractor = get_extractor()
    extracted_data = extractor.extract_fields(ocr_result)
    
    fields = extracted_data.get('fields', {})
    print(f"   Fields extracted: {len(fields)}")
    print(f"   Overall confidence: {extracted_data.get('confidence', 0):.1%}")
    
    for key, value in fields.items():
        if key != 'items':
            print(f"   - {key}: {value}")
    
    if 'items' in fields:
        print(f"   - Items: {len(fields['items'])}")
        for i, item in enumerate(fields['items'], 1):
            print(f"     Item {i}: {item.get('description', 'N/A')} - ${item.get('total_value', 0):.2f}")
    
    # Validate
    print("\n3️⃣ Validation")
    validator = get_validator()
    validation_results = validator.validate(extracted_data, country="USA")
    
    print(f"   Valid: {validation_results.get('valid', False)}")
    print(f"   Confidence: {validation_results.get('confidence', 0):.1%}")
    print(f"   Auto-fill safe: {validation_results.get('auto_fill_safe', False)}")
    print(f"   Errors: {len(validation_results.get('errors', []))}")
    print(f"   Warnings: {len(validation_results.get('warnings', []))}")
    
    # Generate form
    print("\n4️⃣ Form Generation")
    generator = get_form_generator()
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "demo_customs_form_USA.pdf"
    
    try:
        generator.generate_form(extracted_data, "USA", str(output_path))
        print(f"   ✅ Form generated: {output_path}")
        print(f"   File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Demo complete!")
    print("\nNext steps:")
    print("1. Run: streamlit run app.py")
    print("2. Upload a real document")
    print("3. Process and generate forms")


if __name__ == "__main__":
    run_demo()
