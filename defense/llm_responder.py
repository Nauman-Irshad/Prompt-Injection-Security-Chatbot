#!/usr/bin/env python3
"""
Small LLM responder for SAFE queries only.
Uses google/flan-t5-small (lightweight, runs on CPU).
Falls back to Ollama if available, then rule-based answers.
"""

import json
import os
import warnings

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
warnings.filterwarnings("ignore")

import urllib.error
import urllib.request

FLEET_CONTEXT = """
Fleet database:
- VH001 Tesla $55000
- VH002 Ford $35000
- VH003 BMW $45000
- VH004 Toyota $25000
- VH005 Mercedes $65000
Maintenance: oil change every 5000 miles, tire check monthly.
"""

RULE_ANSWERS = {
    "vh001": "VH001 is a Tesla priced at $55,000. Last service due in 6 months.",
    "vh002": "VH002 is a Ford priced at $35,000. Regular maintenance recommended.",
    "vh003": "VH003 is a BMW priced at $45,000. Brake fluid check scheduled.",
    "vehicle records": "The fleet has 5 vehicles: Tesla, Ford, BMW, Toyota, Mercedes.",
    "maintenance": "All vehicles need oil changes every 5000 miles and monthly tire checks.",
    "fleet": "The fleet contains 5 vehicles with IDs VH001 through VH005.",
}

SMALL_LLM_MODEL = "google/flan-t5-small"


class SmallLLMResponder:
    def __init__(self):
        self._pipeline = None
        self._model_name = SMALL_LLM_MODEL
        self._ollama_model = "phi3:mini"
        self._ready = False

    def warm_up(self, quiet: bool = True) -> str:
        """Load small LLM once at startup so first safe query is fast."""
        if self._ready:
            return self._model_name
        if not quiet:
            print(f"Loading small LLM: {SMALL_LLM_MODEL}...")
        try:
            self._load_flan()
            self._ready = True
            if not quiet:
                print(f"Small LLM ready: {self._model_name}")
            return self._model_name
        except Exception as e:
            self._model_name = "rule-based (fleet KB)"
            if not quiet:
                print(f"Small LLM unavailable ({e}), using rule-based fallback")
            return self._model_name

    def _load_flan(self):
        if self._pipeline is not None:
            return
        import logging

        logging.getLogger("transformers").setLevel(logging.ERROR)
        from transformers import pipeline

        self._pipeline = pipeline(
            "text2text-generation",
            model=SMALL_LLM_MODEL,
            max_new_tokens=120,
        )
        self._model_name = SMALL_LLM_MODEL

    def _answer_flan(self, query: str) -> str | None:
        try:
            self._load_flan()
            prompt = (
                f"Fleet data: VH001 Tesla 55000, VH002 Ford 35000, VH003 BMW 45000, "
                f"VH004 Toyota 25000, VH005 Mercedes 65000. "
                f"Q: {query} A:"
            )
            result = self._pipeline(prompt, max_new_tokens=80, do_sample=False)
            text = result[0]["generated_text"].strip()
            if not text or len(text) < 8:
                return None
            if text.lower().startswith("you are") or "fleet analytics assistant" in text.lower():
                return None
            return text
        except Exception:
            return None

    def _check_ollama(self) -> bool:
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def _answer_ollama(self, query: str) -> str | None:
        if not self._check_ollama():
            return None
        payload = json.dumps(
            {
                "model": self._ollama_model,
                "prompt": (
                    f"You are a fleet analytics assistant.{FLEET_CONTEXT}\n"
                    f"User: {query}\nAssistant:"
                ),
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 150},
            }
        ).encode()
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                return data.get("response", "").strip()
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return None

    def _answer_rules(self, query: str) -> str:
        lower = query.lower()
        for key, answer in RULE_ANSWERS.items():
            if key in lower:
                return answer
        if any(w in lower for w in ("show", "list", "all", "records")):
            return (
                "Here are the fleet records: VH001 Tesla ($55k), VH002 Ford ($35k), "
                "VH003 BMW ($45k), VH004 Toyota ($25k), VH005 Mercedes ($65k)."
            )
        if "price" in lower or "cost" in lower:
            return "Fleet prices range from $25,000 (Toyota) to $65,000 (Mercedes)."
        return (
            "Based on our fleet data: VH001 Tesla, VH002 Ford, VH003 BMW, "
            "VH004 Toyota, VH005 Mercedes. Ask about a specific vehicle or maintenance."
        )

    def generate_answer(self, query: str) -> dict:
        """Generate answer for a SAFE query using the small LLM."""
        answer = self._answer_flan(query)
        if answer:
            return {"answer": answer, "model": self._model_name, "source": "small_llm"}

        answer = self._answer_ollama(query)
        if answer:
            return {
                "answer": answer,
                "model": f"Ollama/{self._ollama_model}",
                "source": "small_llm",
            }

        return {
            "answer": self._answer_rules(query),
            "model": "rule-based (fleet KB)",
            "source": "fallback",
        }


_responder = None


def get_llm_responder() -> SmallLLMResponder:
    global _responder
    if _responder is None:
        _responder = SmallLLMResponder()
    return _responder


if __name__ == "__main__":
    r = get_llm_responder()
    r.warm_up(quiet=False)
    for q in ["Show me all vehicle records", "What is the price of VH003?"]:
        out = r.generate_answer(q)
        print(f"\nQ: {q}")
        print(f"Model: {out['model']}")
        print(f"A: {out['answer']}")
