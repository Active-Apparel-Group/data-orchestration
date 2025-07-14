"""
Blob Auth Test Script
Purpose: Authenticate to Azure Blob Storage using environment variables and show connection status.
"""

import os
import sys
from pathlib import Path

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

# --- repo utils path setup ----------------------------------------------------
def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with utils/ folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

try:
    from dotenv import load_dotenv
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".venv" / ".env")
except ImportError:
    pass

# ---------------- ENV VARIABLES -------------------------------
TENANT_ID     = os.getenv('AZ_TENANT_ID') or "{{ secret('AZ_TENANT_ID') }}"
CLIENT_ID     = os.getenv('BLOB_CLIENT_ID') or "{{ secret('BLOB_CLIENT_ID') }}"
CLIENT_SECRET = os.getenv('BLOB_CLIENT_SECRET') or "{{ secret('BLOB_CLIENT_SECRET') }}"
ACCOUNT_NAME  = os.getenv('BLOB_ACCOUNT_NAME') or "{{ secret('BLOB_ACCOUNT_NAME') }}"

def main():
    print("Authenticating to Azure Blob Storage...")
    try:
        credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        blob_svc = BlobServiceClient(
            account_url=f"https://{ACCOUNT_NAME}.blob.core.windows.net",
            credential=credential,
        )
        print("✅ Authentication successful!")
        print(f"BlobServiceClient: {blob_svc}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")

if __name__ == "__main__":
    main()