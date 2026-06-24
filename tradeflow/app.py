from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from PIL import Image
import easyocr
import numpy as np
import io

from extraction_service import extract_trade_fields
from japan_customs_extraction import extract_japan_customs_fields
from text_cleaning import clean_ocr_text
from compliance_engine import check_compliance

app = FastAPI()

# =============================
# STATIC FILES (UI)
# =============================

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# =============================
# INITIALIZE OCR
# =============================

reader = easyocr.Reader(['en'], gpu=False)


# =============================
# OCR FUNCTION
# =============================

def run_ocr(image: Image.Image) -> str:
    image_np = np.array(image)
    results = reader.readtext(image_np)
    extracted_text = " ".join([res[1] for res in results])
    return extracted_text


# =============================
# UPLOAD ENDPOINT
# =============================

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):

    # Only allow image files
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(
            status_code=400,
            detail="Only image files (PNG, JPG, JPEG) are supported."
        )

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=500, detail="Image could not be read")

    # OCR
    raw_text = run_ocr(image)

    # Clean text
    cleaned_text = clean_ocr_text(raw_text)

    # Document detection
    if "JAPAN CUSTOMS" in cleaned_text.upper():
        extracted_data = extract_japan_customs_fields(cleaned_text)
        document_type = "Japan Customs"
    else:
        extracted_data = extract_trade_fields(cleaned_text)
        document_type = "Generic Trade Document"

    # Compliance
    compliance_result = check_compliance(
        extracted_data.get("hs_code"),
        extracted_data.get("destination_country")
    )

    return {
        "message": "Document processed successfully",
        "document_type": document_type,
        "extracted_data": extracted_data,
        "compliance_result": compliance_result
    }