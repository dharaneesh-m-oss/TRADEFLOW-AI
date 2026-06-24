# Simple Installation Guide

## Quick Start (Minimal Dependencies)

For a quick hackathon demo, you can run the app with minimal dependencies:

```bash
# Install only core dependencies
pip install streamlit reportlab pillow pandas numpy python-dotenv
```

The app will work in **demo mode** without OCR. You can:
- Use the demo script to see the full workflow
- Manually input document data for testing
- Generate forms with sample data

## Full Installation (With OCR)

### Step 1: Core Dependencies
```bash
pip install streamlit reportlab pillow pandas numpy python-dotenv
```

### Step 2: Choose ONE OCR Option

**Option A: EasyOCR (Recommended for Windows)**
```bash
pip install easyocr
```

**Option B: PaddleOCR (Best Accuracy)**
```bash
# Windows: Use Chinese mirror
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddleocr
```

**Option C: Tesseract (Lightweight)**
```bash
pip install pytesseract
# Also install Tesseract binary from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Step 3: PDF Support (Optional)
```bash
pip install pdf2image
# Also install poppler-utils (see INSTALL_WINDOWS.md)
```

## Verify Installation

Run the demo script:
```bash
python demo_script.py
```

If it completes without errors, you're ready to go!

## Run the App

```bash
streamlit run app.py
```

## Troubleshooting

**If OCR installation fails**: The app will work in demo mode. You can still test all features except actual OCR extraction.

**If PDF upload fails**: Install pdf2image and poppler-utils, or use image files (PNG/JPG) instead.

**For Windows-specific issues**: See `INSTALL_WINDOWS.md`
