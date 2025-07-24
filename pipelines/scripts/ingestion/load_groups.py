#!/usr/bin/env python3
"""
Fetch Monday.com Groups for a Board and Load to Database (With board_name)
==========================================================================

- Requires --board_id {id}
- Loads get-group.graphql via GraphQLLoader
- Calls Monday.com API (sync HTTP)
- Loads results into MON_Boards_Groups via db.execute
- Ensures table exists before inserting

"""

import sys, os, argparse, requests
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_NAME = "orders"  # <-- Update as needed

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
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db
from pipelines.utils import logger
from pipelines.integrations.monday.graphql_loader import GraphQLLoader

logger = logger.get_logger("fetch_groups")

try:
    from dotenv import load_dotenv
    # Load .env from repo root and .venv/.env if present
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".venv" / ".env")
except ImportError:
    pass

def get_api_key():
    key = os.getenv("MONDAY_API_KEY")
    if not key:
        logger.error("MONDAY_API_KEY environment variable not set")
        sys.exit(1)
    return key

def ensure_groups_table_exists():
    create_sql = """
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MON_Boards_Groups'
    )
    CREATE TABLE MON_Boards_Groups (
        board_id NVARCHAR(128),
        board_name NVARCHAR(255),
        group_id NVARCHAR(128),
        group_name NVARCHAR(255)
    );
    """
    try:
        db.execute(create_sql, DB_NAME)
        logger.info("Ensured MON_Boards_Groups table exists")
    except Exception as e:
        logger.error(f"Failed to create MON_Boards_Groups table: {e}")
        sys.exit(1)

def fetch_groups(board_id: str) -> list:
    api_key = get_api_key()
    api_url = "https://api.monday.com/v2"
    loader = GraphQLLoader()
    query = loader.get_query("get-group")

    payload = {
        "query": query,
        "variables": {"boardId": int(board_id)}
    }
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    resp = requests.post(api_url, json=payload, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Monday.com API HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)
    data = resp.json()
    if "errors" in data and data["errors"]:
        logger.error(f"Monday.com API error: {data['errors']}")
        sys.exit(1)
    try:
        board_data = data["data"]["boards"][0]
        board_id_out = board_data["id"]
        board_name = board_data["name"]
        groups = board_data["groups"]
        logger.info(f"Fetched {len(groups)} groups for board {board_id_out} ({board_name})")
        return [
            {
                "board_id": board_id_out,
                "board_name": board_name,
                "group_id": g["id"],
                "group_name": g["title"]
            } for g in groups
        ]
    except Exception as e:
        logger.error(f"Failed to parse API response: {e}")
        sys.exit(1)

def load_groups_to_db(groups: list):
    if not groups:
        logger.warning("No groups to load, skipping DB insert")
        return
    for g in groups:
        query = """
        MERGE MON_Boards_Groups AS target
        USING (SELECT ? AS board_id, ? AS board_name, ? AS group_id, ? AS group_name) AS source
            ON target.group_id = source.group_id
        WHEN MATCHED THEN
            UPDATE SET 
                board_id = source.board_id,
                board_name = source.board_name,
                group_name = source.group_name
        WHEN NOT MATCHED THEN
            INSERT (board_id, board_name, group_id, group_name)
            VALUES (source.board_id, source.board_name, source.group_id, source.group_name);
        """
        params = (g["board_id"], g["board_name"], g["group_id"], g["group_name"])
        try:
            db.execute(query, DB_NAME, params=params)
            logger.info(f"Upserted group {g['group_id']}: {g['group_name']}")
        except Exception as e:
            logger.error(f"DB upsert failed for group {g['group_id']}: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Fetch Monday.com Groups for Board and Load to DB")
    parser.add_argument("--board_id", required=True, help="Monday.com Board ID")
    args = parser.parse_args()

    logger.info(f"Starting group fetch/load for board {args.board_id}")
    ensure_groups_table_exists()
    groups = fetch_groups(args.board_id)
    load_groups_to_db(groups)
    logger.info("All groups loaded successfully.")

if __name__ == "__main__":
    main()
