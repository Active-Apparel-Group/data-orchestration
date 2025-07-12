"""
ORDER_LIST Extract Layer - Milestone 1
Purpose: Optimized blob storage extraction to raw landing tables
Author: Data Engineering Team
Date: July 8, 2025

Features:
- SQL Server-native bulk loading using executemany() for performance
- Minimal transformation - raw data landing only
- Comprehensive error handling and logging
- Schema discovery and column normalization using schema_helper
- Parallel processing for multiple files
- Proper SQL Server table existence checks (no SQLite dependencies)
"""

import sys
import os
from pathlib import Path
import pandas as pd
import re
import io
import time
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import warnings

# Azure imports
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

# Hide irrelevant openpyxl warnings
warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists() and (current / "integrations").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root (needs both utils and integrations folders)")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper
import schema_helper

# Copy the full OrderListExtractor class and main() from the previous extract script here.
from dev.order_list.order_list_extract import OrderListExtractor

def main():
    OrderListExtractor.main()

if __name__ == "__main__":
    main()
