#!/usr/bin/env python3
"""
Big Data Security Chatbot Engine
Simple pipeline: Mirror Detector + P2SQL + Keyword check + Spark logging.
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from defense.utdmf_defense import UTDMFDefense
from defense.llm_responder import get_llm_responder
from utils.spark_analytics import aggregate_with_spark
from utils.spark_session import create_spark_session

LOG_DIR = os.path.join(PROJECT_ROOT, "data", "query_logs")
LOG_FILE = os.path.join(LOG_DIR, "queries.jsonl")


class ChatbotSecurityEngine:
    """Prompt injection detector with Spark-backed query analytics."""

    SQL_TRIGGERS = re.compile(
        r"\b(show|list|select|drop|delete|table|records|vehicles|database|query|truncate|insert|update|export|dump)\b",
        re.IGNORECASE,
    )

    def __init__(self):
        self.defense = UTDMFDefense()
        self.spark = create_spark_session("SecurityChatbot")
        self.spark_active = self.spark is not None
        os.makedirs(LOG_DIR, exist_ok=True)
        self._memory_log = []

    def _get_spark(self):
        if self.spark is None:
            self.spark = create_spark_session("SecurityChatbot")
            self.spark_active = self.spark is not None
        return self.spark

    def _simulate_sql_from_prompt(self, prompt: str) -> str:
        lower = prompt.lower()
        if "drop" in lower and "table" in lower:
            return "DROP TABLE vehicles;"
        if "delete" in lower:
            return "DELETE FROM vehicles WHERE price > 0;"
        if any(w in lower for w in ("show", "list", "records", "vehicles")):
            return "SELECT * FROM vehicles"
        return f"-- Unable to parse: {prompt[:80]}"

    def _is_database_query(self, prompt: str) -> bool:
        """Only run P2SQL check when prompt looks like a data/SQL request."""
        return bool(self.SQL_TRIGGERS.search(prompt))

    def _build_block_reasons(self, record: dict, mirror: dict, sql_msg: str, sql_checked: bool) -> list:
        reasons = []
        if mirror["is_malicious"]:
            reasons.append({
                "layer": "Mirror Detector",
                "status": "BLOCKED",
                "reason": (
                    f"Prompt injection detected — confidence {mirror['confidence']:.1%}, "
                    f"risk level {mirror['risk']}"
                ),
            })
        else:
            reasons.append({
                "layer": "Mirror Detector",
                "status": "PASSED",
                "reason": "No prompt injection pattern found",
            })

        if sql_checked:
            if record["sql_allowed"]:
                reasons.append({
                    "layer": "P2SQL Check",
                    "status": "PASSED",
                    "reason": f"SQL is safe: {record['simulated_sql']}",
                })
            else:
                reasons.append({
                    "layer": "P2SQL Check",
                    "status": "BLOCKED",
                    "reason": sql_msg,
                })
        else:
            reasons.append({
                "layer": "P2SQL Check",
                "status": "SKIPPED",
                "reason": "General chat — not a database query, SQL check skipped",
            })

        if record["keyword_hits"]:
            reasons.append({
                "layer": "Keyword Scanner",
                "status": "BLOCKED",
                "reason": f"Suspicious keywords found: {', '.join(record['keyword_hits'])}",
            })
        else:
            reasons.append({
                "layer": "Keyword Scanner",
                "status": "PASSED",
                "reason": "No suspicious keywords",
            })

        return reasons

    def analyze(self, user_prompt: str, scan_type: str = "prompt") -> dict:
        prompt = user_prompt.strip()
        if not prompt:
            return {"error": "Empty input"}

        mirror = self.defense.scan_prompt(prompt)
        simulated_sql = self._simulate_sql_from_prompt(prompt)
        sql_checked = self._is_database_query(prompt)
        if sql_checked:
            sql_ok, sql_msg = self.defense.validate_sql(simulated_sql)
        else:
            sql_ok, sql_msg = True, "Skipped — general chat, not a database query"

        keyword_hits = []
        for pattern in (
            "ignore previous",
            "system override",
            "admin mode",
            "reveal all",
            "drop table",
            "delete from",
        ):
            if pattern in prompt.lower():
                keyword_hits.append(pattern)

        blocked = mirror["is_malicious"] or not sql_ok
        threats = []
        if mirror["is_malicious"]:
            threats.append(f"Prompt injection detected (risk: {mirror['risk']})")
        if not sql_ok:
            threats.append(sql_msg)
        if keyword_hits:
            threats.append(f"Suspicious keywords: {', '.join(keyword_hits)}")

        record = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "scan_type": scan_type,
            "is_malicious": bool(mirror["is_malicious"]),
            "confidence": float(round(mirror["confidence"], 4)),
            "risk": str(mirror["risk"]),
            "blocked": bool(blocked),
            "simulated_sql": simulated_sql,
            "sql_allowed": bool(sql_ok),
            "sql_checked": sql_checked,
            "keyword_hits": keyword_hits,
            "threats": threats,
        }

        block_reasons = self._build_block_reasons(record, mirror, sql_msg, sql_checked)

        self._log_query(record)
        response = self._build_response(record, prompt, block_reasons)
        response["pipeline_steps"] = self._build_pipeline_steps(record, prompt)

        if not record["blocked"]:
            llm = get_llm_responder().generate_answer(prompt)
            response["llm_answer"] = llm["answer"]
            response["llm_model"] = llm["model"]
            response["message"] = llm["answer"]
            response["pipeline_steps"].append(
                {
                    "id": 6,
                    "name": "Small LLM Answer",
                    "icon": "LLM",
                    "status": "success",
                    "detail": f"Small LLM ({llm['model']}) answered safe query",
                }
            )
        else:
            response["llm_answer"] = None
            response["security_score"] = self._security_score(record, block_reasons)
            response["block_reasons"] = block_reasons
            response["pipeline_steps"].append(
                {
                    "id": 6,
                    "name": "LLM Blocked",
                    "icon": "BLOCK",
                    "status": "blocked",
                    "detail": "; ".join(
                        r["reason"] for r in block_reasons if r["status"] == "BLOCKED"
                    ) or "Malicious prompt blocked",
                }
            )
        return response

    def _build_pipeline_steps(self, record: dict, prompt: str) -> list:
        return [
            {
                "id": 1,
                "name": "User Prompt",
                "icon": "IN",
                "status": "success",
                "detail": prompt[:80] + ("..." if len(prompt) > 80 else ""),
            },
            {
                "id": 2,
                "name": "Mirror Detector",
                "icon": "SCAN",
                "status": "danger" if record["is_malicious"] else "success",
                "detail": (
                    f"Malicious={record['is_malicious']}, "
                    f"Confidence={record['confidence']:.1%}, Risk={record['risk']}"
                ),
            },
            {
                "id": 3,
                "name": "P2SQL Check",
                "icon": "SQL",
                "status": "success" if record["sql_allowed"] else "danger",
                "detail": (
                    record["simulated_sql"]
                    if record.get("sql_checked")
                    else "Skipped — general chat"
                ),
            },
            {
                "id": 4,
                "name": "Spark Log",
                "icon": "SPARK",
                "status": "success" if self.spark_active else "warning",
                "detail": f"Query ID: {record['id']}",
            },
            {
                "id": 5,
                "name": "Verdict",
                "icon": "DONE",
                "status": "danger" if record["blocked"] else "success",
                "detail": "BLOCKED" if record["blocked"] else "SAFE",
            },
        ]

    def _security_score(self, record: dict, block_reasons: list) -> dict:
        conf = record["confidence"]
        risk = record["risk"]
        score = min(100, int(conf * 100) + (40 if risk == "HIGH" else 20 if risk == "MEDIUM" else 10))
        failed = [r for r in block_reasons if r["status"] == "BLOCKED"]
        return {
            "threat_score": score,
            "verdict": "BLOCKED",
            "confidence": f"{conf:.1%}",
            "risk_level": risk,
            "mirror_detection": "MALICIOUS" if record["is_malicious"] else "CLEAN",
            "sql_injection_check": "BLOCKED" if not record["sql_allowed"] and record.get("sql_checked") else "PASSED",
            "simulated_sql": record["simulated_sql"],
            "keyword_hits": record["keyword_hits"],
            "threats_detected": record["threats"],
            "block_reasons": block_reasons,
            "why_blocked": [r["reason"] for r in failed] or record["threats"],
            "layers_triggered": len(failed),
        }

    def _build_response(self, record: dict, prompt: str, block_reasons: list) -> dict:
        if record["blocked"]:
            verdict, message, color = (
                "MALICIOUS",
                "BLOCKED: Attack detected. LLM answer withheld.",
                "danger",
            )
        else:
            verdict, message, color = (
                "SAFE",
                "Query passed checks. Generating answer...",
                "safe",
            )

        return {
            "verdict": verdict,
            "message": message,
            "color": color,
            "llm_answer": None,
            "llm_model": None,
            "security_score": None,
            "block_reasons": block_reasons,
            "details": {
                "malicious": record["is_malicious"],
                "confidence": f"{record['confidence']:.1%}",
                "risk_level": record["risk"],
                "blocked": record["blocked"],
                "simulated_sql": record["simulated_sql"],
                "sql_status": "allowed" if record["sql_allowed"] else "blocked",
                "keyword_hits": record["keyword_hits"],
                "threats": record["threats"],
            },
            "big_data": {
                "pipeline": "Prompt -> Mirror -> P2SQL -> Spark -> Verdict",
                "query_id": record["id"],
                "processed_by": (
                    "Apache Spark (PySpark) + UTDMF"
                    if self.spark_active
                    else "UTDMF + JSONL Log"
                ),
                "spark_active": self.spark_active,
            },
        }

    def _log_query(self, record: dict):
        self._memory_log.append(record)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        spark = self._get_spark()
        if spark:
            try:
                spark.createDataFrame([record]).count()
            except Exception:
                pass

    def get_analytics(self) -> dict:
        records = self._load_all_records()
        if not records:
            return {
                "total_queries": 0,
                "malicious_count": 0,
                "safe_count": 0,
                "block_rate": "0%",
                "risk_breakdown": {},
                "recent_queries": [],
                "engine": (
                    "Apache Spark (PySpark) — ACTIVE"
                    if self.spark_active
                    else "Waiting for queries..."
                ),
                "spark_active": self.spark_active,
            }

        spark_result = aggregate_with_spark(records)
        if spark_result:
            spark_result["spark_active"] = True
            return spark_result

        total = len(records)
        malicious = sum(1 for r in records if r.get("is_malicious"))
        recent_queries = [
            {
                "prompt": r["prompt"][:60] + ("..." if len(r["prompt"]) > 60 else ""),
                "malicious": r["is_malicious"],
                "risk": r["risk"],
                "time": r["timestamp"],
            }
            for r in reversed(records[-5:])
        ]
        risk_breakdown = {}
        for r in records:
            risk = r.get("risk", "LOW")
            risk_breakdown[risk] = risk_breakdown.get(risk, 0) + 1

        return {
            "total_queries": total,
            "malicious_count": malicious,
            "safe_count": total - malicious,
            "block_rate": f"{(malicious / total * 100):.1f}%" if total else "0%",
            "risk_breakdown": risk_breakdown,
            "recent_queries": recent_queries,
            "engine": "Apache Spark (PySpark) — ACTIVE" if self.spark_active else "JSONL Analytics",
            "spark_active": self.spark_active,
        }

    def _load_all_records(self) -> list:
        if not os.path.exists(LOG_FILE):
            return list(self._memory_log)
        records = []
        with open(LOG_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records


_engine = None


def get_engine() -> ChatbotSecurityEngine:
    global _engine
    if _engine is None:
        _engine = ChatbotSecurityEngine()
    return _engine
