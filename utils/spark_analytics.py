"""Apache Spark analytics helpers for query logging."""

from utils.spark_session import create_spark_session, setup_spark_env


def aggregate_with_spark(records: list) -> dict | None:
    """
    Run Spark aggregations on query log records.
    Returns analytics dict or None if Spark fails.
    """
    if not records:
        return None

    try:
        from pyspark.sql.functions import col
    except ImportError:
        return None

    setup_spark_env()
    spark = create_spark_session("SparkAnalytics")
    if spark is None:
        return None

    try:
        df = spark.createDataFrame(records)
        total = df.count()
        malicious = df.filter(col("is_malicious") == True).count()
        safe = total - malicious

        risk_breakdown = {}
        for risk_val in ("LOW", "MEDIUM", "HIGH"):
            cnt = df.filter(col("risk") == risk_val).count()
            if cnt:
                risk_breakdown[risk_val] = cnt

        recent_rows = (
            df.orderBy(col("timestamp").desc())
            .select("prompt", "is_malicious", "risk", "timestamp")
            .limit(5)
            .toLocalIterator()
        )
        recent_queries = [
            {
                "prompt": r["prompt"][:60] + ("..." if len(r["prompt"]) > 60 else ""),
                "malicious": bool(r["is_malicious"]),
                "risk": r["risk"],
                "time": r["timestamp"],
            }
            for r in recent_rows
        ]

        return {
            "total_queries": total,
            "malicious_count": malicious,
            "safe_count": safe,
            "block_rate": f"{(malicious / total * 100):.1f}%" if total else "0%",
            "risk_breakdown": risk_breakdown,
            "recent_queries": recent_queries,
            "engine": "Apache Spark (PySpark) — ACTIVE",
            "spark_active": True,
        }
    except Exception as exc:
        print(f"Spark analytics error: {exc}")
        return None
