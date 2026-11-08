"""Quick test to verify Tesseract OCR is working."""
from app.services.ocr_service import OCRService

# Test if Tesseract is available
if OCRService.is_tesseract_available():
    print("✅ Tesseract OCR is installed and working!")
    import pytesseract
    version = pytesseract.get_tesseract_version()
    print(f"   Version: {version}")
else:
    print("❌ Tesseract OCR is NOT available")
    print("   Please install Tesseract OCR:")
    print("   winget install --id UB-Mannheim.TesseractOCR")

# Test with a simple image (1x1 pixel won't have text, but tests the pipeline)
test_data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

try:
    result = OCRService.extract_text_from_data_url(test_data_url)
    print(f"\n✅ OCR pipeline working!")
    print(f"   Test extraction result: {repr(result)}")
except Exception as e:
    print(f"\n❌ OCR pipeline error: {e}")
