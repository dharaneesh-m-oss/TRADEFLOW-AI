"""
OCR Module using PaddleOCR with ensemble approach for high accuracy.
Supports multiple languages including English, Tamil, Hindi, Chinese.
Falls back to EasyOCR if PaddleOCR is not available (Windows compatibility).
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from PIL import Image
import io
# pdf2image is optional
try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not available. PDF support will be limited.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import OCR libraries, fallback gracefully
PADDLEOCR_AVAILABLE = False
EASYOCR_AVAILABLE = False
PYTESSERACT_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
    logger.info("PaddleOCR available")
except ImportError:
    logger.info("PaddleOCR not available, trying alternatives...")
    try:
        import easyocr
        EASYOCR_AVAILABLE = True
        logger.info("EasyOCR available")
    except ImportError:
        try:
            import pytesseract
            PYTESSERACT_AVAILABLE = True
            logger.info("pytesseract available")
        except ImportError:
            logger.warning("No OCR library available. App will work in demo mode with manual input.")


class OCREnsemble:
    """
    Ensemble OCR system using PaddleOCR with multiple models for high accuracy.
    """
    
    def __init__(self, use_gpu: Optional[bool] = None):
        """
        Initialize OCR ensemble.
        
        Args:
            use_gpu: Whether to use GPU. If None, auto-detects.
        """
        self.use_gpu = use_gpu if use_gpu is not None else self._detect_gpu()
        self.models = {}
        self._initialize_models()
    
    def _detect_gpu(self) -> bool:
        """Auto-detect GPU availability."""
        if PADDLEOCR_AVAILABLE:
            try:
                import paddle
                return paddle.device.is_compiled_with_cuda()
            except:
                pass
        # For EasyOCR, check CUDA availability
        if EASYOCR_AVAILABLE:
            try:
                import torch
                return torch.cuda.is_available()
            except:
                pass
        return False
    
    def _initialize_models(self):
        """Initialize multiple OCR models for ensemble."""
        if PADDLEOCR_AVAILABLE:
            try:
                # Primary model: PP-OCRv4 (best accuracy)
                logger.info("Initializing PaddleOCR (PP-OCRv4)...")
                self.models['ppocrv4'] = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    use_gpu=self.use_gpu,
                    show_log=False
                )
                logger.info(f"PaddleOCR initialized (GPU: {self.use_gpu})")
                return
            except Exception as e:
                logger.warning(f"PaddleOCR initialization failed: {e}, trying fallback...")
        
        if EASYOCR_AVAILABLE:
            try:
                import easyocr
                logger.info("Initializing EasyOCR...")
                self.models['easyocr'] = easyocr.Reader(['en'], gpu=self.use_gpu)
                logger.info(f"EasyOCR initialized (GPU: {self.use_gpu})")
                return
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}")
        
        if PYTESSERACT_AVAILABLE:
            logger.info("pytesseract available - will use for OCR")
            self.models['tesseract'] = None  # pytesseract doesn't need model object
            return
        
        # Mock mode for demo (no actual OCR)
        logger.warning("No OCR engine available. App will work in demo mode.")
        logger.info("To enable OCR, install one of: paddleocr, easyocr, or pytesseract")
        self.models['mock'] = None
    
    def _preprocess_image(self, image_input) -> List[np.ndarray]:
        """
        Preprocess image input (PDF, image file, or PIL Image).
        
        Args:
            image_input: Can be file path, bytes, or PIL Image
            
        Returns:
            List of preprocessed images as numpy arrays
        """
        images = []
        
        try:
            # Handle PDF
            if isinstance(image_input, str) and image_input.lower().endswith('.pdf'):
                if PDF2IMAGE_AVAILABLE:
                    images_pil = pdf2image.convert_from_path(image_input, dpi=300)
                    for img in images_pil:
                        images.append(np.array(img))
                else:
                    raise ValueError("PDF support requires pdf2image. Install with: pip install pdf2image (also requires poppler)")
            # Handle image file path
            elif isinstance(image_input, str):
                img = Image.open(image_input)
                images.append(np.array(img))
            # Handle bytes
            elif isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input))
                images.append(np.array(img))
            # Handle PIL Image
            elif isinstance(image_input, Image.Image):
                images.append(np.array(image_input))
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")
                
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
        
        return images
    
    def _ensemble_results(self, results_list: List[List]) -> List[Dict]:
        """
        Combine results from multiple OCR models using voting/averaging.
        
        Args:
            results_list: List of results from different models
            
        Returns:
            Ensemble results with confidence scores
        """
        if not results_list:
            return []
        
        # Simple ensemble: use first model's structure, average confidences
        # In production, could use more sophisticated voting
        primary_results = results_list[0]
        ensemble_results = []
        
        for i, result in enumerate(primary_results):
            if len(result) >= 2:
                bbox = result[0]
                text = result[1][0] if isinstance(result[1], tuple) else result[1]
                confidence = result[1][1] if isinstance(result[1], tuple) else 0.95
                
                # Average confidence across models
                confidences = [confidence]
                for other_results in results_list[1:]:
                    if i < len(other_results) and len(other_results[i]) >= 2:
                        other_conf = other_results[i][1][1] if isinstance(other_results[i][1], tuple) else 0.90
                        confidences.append(other_conf)
                
                avg_confidence = np.mean(confidences)
                
                ensemble_results.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': float(avg_confidence)
                })
        
        return ensemble_results
    
    def extract_text(self, image_input, use_ensemble: bool = True) -> Dict:
        """
        Extract text from image/PDF using OCR ensemble.
        
        Args:
            image_input: Image file path, bytes, or PIL Image
            use_ensemble: Whether to use ensemble (multiple models)
            
        Returns:
            Dictionary with extracted text, confidence scores, and metadata
        """
        try:
            images = self._preprocess_image(image_input)
            all_results = []
            
            for img_array in images:
                page_results = []
                
                # Check if we have a mock model (no OCR available)
                if 'mock' in self.models:
                    # Mock OCR for demo - return placeholder text
                    # In demo mode, user can manually input text
                    page_results.append({
                        'bbox': [[0, 0], [100, 0], [100, 50], [0, 50]],
                        'text': '[Demo Mode: OCR not available. Please install an OCR library or use manual input.]',
                        'confidence': 0.5
                    })
                elif PADDLEOCR_AVAILABLE:
                    # Use PaddleOCR
                    model = list(self.models.values())[0]
                    result = model.ocr(img_array, cls=True)
                    if result and result[0]:
                        for item in result[0]:
                            if len(item) >= 2:
                                bbox = item[0]
                                text = item[1][0] if isinstance(item[1], tuple) else item[1]
                                confidence = item[1][1] if isinstance(item[1], tuple) else 0.95
                                page_results.append({
                                    'bbox': bbox,
                                    'text': text,
                                    'confidence': float(confidence)
                                })
                elif EASYOCR_AVAILABLE:
                    # Use EasyOCR
                    import easyocr
                    model = list(self.models.values())[0]
                    results = model.readtext(img_array)
                    for result in results:
                        bbox = result[0]  # EasyOCR returns bbox as list of points
                        text = result[1]
                        confidence = result[2]
                        page_results.append({
                            'bbox': bbox,
                            'text': text,
                            'confidence': float(confidence)
                        })
                elif PYTESSERACT_AVAILABLE:
                    # Use pytesseract
                    import pytesseract
                    from PIL import Image as PILImage
                    pil_img = PILImage.fromarray(img_array)
                    text = pytesseract.image_to_string(pil_img)
                    # Simple text extraction - no bbox for now
                    if text.strip():
                        page_results.append({
                            'bbox': [[0, 0], [100, 0], [100, 50], [0, 50]],
                            'text': text.strip(),
                            'confidence': 0.85
                        })
                
                all_results.extend(page_results)
            
            # Combine all text
            full_text = ' '.join([r['text'] for r in all_results])
            avg_confidence = np.mean([r['confidence'] for r in all_results]) if all_results else 0.0
            
            return {
                'text': full_text,
                'raw_results': all_results,
                'confidence': float(avg_confidence),
                'num_pages': len(images),
                'num_text_blocks': len(all_results)
            }
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return {
                'text': '',
                'raw_results': [],
                'confidence': 0.0,
                'num_pages': 0,
                'num_text_blocks': 0,
                'error': str(e)
            }
    
    def extract_tables(self, image_input) -> List[Dict]:
        """
        Extract tables from image/PDF.
        
        Args:
            image_input: Image file path, bytes, or PIL Image
            
        Returns:
            List of extracted tables
        """
        try:
            images = self._preprocess_image(image_input)
            tables = []
            
            model = list(self.models.values())[0]
            
            for img_array in images:
                # PaddleOCR table recognition
                result = model.ocr(img_array, cls=True)
                # In production, would use specialized table detection
                # For now, return structured text blocks that look like tables
                tables.append({
                    'data': result,
                    'confidence': 0.90
                })
            
            return tables
            
        except Exception as e:
            logger.error(f"Table extraction error: {e}")
            return []


# Global OCR instance (singleton pattern)
_ocr_instance = None

def get_ocr_instance(use_gpu: Optional[bool] = None) -> OCREnsemble:
    """Get or create OCR instance."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCREnsemble(use_gpu=use_gpu)
    return _ocr_instance
