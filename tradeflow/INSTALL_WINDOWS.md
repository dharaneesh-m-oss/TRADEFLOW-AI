# Windows Installation Guide for PerfectDocAI

## Quick Install (Recommended)

### Option 1: Use EasyOCR (Easiest for Windows)

```bash
# Install basic dependencies
pip install -r requirements.txt

# EasyOCR will be installed automatically and works on Windows without PaddlePaddle
```

EasyOCR is included in requirements.txt and works immediately on Windows without additional setup.

### Option 2: Install PaddleOCR (For Best Accuracy)

PaddleOCR requires PaddlePaddle, which has special installation on Windows:

```bash
# Step 1: Install PaddlePaddle (CPU version for Windows)
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple

# Step 2: Install PaddleOCR
pip install paddleocr

# Step 3: Install other dependencies
pip install -r requirements.txt
```

**Note**: If PaddlePaddle installation fails, use Option 1 (EasyOCR) which works out of the box.

## Full Installation Steps

1. **Install Python 3.12+** (if not already installed)
   - Download from https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **For PDF support**, install Poppler (required by pdf2image):
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract and add `bin` folder to PATH
   - Or use: `conda install -c conda-forge poppler`

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

## Troubleshooting

### Error: "No module named 'paddleocr'"

**Solution**: Install EasyOCR instead (included in requirements.txt):
```bash
pip install easyocr
```

The app will automatically use EasyOCR if PaddleOCR is not available.

### Error: "pdf2image requires poppler"

**Solution**: Install Poppler:
- Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/
- Extract and add to PATH
- Or use conda: `conda install -c conda-forge poppler`

### Error: "Could not find a version that satisfies paddlepaddle"

**Solution**: This is normal on Windows. Use EasyOCR instead:
```bash
pip install easyocr
```

The app will detect and use EasyOCR automatically.

## Verification

Run the demo script to verify installation:

```bash
python demo_script.py
```

If you see "✅ Demo complete!" without errors, installation is successful.

## Performance Notes

- **EasyOCR**: Works immediately, good accuracy (~95%), slower on CPU
- **PaddleOCR**: Best accuracy (~99%), requires PaddlePaddle installation
- **GPU**: Optional but recommended for faster processing

## Alternative: Use Docker (No Windows Setup Needed)

If installation is problematic, use Docker:

```bash
docker build -t perfectdocai .
docker run -p 8501:8501 perfectdocai
```

This avoids all Windows-specific installation issues.
