import openai
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
    LLM Thinking Engine using Sumopod (OpenAI-compatible).
    Applies Personal Budget Rules and categorization.
    """
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-6", base_url: str = None):
        self.api_key = api_key or os.getenv("SUMOPOD_API_KEY")
        self.base_url = base_url or os.getenv("SUMOPOD_BASE_URL")
        
        if not self.api_key:
            raise ValueError("Sumopod API key required.")
        
        # Initialize OpenAI client for Sumopod compatibility
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url if self.base_url else None
        )
        self.model_name = model
        self.phase_name = "REASON"
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        instructions = []
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
        logger.info(f"[{self.phase_name}] Starting thinking with Sumopod AI ({self.model_name})...")
        
        user_prompt = self._build_user_prompt(extracted_data, calc_result, goal_text)
        
        try:
            # Use Chat Completion API (standard for proxies)
            response = self.client.chat.completions.create(
                model=self.model_name,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"DATA TO ANALYZE:\n{user_prompt}\n\nPlease provide the audit result in strict JSON format."}
                ],
                response_format={"type": "json_object"} if "gpt-4" in self.model_name or "gpt-3.5" in self.model_name else None
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON if LLM adds markdown wrapper
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content)
            
            # Metadata
            result['phase'] = self.phase_name
            result['model_used'] = self.model_name
            result['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"[{self.phase_name}] Error: {str(e)}")
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

