"""
PDF Form Generator for customs forms.
Generates country-specific customs forms using ReportLab.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomsFormGenerator:
    """
    Generate country-specific customs forms as PDFs.
    """
    
    def __init__(self, customs_rules_path: Optional[str] = None):
        """
        Initialize form generator.
        
        Args:
            customs_rules_path: Path to customs_rules.json
        """
        if customs_rules_path is None:
            customs_rules_path = os.path.join(os.path.dirname(__file__), 'customs_rules.json')
        
        with open(customs_rules_path, 'r', encoding='utf-8') as f:
            self.customs_rules = json.load(f)
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def _calculate_duties(self, country: str, total_amount: float) -> Dict[str, float]:
        """Calculate duties and taxes based on country rules."""
        if country not in self.customs_rules:
            return {}
        
        rules = self.customs_rules[country]
        duty_calc = rules.get('duty_calculation', {})
        
        duties = {}
        
        # Base duty
        base_rate = duty_calc.get('base_rate', 0.0)
        duties['duty_amount'] = total_amount * base_rate
        
        # Processing fee
        duties['processing_fee'] = duty_calc.get('processing_fee', 0.0)
        
        # Country-specific taxes
        if 'igst_rate' in duty_calc:  # India
            duties['igst_amount'] = total_amount * duty_calc['igst_rate']
        
        if 'vat_rate' in duty_calc:  # EU, China
            duties['vat_amount'] = total_amount * duty_calc['vat_rate']
        
        if 'icms_rate' in duty_calc:  # Brazil
            duties['icms_amount'] = total_amount * duty_calc['icms_rate']
        
        if 'ipi_rate' in duty_calc:  # Brazil
            duties['ipi_amount'] = total_amount * duty_calc['ipi_rate']
        
        if 'cess_rate' in duty_calc:  # India
            duties['cess_amount'] = total_amount * duty_calc['cess_rate']
        
        if 'harbor_maintenance_fee' in duty_calc:  # USA
            duties['harbor_fee'] = total_amount * duty_calc['harbor_maintenance_fee']
        
        # Total
        duties['total_duties'] = sum(v for k, v in duties.items() if k != 'total_duties')
        
        return duties
    
    def _generate_entry_number(self, country: str) -> str:
        """Generate a mock entry/declaration number."""
        prefix_map = {
            'USA': 'US',
            'India': 'IN',
            'EU': 'EU',
            'China': 'CN',
            'Brazil': 'BR'
        }
        prefix = prefix_map.get(country, 'XX')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}-{timestamp}"
    
    def generate_form(self, extracted_data: Dict, country: str, output_path: str) -> str:
        """
        Generate customs form PDF.
        
        Args:
            extracted_data: Extracted document data
            country: Country code
            output_path: Output file path
            
        Returns:
            Path to generated PDF
        """
        if country not in self.customs_rules:
            raise ValueError(f"Unknown country: {country}")
        
        rules = self.customs_rules[country]
        fields = extracted_data.get('fields', {})
        
        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Title
        form_name = rules.get('form_name', 'Customs Declaration Form')
        story.append(Paragraph(form_name, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Entry number
        entry_number = self._generate_entry_number(country)
        entry_field_name = rules.get('form_fields', {}).get('entry_number', 'Entry Number')
        if 'sad_number' in rules.get('form_fields', {}):
            entry_field_name = 'SAD Number'
        elif 'be_number' in rules.get('form_fields', {}):
            entry_field_name = 'BE Number'
        elif 'declaration_number' in rules.get('form_fields', {}):
            entry_field_name = 'Declaration Number'
        elif 'di_number' in rules.get('form_fields', {}):
            entry_field_name = 'DI Number'
        
        story.append(Paragraph(f"<b>{entry_field_name}:</b> {entry_number}", self.styles['CustomNormal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Form fields mapping
        form_fields = rules.get('form_fields', {})
        
        # Prepare data table
        data = []
        
        # Importer/Exporter info
        if 'buyer_name' in fields:
            buyer_name = fields.get('buyer_name', 'N/A')
            data.append(['Importer Name:', buyer_name])
        
        if 'seller_name' in fields:
            seller_name = fields.get('seller_name', 'N/A')
            data.append(['Exporter Name:', seller_name])
        
        if 'invoice_number' in fields:
            data.append(['Invoice Number:', fields.get('invoice_number', 'N/A')])
        
        if 'date' in fields:
            data.append(['Date:', fields.get('date', 'N/A')])
        
        if 'country_origin' in fields:
            data.append(['Country of Origin:', fields.get('country_origin', 'N/A')])
        
        if 'ship_to' in fields:
            data.append(['Port of Entry:', fields.get('ship_to', 'N/A')])
        
        if 'ship_from' in fields:
            data.append(['Port of Export:', fields.get('ship_from', 'N/A')])
        
        # Amounts
        total_amount = 0.0
        if 'total_amount' in fields:
            try:
                total_amount = float(str(fields['total_amount']).replace(',', '').replace('$', ''))
            except:
                pass
        
        currency = fields.get('currency', 'USD')
        data.append(['Total Value:', f"{currency} {total_amount:,.2f}"])
        
        # Calculate duties
        duties = self._calculate_duties(country, total_amount)
        if duties:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Duties and Taxes:</b>", self.styles['CustomHeading']))
            
            duty_data = []
            for key, value in duties.items():
                if key != 'total_duties':
                    label = key.replace('_', ' ').title()
                    duty_data.append([f"{label}:", f"{currency} {value:,.2f}"])
            
            if 'total_duties' in duties:
                duty_data.append(['<b>Total Duties:</b>', f"<b>{currency} {duties['total_duties']:,.2f}</b>"])
            
            duty_table = Table(duty_data, colWidths=[3*inch, 2*inch])
            duty_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(duty_table)
        
        # Create main data table
        if data:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Document Information:</b>", self.styles['CustomHeading']))
            
            table = Table(data, colWidths=[2.5*inch, 4.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f2f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(table)
        
        # Items table
        if 'items' in fields and fields['items']:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Items:</b>", self.styles['CustomHeading']))
            
            items_data = [['#', 'Description', 'HS Code', 'Qty', 'Unit Price', 'Total']]
            
            for i, item in enumerate(fields['items'], 1):
                desc = item.get('description', 'N/A')[:50]  # Truncate long descriptions
                hs_code = item.get('hs_code', 'N/A')
                qty = item.get('quantity', 0)
                unit_price = item.get('unit_price', 0)
                total = item.get('total_value', 0)
                
                items_data.append([
                    str(i),
                    desc,
                    str(hs_code) if hs_code else 'N/A',
                    f"{qty:.2f}",
                    f"{currency} {unit_price:.2f}",
                    f"{currency} {total:.2f}"
                ])
            
            items_table = Table(items_data, colWidths=[0.4*inch, 2*inch, 1*inch, 0.6*inch, 1*inch, 1*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ]))
            story.append(items_table)
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"<i>Generated by PerfectDocAI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles['CustomNormal']
        ))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Generated customs form for {country} at {output_path}")
        return output_path


# Global generator instance
_generator_instance = None

def get_form_generator() -> CustomsFormGenerator:
    """Get or create form generator instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = CustomsFormGenerator()
    return _generator_instance
