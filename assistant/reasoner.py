import google.generativeai as genai
import json
import os
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReasonerAssistant:
    """
    LLM Thinking Engine using Gemini Flash.
    Applies Personal Budget Rules and categorization.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key required.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.phase_name = "REASON"
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        instructions = []
        # Paths to mandatory files
        base_dir = os.path.join(os.path.dirname(__file__), "..")
        agents_path = os.path.join(base_dir, "AGENTS.md")
        soul_path = os.path.join(base_dir, "SOUL.md")
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")

        if os.path.exists(agents_path):
            with open(agents_path, "r", encoding="utf-8") as f:
                instructions.append(f"### AGENT DEFINITION ###\n{f.read()}")
        
        if os.path.exists(soul_path):
            with open(soul_path, "r", encoding="utf-8") as f:
                instructions.append(f"### AGENT SOUL/PERSONALITY ###\n{f.read()}")

        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                instructions.append(f"### TECHNICAL FORMAT ###\n{f.read()}")

        return "\n\n".join(instructions) if instructions else "You are a Disciplined Personal Expense Auditor."

    def run(self, extracted_data: Dict[str, Any], calc_result: Dict[str, Any], goal_text: str = "") -> Dict[str, Any]:
        logger.info(f"[{self.phase_name}] Starting thinking with Gemini...")
        
        user_prompt = self._build_user_prompt(extracted_data, calc_result, goal_text)
        
        try:
            # Gemini 1.5 Flash supports system instruction in the model constructor or in the prompt
            # For simplicity, we combine system prompt and user prompt
            full_prompt = f"{self.system_prompt}\n\nDATA TO ANALYZE:\n{user_prompt}\n\nJSON OUTPUT:"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            
            content = response.text
            result = json.loads(content)
            
            # Metadata
            result['phase'] = self.phase_name
            result['model_used'] = "gemini-1.5-flash"
            result['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"[{self.phase_name}] Error: {str(e)}")
            # Fallback result if LLM fails
            return {
                "status": "REVIEW",
                "insights": [f"Thinking failed: {str(e)}"],
                "total_match": calc_result.get("match_status", False)
            }

    def _build_user_prompt(self, extracted: Dict[str, Any], calc: Dict[str, Any], goal_text: str = "") -> str:
        goal_context = f"\nUSER FINANCIAL GOAL: {goal_text}\n(Jika pengeluaran ini menghambat goal tersebut, berikan omelan/nasehat yang tegas dalam field 'insights'.)\n" if goal_text else ""
        
        return f"""
        {goal_context}
        Merchant: {extracted.get('merchant', 'Unknown')}
        Date: {extracted.get('date', 'Unknown')}
        Items: {json.dumps(extracted.get('items', []), indent=2)}
        Stated Total: Rp {extracted.get('total', 0):,}
        
        Verification Result:
        Calculated Total: Rp {calc.get('calculated_total', 0):,}
        Match: {calc.get('match_status')}
        Thinking: {calc.get('thinking', '')}
        """
