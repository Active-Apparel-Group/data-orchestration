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

def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # pipelines/utils ONLY

import db_helper as db
import logger_helper
import schema_helper

# Copy the full OrderListExtractor class and main() from the previous extract script here.
from dev.order_list.order_list_extract import OrderListExtractor

def main():
    OrderListExtractor.main()

if __name__ == "__main__":
    main()
