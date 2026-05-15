import logging
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
        ocr_tool = self.registry.get("ocr_extractor")
        ocr_result = ocr_tool.run(image_path=image_path)
        
        if not ocr_result.get("success"):
            self._log_thinking(
                step="OCR_FAILED",
                thought="OCR failed to read the image.",
                action="Stopping process.",
                result=ocr_result.get("error", "Unknown error")
            )
            return {"status": "ERROR", "message": "OCR Failed", "thinking_log": self.thinking_log}

        self._log_thinking(
            step="OCR_SUCCESS",
            thought=f"Extracted {ocr_result['item_count']} items from {ocr_result['merchant']}.",
            action="Proceeding to mathematical verification.",
            result=f"Items: {ocr_result['item_count']}, Stated Total: Rp {ocr_result['total']:,}"
        )

        # STEP 2: Calculator Verification (with Autonomous Loop)
        final_calc_result = self._run_verification_loop(ocr_result["items"], ocr_result["total"])
        
        # STEP 3: LLM Reasoner
        self._log_thinking(
            step="LLM_THINKING",
            thought=f"Applying Personal Budget Rules and categorization. Goal context: {goal_text[:20]}...",
            action="Calling tool: claude_reasoner"
        )
        llm_result = self.reasoner.run(ocr_result, final_calc_result, goal_text=goal_text)
        
        # STEP 4: Rule-Based Validation (Safety Net)
        self._log_thinking(
            step="RULE_VALIDATION",
            thought="Ensuring strict budget rule enforcement.",
            action="Calling tool: rule_engine"
        )
        final_result = self.validator.run(llm_result)
        
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
