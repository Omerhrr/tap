# backend/app/services/ocr_service.py
import asyncio
import re
from typing import List, Tuple, Optional
import numpy as np

from app.schemas import OCRItem
from app.config import settings

# Try to import OCR libraries, provide fallback behavior
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def preprocess_receipt(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess receipt image for better OCR results.

    Steps:
    1. Decode image
    2. Resize if too large
    3. Convert to grayscale
    4. Denoise
    5. Enhance contrast (CLAHE)
    6. Binarize
    7. Deskew if needed
    """
    if not CV2_AVAILABLE:
        raise RuntimeError("OpenCV not available. Install with: pip install opencv-python")

    # 1. Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image")

    # 2. Resize if too large (max 2000px width)
    height, width = img.shape[:2]
    if width > 2000:
        scale = 2000 / width
        img = cv2.resize(img, None, fx=scale, fy=scale)

    # 3. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4. Noise reduction
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # 5. Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 6. Binarization
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 7. Deskew if needed (detect rotation)
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) > 0.5:
            center = (width // 2, height // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            binary = cv2.warpAffine(
                binary, M, (width, height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )

    return binary


def run_tesseract_ocr(processed_img: np.ndarray) -> dict:
    """
    Run Tesseract OCR on preprocessed image.
    """
    if not TESSERACT_AVAILABLE:
        raise RuntimeError("Tesseract not available. Install with: apt-get install tesseract-ocr && pip install pytesseract")

    # Set tesseract data path if configured
    if settings.TESSDATA_PREFIX:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSDATA_PREFIX

    # Tesseract configuration
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.$ "'

    data = pytesseract.image_to_data(
        processed_img,
        config=custom_config,
        output_type=pytesseract.Output.DICT
    )

    return data


def extract_items(ocr_data: dict) -> List[OCRItem]:
    """
    Extract items from OCR data.

    Looks for patterns like:
    - "Burger $12.99"
    - "Pizza 16.00"
    - "Salad .... $8.50"
    """
    items = []
    lines = {}

    # Group text by line number
    for i in range(len(ocr_data['text'])):
        confidence = int(ocr_data['conf'][i])
        if confidence > 60:  # Filter low-confidence text
            line_num = ocr_data['line_num'][i]
            text = ocr_data['text'][i].strip()
            if text:
                if line_num not in lines:
                    lines[line_num] = []
                lines[line_num].append(text)

    # Process each line
    for line_num in sorted(lines.keys()):
        line_text = ' '.join(lines[line_num])

        # Pattern: description + price
        # Matches: "Burger $12.99" or "Burger 12.99" or "Burger...$12.99"
        match = re.search(r'([A-Za-z][A-Za-z\s\-\']+)[\s\.\$]*(\d+\.\d{2})\s*$', line_text)
        if match:
            desc = match.group(1).strip()
            price = float(match.group(2))

            # Filter noise (too short descriptions, zero prices)
            if len(desc) > 2 and price > 0:
                # Skip common non-item text
                skip_words = ['subtotal', 'total', 'tax', 'tip', 'discount', 'change', 'cash', 'card', 'amount', 'balance']
                if not any(word in desc.lower() for word in skip_words):
                    items.append(OCRItem(
                        description=desc,
                        amount=price,
                        quantity=1,
                        confidence=None  # Could calculate average confidence per line
                    ))

    return items


def get_raw_text(ocr_data: dict) -> str:
    """Extract raw text from OCR data for debugging/fallback."""
    lines = {}
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if text and int(ocr_data['conf'][i]) > 30:
            line_num = ocr_data['line_num'][i]
            if line_num not in lines:
                lines[line_num] = []
            lines[line_num].append(text)

    return '\n'.join(' '.join(lines[num]) for num in sorted(lines.keys()))


async def process_receipt(image_bytes: bytes) -> Tuple[List[OCRItem], Optional[str]]:
    """
    Main OCR processing function.

    Returns:
        Tuple of (items, raw_text)
    """
    # Run OCR in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    try:
        # Preprocess image
        processed_img = await loop.run_in_executor(None, preprocess_receipt, image_bytes)

        # Run OCR
        ocr_data = await loop.run_in_executor(None, run_tesseract_ocr, processed_img)

        # Extract items
        items = extract_items(ocr_data)

        # Get raw text for debugging
        raw_text = get_raw_text(ocr_data)

        return items, raw_text

    except RuntimeError as e:
        # OCR libraries not available - return empty result
        print(f"OCR Error: {e}")
        return [], None
    except Exception as e:
        print(f"OCR Processing Error: {e}")
        return [], None
