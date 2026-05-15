import os
import logging
from assistant.reasoner import ReasonerAssistant
from tools.ocr_tool import OCRTool
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_initialization():
    print("--- TESTING INITIALIZATION ---")
    
    try:
        print("1. Testing Reasoner (Claude/Sumopod)...")
        reasoner = ReasonerAssistant()
        print(f"   Success: Reasoner initialized with model {reasoner.model_name}")
        
        print("2. Testing OCR Tool (EasyOCR)...")
        # Use GPU=False for safety in test
        ocr = OCRTool(use_gpu=False)
        print("   Success: OCR Tool initialized (Reader ready)")
        
        print("\n--- ALL SYSTEMS READY ---")
        print("Jika tahap ini lolos tapi Telegram tidak merespon, maka masalahnya murni di koneksi Telegram / Token.")
        
    except Exception as e:
        print(f"\n[!] ERROR DETECTED: {str(e)}")

if __name__ == "__main__":
    test_initialization()
