#!/usr/bin/env python3
"""
Debug connection configuration for INFOR_134
"""
import os
import sys
sys.path.insert(0, 'src')

# Load the .env file first
from dotenv import load_dotenv
load_dotenv('.env')

from audit_pipeline.config import get_db_config

# Test INFOR_134 config
print('=== INFOR_134 CONFIG ===')
config = get_db_config('INFOR_134')
for key, value in config.items():
    print(f'{key}: {value}')

print()
print('=== CONNECTION STRING ===')
conn_str = (
    f"DRIVER={{SQL Server}};SERVER={config['host']},{config['port']};"
    f"DATABASE={config['database']};UID={config['username']};PWD={config['password']};"
    f"Encrypt={config['encrypt']};TrustServerCertificate={config['trustServerCertificate']};"
)
print(conn_str)

print()
print('=== GFS CONFIG (for comparison) ===')
config_gfs = get_db_config('GFS')
for key, value in config_gfs.items():
    print(f'{key}: {value}')
