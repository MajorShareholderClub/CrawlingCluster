# 기존의 이미지 베이스로부터 시작
FROM apache/airflow:2.8.1-python3.11

# Switch to the Airflow user
USER root

# Install necessary packages and set timezone
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    g++ \
    git \
    curl \
    openjdk-17-jre-headless \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64

# Switch back to the Airflow user
USER airflow

# Copy and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
