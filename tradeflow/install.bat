@echo off
echo ========================================
echo PerfectDocAI Installation Script (Windows)
echo ========================================
echo.

echo Step 1: Installing basic dependencies...
pip install streamlit reportlab pillow python-dotenv pdf2image pandas numpy

echo.
echo Step 2: Installing EasyOCR (works on Windows)...
pip install easyocr

echo.
echo Step 3: Attempting to install PaddleOCR (optional)...
pip install paddleocr 2>nul
if %errorlevel% neq 0 (
    echo PaddleOCR installation skipped (not critical)
    echo The app will use EasyOCR instead
) else (
    echo PaddleOCR installed successfully
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To run the app:
echo   streamlit run app.py
echo.
pause
