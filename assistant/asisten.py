import logging
from typing import Dict, Any, List
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleBasedAssistant:
    """
    Deterministic validation layer to ensure LLM consistency.
    Acts as a safety net for Personal Budget Rules.
    """
    
    CATEGORY_LIMITS = {
        "MAKANAN": 150_000,
        "MINUMAN": 50_000,
        "TRANSPORTASI": 200_000,
        "HIBURAN": 0,  # Attention if > 0
        "BELANJA": 100_000,
        "UTILITAS": 500_000,
        "KESEHATAN": 1_000_000,
        "LAINNYA": 100_000
    }

    FORBIDDEN_KEYWORDS = {
        'rokok': 'Produk tembakau dilarang dalam anggaran.',
        'sampoerna': 'Produk tembakau dilarang dalam anggaran.',
        'djarum': 'Produk tembakau dilarang dalam anggaran.',
        'vape': 'Produk tembakau/vape dilarang.',
        'alkohol': 'Minuman beralkohol dilarang.',
        'beer': 'Minuman beralkohol dilarang.',
        'wine': 'Minuman beralkohol dilarang.',
        'voucher': 'Voucher game/digital perlu perhatian.',
        'steam': 'Voucher game dilarang.',
        'skincare': 'Skincare non-medis perlu perhatian.',
        'parfum': 'Parfum/Kosmetik perlu perhatian.'
    }

    def __init__(self):
        self.phase_name = "VALIDATION"

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refines the LLM result with deterministic rules.
        """
        logger.info(f"[{self.phase_name}] Starting rule-based validation...")
        
        refined = dict(data)
        items = refined.get('items', [])
        
        # 1. Validate Forbidden Keywords
        self._validate_forbidden_items(refined)
        
        # 2. Validate Category Spending Limits
        self._validate_limits(refined)
        
        # 3. Detect Duplicates
        self._detect_duplicates(refined)
        
        # 4. Recalculate Insight Score & Status
        self._finalize_status_and_score(refined)
        
        return refined

    def _validate_forbidden_items(self, data: Dict[str, Any]) -> None:
        items = data.get('items', [])
        alerts = data.get('spending_alerts', [])
        
        for item in items:
            name_lower = item.get('name', '').lower()
            for kw, reason in self.FORBIDDEN_KEYWORDS.items():
                if kw in name_lower:
                    item['spending_alert'] = True
                    item['budget_reason'] = reason
                    item['flag'] = True
                    if reason not in alerts:
                        alerts.append(f"{item['name']}: {reason}")
        
        data['spending_alerts'] = alerts

    def _validate_limits(self, data: Dict[str, Any]) -> None:
        items = data.get('items', [])
        patterns = data.get('unusual_patterns', [])
        
        for item in items:
            cat = item.get('category', 'LAINNYA').upper()
            price = item.get('price', 0)
            limit = self.CATEGORY_LIMITS.get(cat, 100_000)
            
            if cat == "HIBURAN" and price > 0:
                item['flag'] = True
                item['reason'] = "Hiburan harus dikontrol ketat untuk mencapai target tabungan."
                patterns.append(f"{item['name']}: Pengeluaran hiburan (kategori non-pokok) terdeteksi.")
            elif price > limit:
                item['flag'] = True
                item['reason'] = f"Harga melebihi limit {cat} (Rp {limit:,})"
                patterns.append(f"{item['name']}: Melebihi limit {cat}.")
        
        data['unusual_patterns'] = patterns

    def _detect_duplicates(self, data: Dict[str, Any]) -> None:
        items = data.get('items', [])
        if len(items) < 2: return
        
        patterns = data.get('unusual_patterns', [])
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                name1 = items[i].get('name', '').lower()
                name2 = items[j].get('name', '').lower()
                similarity = SequenceMatcher(None, name1, name2).ratio()
                
                if similarity > 0.85:
                    items[i]['flag'] = True
                    items[j]['flag'] = True
                    msg = f"Kemungkinan duplikasi: {items[i]['name']} & {items[j]['name']}"
                    if msg not in patterns:
                        patterns.append(msg)
        
        data['unusual_patterns'] = patterns

    def _finalize_status_and_score(self, data: Dict[str, Any]) -> None:
        # Simple scoring logic
        score = 0
        alerts = data.get('spending_alerts', [])
        patterns = data.get('unusual_patterns', [])
        
        score += len(alerts) * 40
        score += len(patterns) * 20
        if not data.get('total_match', True):
            score += 25
            
        data['insight_score'] = min(100, score)
        
        # Final Status determination
        if len(alerts) > 0 or score >= 80:
            data['status'] = "ATTENTION"
        elif len(patterns) > 0 or score >= 40:
            data['status'] = "REVIEW"
        else:
            data['status'] = "APPROVED"
            
        if data['status'] == "ATTENTION" and not data.get('attention_reason'):
            data['attention_reason'] = "Melanggar Aturan Anggaran Pribadi."
