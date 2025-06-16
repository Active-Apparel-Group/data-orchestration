FROM kestra/kestra:latest

USER root

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive
ENV ACCEPT_EULA=Y

# Clean package cache and update
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Install prerequisites
RUN apt-get update -y && \
    apt-get install -y \
    python3-pip \
    curl \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository and key
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/ubuntu/20.04/prod focal main" > /etc/apt/sources.list.d/mssql-release.list

# Update package lists and install ODBC driver
RUN apt-get update && \
    apt-get install -y msodbcsql17 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

USER kestra