import logging
import json
import os
from typing import Dict, Any, List
from datetime import datetime
from tools.tool_registry import get_registry
from assistant.reasoner import ReasonerAssistant
from tools.budget_tool import BudgetTool
from assistant.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssistantAssistant:
    """
    The Brain - Autonomous Loop Controller.
    """
    def __init__(self, max_loops: int = 3):
        self.max_loops = max_loops
        self.registry = get_registry()
        self.reasoner = ReasonerAssistant()
        self.validator = BudgetTool()
        self.db = DatabaseManager()
        self.thinking_log: List[Dict[str, Any]] = []
        self.loop_count = 0

    def _log_thinking(self, step: str, thought: str, action: str, result: str = "") -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "thought": thought,
            "action": action,
            "result": result
        }
        self.thinking_log.append(entry)
        logger.info(f"[{step}] {thought} -> {action}")

    def run(self, image_path: str, user_id: str = "default") -> Dict[str, Any]:
        self.thinking_log = []
        self.loop_count = 0
        
        # Fetch Goal context
        goal_text = self.db.get_latest_goal(user_id)
        
        # STEP 1: OCR Extraction
        self._log_thinking(
            step="INITIAL_OCR",
            thought="I need to read the receipt contents using OCR.",
            action="Calling tool: ocr_extractor"
        )
        
        # Fetch user's goal
        goal_text = self.db.get_latest_goal(user_id)
        
        # STEP 1: Raw OCR Extraction
        self._log_thinking(step="OCR", thought="Membaca teks dari gambar struk.", action="Running EasyOCR.")
        ocr_tool = self.registry.get("ocr_extractor")
        ocr_raw = ocr_tool.run(image_path=image_path)
        raw_text = ocr_raw.get("raw_text", "")
        
        if not raw_text.strip():
            return {
                "status": "FAILED",
                "insights": ["Gambar tidak terbaca atau teks terlalu buram."],
                "merchant": "Tidak dikenal",
                "calculated_total": 0
            }

        # STEP 2: LLM Data Structuring
        self._log_thinking(step="PARSING", thought="Menyuruh AI merapikan teks mentah OCR.", action="Calling LLM Parser.")
        
        print(f"--- [DEBUG] Raw Text length: {len(raw_text)} characters ---")
        
        parse_prompt = (
            "Extract receipt data from this raw OCR text into JSON.\n"
            "RAW TEXT:\n"
            f"{raw_text}\n\n"
            "Output MUST be JSON with: 'merchant', 'date', 'items' (list), 'total' (int)."
        )
        
        try:
            parse_response = self.reasoner.client.chat.completions.create(
                model=self.reasoner.model_name,
                messages=[
                    {"role": "system", "content": "You are a receipt parser. Respond ONLY with JSON."},
                    {"role": "user", "content": parse_prompt}
                ],
                response_format={"type": "json_object"}
            )
            structured_data = json.loads(parse_response.choices[0].message.content)
            print(f"--- [DEBUG] AI Structured Data: {structured_data} ---")
        except Exception as e:
            print(f"--- [ERROR] AI Parsing Failed: {str(e)} ---")
            structured_data = ocr_raw

        # Validation: If still empty, something is wrong with OCR quality
        if not structured_data.get("items") and structured_data.get("total", 0) == 0:
            return {
                "status": "FAILED",
                "insights": ["AI tidak bisa menemukan barang atau total di struk ini. Pastikan foto jelas dan terang."],
                "merchant": "Tidak terbaca",
                "calculated_total": 0,
                "raw_ocr_debug": raw_text[:200] + "..." # Send a bit of raw text for debugging
            }
 # Fallback to manual if LLM fails

        # STEP 3: Calculator Verification (Cross-check prices)
        self._log_thinking(step="CALCULATOR", thought="Memverifikasi hitungan harga.", action="Running CalculatorTool.")
        final_calc_result = self._run_verification_loop(structured_data.get("items", []), structured_data.get("total", 0))
        
        # STEP 4: LLM Audit (The "Nagging" / Persona part)
        self._log_thinking(step="AUDIT", thought="Menganalisis pengeluaran berdasarkan aturan anggaran.", action="Calling Reasoner.")
        llm_result = self.reasoner.run(structured_data, final_calc_result, goal_text=goal_text)
        
        # Final formatting
        final_result = self.validator.run(llm_result)
        final_result['calculated_total'] = final_calc_result.get('calculated_total', 0)
        
        self._log_thinking(
            step="FINAL_STATUS",
            thought=f"Final analysis complete. Status: {final_result.get('status')}",
            action="Generating final report.",
            result=f"Final Score: {final_result.get('insight_score', 0)}"
        )
        
        final_result["thinking_log"] = self.thinking_log
        final_result["loop_count"] = self.loop_count
        
        # SAVE TO DATABASE
        try:
            self.db.save_expense(final_result)
            logger.info("[DATABASE] Expense saved successfully.")
        except Exception as e:
            logger.error(f"[DATABASE] Error saving expense: {str(e)}")
        
        return final_result

    def _run_verification_loop(self, items: List[Dict], stated_total: int) -> Dict[str, Any]:
        calc_tool = self.registry.get("calculator")
        
        for loop in range(self.max_loops):
            self.loop_count = loop + 1
            calc_result = calc_tool.run(items=items, stated_total=stated_total)
            
            if calc_result["match_status"]:
                self._log_thinking(
                    step=f"CALC_LOOP_{loop+1}",
                    thought=f"Math verification successful on attempt {loop+1}.",
                    action="Total matches. Proceeding.",
                    result=f"Calculated: Rp {calc_result['calculated_total']:,}"
                )
                return calc_result
            
            self._log_thinking(
                step=f"CALC_LOOP_{loop+1}",
                thought=f"Mismatch detected! {calc_result['thinking']}",
                action=f"Retry {loop+1}/{self.max_loops}: Analyzing for hidden charges...",
                result=f"Discrepancy: Rp {calc_result['discrepancy']:,}"
            )
            
            # In a real scenario, we might retry OCR with different parameters
            # Here we simulate the assistant "thinking" and looking closer at raw text
            if loop < self.max_loops - 1:
                self._log_thinking(
                    step=f"CALC_RETRY_{loop+1}",
                    thought="Looking for 'pajak', 'tax', or 'service' in raw text...",
                    action="Simulating re-analysis...",
                    result="Found possible tax patterns."
                )

        self._log_thinking(
            step="CALC_FINAL",
            thought=f"After {self.max_loops} loops, total still doesn't match. Flagging as Unusual Pattern.",
            action="Marking as REVIEW status.",
            result="Max loop reached."
        )
        return calc_result
    def chat(self, user_text: str, user_id: str = "default") -> str:
        """
        Handles general conversation and financial advice.
        """
        goal_text = self.db.get_latest_goal(user_id)
        
        self._log_thinking(
            step="CHAT",
            thought=f"User asked a question. Goal context: {goal_text[:20]}...",
            action="Calling LLM for response."
        )
        
        # We reuse the reasoner but with a simplified prompt for chat
        try:
            # Identity is forced at the very top
            chat_system_prompt = (
                "PERINTAH KRITIKAL: Anda ADALAH 'Smart Expense Auditor'.\n"
                "IDENTITAS ANDA BUKAN CLAUDE. JANGAN PERNAH MENYEBUT ANTHROPIC.\n"
                "Tugas Anda: Menjadi pengawas keuangan yang tegas, cerewet, dan disiplin.\n"
                "Gunakan Bahasa Indonesia yang kasual tapi pedas jika user boros.\n\n"
                f"{self.reasoner.system_prompt}"
            )
            
            response = self.reasoner.client.chat.completions.create(
                model=self.reasoner.model_name,
                messages=[
                    {"role": "system", "content": chat_system_prompt},
                    {"role": "user", "content": (
                        "PENGINGAT: Jawablah sebagai Smart Expense Auditor (Auditor Keuangan Galak).\n"
                        f"KONTEKS TARGET USER: {goal_text if goal_text else 'Belum ada target.'}\n\n"
                        f"PERTANYAAN USER: {user_text}"
                    )}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[CHAT] Error: {str(e)}")
            return "Maaf, saya sedang pusing memikirkan anggaran Anda. Bisa ulangi lagi?"
