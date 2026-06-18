"""Cross-platform Spark session helper for Windows/Linux demos."""

import os
import sys
import tempfile


def setup_spark_env():
    """Configure environment variables for PySpark on Windows."""
    python_exe = sys.executable
    os.environ["PYSPARK_PYTHON"] = python_exe
    os.environ["PYSPARK_DRIVER_PYTHON"] = python_exe

    if sys.platform != "win32":
        return

    hadoop_home = os.path.join(tempfile.gettempdir(), "hadoop_win")
    bin_dir = os.path.join(hadoop_home, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    os.environ.setdefault("HADOOP_HOME", hadoop_home)
    os.environ.setdefault("hadoop.home.dir", hadoop_home)
    os.environ.setdefault("HADOOP_USER_NAME", os.environ.get("USERNAME", "sparkuser"))


def java_compat_opts():
    """JVM flags for newer Java versions (17+) with Spark/Hadoop."""
    return (
        "--add-opens=java.base/java.lang=ALL-UNNAMED "
        "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
        "--add-opens=java.base/java.util=ALL-UNNAMED "
        "--add-opens=java.base/java.security=ALL-UNNAMED "
        "--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED"
    )


def create_spark_session(app_name, master="local[1]"):
    """
    Create a SparkSession with Windows-safe defaults.
    Returns None if Spark cannot start (e.g. Java 25 compatibility issues).
    """
    setup_spark_env()

    warehouse = os.path.join(tempfile.gettempdir(), "spark-warehouse")
    os.makedirs(warehouse, exist_ok=True)

    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        .config("spark.sql.warehouse.dir", warehouse.replace("\\", "/"))
        .config("spark.driver.extraJavaOptions", java_compat_opts())
        .config("spark.executor.extraJavaOptions", java_compat_opts())
        .config("spark.hadoop.hadoop.security.authentication", "simple")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.default.parallelism", "1")
    )

    try:
        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("ERROR")
        return spark
    except Exception as exc:
        print(f"Spark unavailable: {exc}")
        print("Continuing in simulation mode (no live Spark session).")
        return None
