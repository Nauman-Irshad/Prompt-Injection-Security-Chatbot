#!/usr/bin/env python3
"""Run all attack and defense demonstrations."""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEMOS = [
    ("CVE-2022-25168 Command Injection", "attacks/command_injection/cve_2022_25168_demo.py"),
    ("SPARK-50239 JavaOptions Injection", "attacks/command_injection/spark_50239_demo.py"),
    ("RAG Poisoning", "attacks/prompt_injection/rag_poisoning.py"),
    ("PIDP Attack", "attacks/prompt_injection/pidp_attack.py"),
    ("P2SQL Attack", "attacks/prompt_injection/p2sql_attack.py"),
    ("Combined Attack Chain", "attacks/combined_attacks/chain_attack.py"),
    ("CleanBase Detector", "defense/cleanbase_detector.py"),
    ("Mirror Detector", "defense/mirror_detector.py"),
    ("UTDMF Defense", "defense/utdmf_defense.py"),
    ("Mitigation Tests", "attacks/combined_attacks/mitigation_test.py"),
]


def main():
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)

    print("=" * 70)
    print("  PROMPT INJECTION & COMMAND INJECTION - FULL DEMO SUITE")
    print("=" * 70)

    for name, script in DEMOS:
        print(f"\n{'#' * 70}")
        print(f"  RUNNING: {name}")
        print(f"{'#' * 70}\n")
        script_path = os.path.join(PROJECT_ROOT, script)
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=PROJECT_ROOT,
                timeout=180,
            )
            if result.returncode != 0:
                print(f"\nWarning: {name} exited with code {result.returncode}")
        except subprocess.TimeoutExpired:
            print(f"\nWarning: {name} timed out after 180s — skipping")

    print("\n" + "=" * 70)
    print("  ALL DEMOS COMPLETE")
    print("  Verify:  python verify_project.py")
    print("  Chatbot: python run_chatbot.py  ->  http://localhost:5000")
    print("  Manual:  see MANUAL.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
