from fpdf import FPDF
from typing import Dict, Any, List
import os
from tools.base_tool import BaseTool

class PDFTool(BaseTool):
    """
    Tool to generate PDF reports for Personal Expense Analysis.
    """
    def __init__(self):
        super().__init__(
            name="pdf_reporter",
            description="Generate a detailed PDF report of the expense analysis",
            version="1.0"
        )

    def validate_input(self, data: Dict[str, Any] = None, **kwargs) -> bool:
        return data is not None and "merchant" in data

    def run(self, data: Dict[str, Any] = None, output_path: str = "report.pdf", **kwargs) -> Dict[str, Any]:
        if not self.validate_input(data=data):
            return {"success": False, "error": "Invalid data for PDF generation"}

        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Header
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Personal Expense Audit Report", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, f"Generated on: {data.get('timestamp', 'N/A')}", ln=True, align="C")
            pdf.ln(10)
            
            # Summary Section
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "1. Summary", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"Merchant: {data.get('merchant', 'Unknown')}", ln=True)
            pdf.cell(0, 8, f"Date: {data.get('date', 'Unknown')}", ln=True)
            pdf.cell(0, 8, f"Status: {data.get('status', 'REVIEW')}", ln=True)
            pdf.cell(0, 8, f"Insight Score: {data.get('insight_score', 0)}/100", ln=True)
            pdf.ln(5)
            
            # Items Table
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "2. Items Detailed Analysis", ln=True)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(80, 8, "Item Name", 1)
            pdf.cell(30, 8, "Category", 1)
            pdf.cell(30, 8, "Price", 1)
            pdf.cell(50, 8, "Flag/Alert", 1)
            pdf.ln()
            
            pdf.set_font("Arial", "", 9)
            for item in data.get('items', []):
                name = str(item.get('name', ''))[:40]
                cat = str(item.get('category', ''))
                price = f"Rp {item.get('price', 0):,}"
                flag = "YES" if item.get('flag') else "NO"
                
                pdf.cell(80, 8, name, 1)
                pdf.cell(30, 8, cat, 1)
                pdf.cell(30, 8, price, 1)
                pdf.cell(50, 8, flag, 1)
                pdf.ln()
                
            pdf.ln(10)
            
            # Alerts & Insights
            if data.get('spending_alerts'):
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "3. Budget Alerts (Critical)", ln=True)
                pdf.set_font("Arial", "", 10)
                for alert in data['spending_alerts']:
                    pdf.multi_cell(0, 8, f"• {alert}")
                pdf.ln(5)
                
            if data.get('insights'):
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "4. Savings Insights", ln=True)
                pdf.set_font("Arial", "", 10)
                for insight in data['insights']:
                    pdf.multi_cell(0, 8, f"• {insight}")
            
            pdf.output(output_path)
            return {"success": True, "file_path": output_path}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
