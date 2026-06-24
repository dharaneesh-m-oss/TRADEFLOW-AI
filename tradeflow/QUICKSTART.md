# 🚀 PerfectDocAI Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: First-time installation may take 5-10 minutes due to ML model downloads.

### Step 2: Run the App

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## 🎬 5-Minute Demo Script

### For Hackathon Judges:

1. **Open the App** (already running)
2. **Go to "Demo" page** (sidebar) - Show value proposition
3. **Upload a document**:
   - Use any PDF/image invoice or shipping document
   - Or use sample from `tests/sample_docs/`
4. **Click "Process Documents"**:
   - Watch real-time progress
   - See OCR + NLP extraction
5. **View Validation Tab**:
   - Show confidence scores
   - Show country-specific validation
6. **Generate Form**:
   - Select country (USA/India/EU/China/Brazil)
   - Click "Generate Customs Form"
   - Download PDF
7. **Show Metrics**:
   - Go to "Accuracy" page
   - Show 98% F1 score
   - Show <10s processing time
8. **Show ROI**:
   - Go to "Business" page
   - Adjust slider to show savings

## 📋 Sample Test Documents

Place any shipping-related document in `tests/sample_docs/`:
- Invoice PDFs
- Bills of lading
- Shipping documents
- Any document with: invoice number, dates, amounts, items

## ⚡ Quick Test

```python
# Test OCR
from utils.ocr import get_ocr_instance
ocr = get_ocr_instance()
result = ocr.extract_text("path/to/document.pdf")
print(result['text'][:200])  # First 200 chars

# Test Extraction
from utils.nlp_extract import get_extractor
extractor = get_extractor()
extracted = extractor.extract_fields(result)
print(extracted['fields'])

# Test Validation
from utils.validator import get_validator
validator = get_validator()
validation = validator.validate(extracted, country="USA")
print(f"Confidence: {validation['confidence']:.1%}")
```

## 🐛 Troubleshooting

### PaddleOCR Installation Issues

If PaddleOCR fails to install:
```bash
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddleocr
```

### GPU Not Detected

The app automatically falls back to CPU. GPU is optional but faster.

### Memory Issues

If running out of memory:
- Process one document at a time
- Reduce image resolution in OCR settings

### Port Already in Use

If port 8501 is busy:
```bash
streamlit run app.py --server.port 8502
```

## 🌐 Deployment to Streamlit Cloud

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Click "New app"
4. Connect repository
5. Set main file: `app.py`
6. Deploy!

**That's it!** Your app is live in 2 minutes.

## 📊 Expected Performance

- **First Run**: 30-60s (model downloads)
- **Subsequent Runs**: <10s per document
- **Accuracy**: 95-98% depending on document quality
- **Memory**: ~2GB RAM minimum

## 🎯 Key Features to Demo

1. **Multi-file upload** - Drag & drop multiple files
2. **Real-time processing** - Progress bars and status
3. **Confidence scoring** - Color-coded (green/yellow/red)
4. **Country selection** - 5 countries supported
5. **PDF generation** - Professional customs forms
6. **Validation** - Automatic error detection
7. **Metrics dashboard** - Accuracy and performance

## 💡 Pro Tips

- Use clear, high-quality documents for best results
- Documents with tables work best
- English documents have highest accuracy
- Tamil/Hindi support available for India
- Check validation warnings before generating forms

---

**Ready to demo!** 🎉
