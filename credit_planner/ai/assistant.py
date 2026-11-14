"""Context-grounded Free AI Financial Assistant (Ollama, Gemini, Deterministic Fallback)."""
import os
import json
import requests
from typing import Optional
from credit_planner.db import DatabaseManager
from credit_planner.ai.context_builder import build_financial_context_snapshot


class AIAssistant:
    def __init__(
        self,
        db: DatabaseManager,
        model_name: str = "phi3.5",
        ollama_url: str = "http://localhost:11434/api/generate",
        mock_offline: bool = False,
    ):
        self.db = db
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.mock_offline = mock_offline

    def ask(self, question: str) -> str:
        """Answers a user financial question grounded strictly in their current SQLite snapshot."""
        context_snapshot = build_financial_context_snapshot(self.db)

        system_prompt = (
            "You are a helpful, privacy-preserving AI debt payoff advisor and credit card strategist.\n"
            "Answer the user's questions clearly and concisely based on the following verified financial snapshot.\n"
            "Rely strictly on the pre-calculated numbers provided in the snapshot.\n\n"
            f"{context_snapshot}\n"
        )

        if not self.mock_offline:
            # 1. Try local Ollama first
            ollama_response = self._try_ollama(system_prompt, question)
            if ollama_response:
                return ollama_response

            # 2. Try Google Gemini Free Tier if API key is present
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if gemini_key:
                gemini_response = self._try_gemini(gemini_key, system_prompt, question)
                if gemini_response:
                    return gemini_response

        # 3. Deterministic rule-based fallback
        return self._deterministic_fallback(context_snapshot, question)

    def _try_ollama(self, system_prompt: str, question: str) -> Optional[str]:
        try:
            payload = {
                "model": self.model_name,
                "prompt": f"{system_prompt}\nUser Question: {question}\nAdvisor:",
                "stream": False,
            }
            resp = requests.post(self.ollama_url, json=payload, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
        except Exception:
            return None
        return None

    def _try_gemini(self, api_key: str, system_prompt: str, question: str) -> Optional[str]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_prompt}\nUser Question: {question}"}
                        ]
                    }
                ]
            }
            resp = requests.post(url, json=payload, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            return None
        return None

    def _deterministic_fallback(self, context_snapshot: str, question: str) -> str:
        """Rule-based financial advice when offline."""
        cards = self.db.get_cards()
        if not cards:
            return "No credit cards are registered. Use 'credit-planner parse <statement.pdf>' to add a statement."

        # Find card with highest APR
        highest_apr_card = None
        max_apr = -1.0
        for c in cards:
            stmts = self.db.get_statements_for_card(c.id)
            apr = stmts[0].purchase_apr if stmts else c.current_apr
            if apr > max_apr:
                max_apr = apr
                highest_apr_card = c

        return (
            f"Based on your current financial plan:\n\n"
            f"• Under the **Debt Avalanche** strategy, you should prioritize paying extra on "
            f"**{highest_apr_card.card_name}** because it carries your highest interest rate ({max_apr:.2f}% APR).\n"
            f"• Make sure to continue paying at least the minimum required payments on all other cards.\n\n"
            f"Snapshot Details:\n{context_snapshot}"
        )
