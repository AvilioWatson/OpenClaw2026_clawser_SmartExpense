from typing import Dict, Any, List
from tools.base_tool import BaseTool

class CalculatorTool(BaseTool):
    """
    Calculator Tool for mathematical verification and mismatch detection.
    """
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Calculate totals, detect mismatches, and suggest reasons for discrepancies",
            version="1.0"
        )
        self.tolerance = 1000  # Rp 1.000 tolerance for rounding issues

    def validate_input(self, items: List[Dict] = None, stated_total: int = None, **kwargs) -> bool:
        return isinstance(items, list) and isinstance(stated_total, (int, float))

    def run(self, items: List[Dict] = None, stated_total: int = 0, **kwargs) -> Dict[str, Any]:
        if not self.validate_input(items=items, stated_total=stated_total):
            return {
                "success": False,
                "error": "Invalid input",
                "calculated_total": 0,
                "match_status": False,
                "discrepancy": 0,
                "thinking": "Input invalid"
            }

        calculated = sum(item.get("price", 0) for item in items)
        discrepancy = stated_total - calculated
        match_status = abs(discrepancy) <= self.tolerance
        
        thinking = self._generate_thinking(calculated, stated_total, discrepancy)
        
        return {
            "success": True,
            "tool_used": self.name,
            "calculated_total": calculated,
            "stated_total": stated_total,
            "match_status": match_status,
            "discrepancy": discrepancy,
            "thinking": thinking,
            "requires_loop": not match_status
        }

    def _generate_thinking(self, calculated: int, stated: int, discrepancy: int) -> str:
        if abs(discrepancy) <= self.tolerance:
            return f"Total matches: Calculated Rp {calculated:,} vs Stated Rp {stated:,}"
        
        if discrepancy > 0:
            tax_est = round((discrepancy / calculated) * 100, 1) if calculated > 0 else 0
            return f"Mismatch: Stated total (Rp {stated:,}) is higher by Rp {discrepancy:,}. Possible tax/service charge (~{tax_est}%)."
        else:
            return f"Mismatch: Calculated total (Rp {calculated:,}) is higher by Rp {abs(discrepancy):,}. Possible missing discount or OCR error."
