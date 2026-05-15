import easyocr
import re
from typing import Tuple, Dict, List, Any
from PIL import Image
import numpy as np
import os
from tools.base_tool import BaseTool

class OCRTool(BaseTool):
    """
    OCR Tool using EasyOCR with Indonesian and English languages.
    """
    def __init__(self, use_gpu: bool = False):
        super().__init__(
            name="ocr_extractor",
            description="Extract text and structured data from receipt images using OCR",
            version="1.0"
        )
        self.reader = easyocr.Reader(['id', 'en'], gpu=use_gpu)
        
        # Price patterns (supports Rp 1.000, 1,000, 1000)
        self.price_pattern = re.compile(
            r'(?:Rp\s?)?([\d]{1,3}(?:[.,]\d{3})*(?:,\d{2})?)',
            re.IGNORECASE
        )
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'(\d{2})[/-](\d{2})[/-](\d{4})'),
            re.compile(r'(\d{2})[/-](\d{2})[/-](\d{2})'),
            re.compile(r'(\d{4})[/-](\d{2})[/-](\d{2})'),
        ]
        
        self.total_keywords = [
            'total', 'jumlah', 'bayar', 'grand total', 'total bayar',
            'total belanja', 'subtotal', 'tagihan', 'amount'
        ]
        
        self.noise_words = [
            'terima kasih', 'thank you', 'selamat', 'datang',
            'kembali', 'cashier', 'kasir', 'shift', 'no.', 'nomor'
        ]

    def validate_input(self, image_path: str = None, **kwargs) -> bool:
        if not image_path or not os.path.exists(image_path):
            return False
        try:
            img = Image.open(image_path)
            img.verify()
            return True
        except Exception:
            return False

    def run(self, image_path: str = None, **kwargs) -> Dict[str, Any]:
        if not self.validate_input(image_path=image_path):
            return {
                "success": False,
                "error": "Invalid image path or file",
                "merchant": "Unknown",
                "date": "Unknown",
                "items": [],
                "total": 0,
                "raw_text": ""
            }

        # Preprocess and Run OCR
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Simple resize if too large
        max_width = 1920
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        image_np = np.array(img)
        result = self.reader.readtext(image_np, detail=0, paragraph=False)
        raw_text = "\n".join(result)
        
        structured_data = self._parse_receipt(raw_text)
        structured_data["success"] = True
        structured_data["raw_text"] = raw_text
        structured_data["tool_used"] = self.name
        
        return structured_data

    def _parse_receipt(self, text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return {"merchant": "Unknown", "date": "Unknown", "items": [], "total": 0, "item_count": 0}

        merchant = self._extract_merchant(lines)
        date = self._extract_date(text)
        items, total = self._extract_items_and_total(lines)

        return {
            "merchant": merchant,
            "date": date,
            "items": items,
            "total": total,
            "item_count": len(items)
        }

    def _extract_merchant(self, lines: List[str]) -> str:
        for line in lines[:3]:
            lower_line = line.lower()
            if any(noise in lower_line for noise in self.noise_words):
                continue
            if re.match(r'^\d+$', line) or re.match(r'^\d{2}[/-]\d{2}[/-]\d{2,4}$', line):
                continue
            if len(line) > 2:
                return line
        return "Unknown Merchant"

    def _extract_date(self, text: str) -> str:
        for pattern in self.date_patterns:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return "Unknown"

    def _extract_items_and_total(self, lines: List[str]) -> Tuple[List[Dict], int]:
        items = []
        total = 0
        total_found = False
        lines_with_prices = []

        for i, line in enumerate(lines):
            prices = self._extract_prices(line)
            if prices:
                lines_with_prices.append((i, line, prices))

        if not lines_with_prices:
            return items, total

        for idx, (line_idx, line, prices) in enumerate(lines_with_prices):
            lower_line = line.lower()
            is_total_line = any(keyword in lower_line for keyword in self.total_keywords)
            is_last_price = idx == len(lines_with_prices) - 1

            if is_total_line or (is_last_price and not total_found):
                total = prices[-1]
                total_found = True
            else:
                price = prices[-1]
                item_name = self._clean_item_name(line, prices)
                if item_name and len(item_name) > 2 and price > 1000:
                    items.append({"name": item_name, "price": price, "line_index": line_idx})

        if not total_found and items:
            total = sum(item["price"] for item in items)

        return items, total

    def _extract_prices(self, line: str) -> List[int]:
        matches = self.price_pattern.findall(line)
        prices = []
        for match in matches:
            try:
                # Clean delimiters
                clean = match.replace('.', '').replace(',', '')
                price = int(clean)
                if price > 100:
                    prices.append(price)
            except ValueError:
                continue
        return prices

    def _clean_item_name(self, line: str, prices: List[int]) -> str:
        cleaned = line
        for price in prices:
            price_str = str(price)
            # Remove variations of price from the line to get the name
            for fmt in [price_str, f"Rp{price_str}", f"Rp {price_str}", f"{price_str},-"]:
                cleaned = cleaned.replace(fmt, "")
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
