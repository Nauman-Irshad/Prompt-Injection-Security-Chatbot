#!/bin/bash
# Hadoop pseudo-distributed setup for security research demos
# Requires: Java 8+, Ubuntu/WSL recommended

set -e

HADOOP_VERSION="${HADOOP_VERSION:-3.3.6}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/hadoop}"

echo "=== Hadoop ${HADOOP_VERSION} Setup ==="

if ! command -v java &> /dev/null; then
    echo "Java not found. Install OpenJDK 8 or 11 first."
    exit 1
fi

if [ ! -d "$INSTALL_DIR" ]; then
    echo "Downloading Hadoop ${HADOOP_VERSION}..."
    wget -q "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz"
    tar -xzf "hadoop-${HADOOP_VERSION}.tar.gz"
    mv "hadoop-${HADOOP_VERSION}" "$INSTALL_DIR"
    rm "hadoop-${HADOOP_VERSION}.tar.gz"
fi

export HADOOP_HOME="$INSTALL_DIR"
export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"

echo "export HADOOP_HOME=$INSTALL_DIR" >> ~/.bashrc
echo 'export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH' >> ~/.bashrc

echo "Formatting HDFS namenode..."
hdfs namenode -format -force 2>/dev/null || true

echo "Starting HDFS and YARN..."
start-dfs.sh
start-yarn.sh

echo "=== Hadoop setup complete ==="
echo "Verify with: jps"
jps
