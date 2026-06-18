#!/bin/bash
# Spark setup for security research demos

set -e

SPARK_VERSION="${SPARK_VERSION:-3.5.0}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/spark}"

echo "=== Spark ${SPARK_VERSION} Setup ==="

if [ ! -d "$INSTALL_DIR" ]; then
    echo "Downloading Spark ${SPARK_VERSION}..."
    wget -q "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz"
    tar -xzf "spark-${SPARK_VERSION}-bin-hadoop3.tgz"
    mv "spark-${SPARK_VERSION}-bin-hadoop3" "$INSTALL_DIR"
    rm "spark-${SPARK_VERSION}-bin-hadoop3.tgz"
fi

export SPARK_HOME="$INSTALL_DIR"
export PATH="$SPARK_HOME/bin:$PATH"
export PYSPARK_PYTHON=python3

echo "export SPARK_HOME=$INSTALL_DIR" >> ~/.bashrc
echo 'export PATH=$SPARK_HOME/bin:$PATH' >> ~/.bashrc
echo 'export PYSPARK_PYTHON=python3' >> ~/.bashrc

echo "=== Spark setup complete ==="
spark-submit --version 2>&1 | head -3
