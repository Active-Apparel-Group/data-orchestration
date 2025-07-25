#!/usr/bin/env python3
"""
Database Migration Tool

This tool executes SQL migration scripts using the project's db_helper configuration.
It supports running single migrations or entire directories of migrations.

Usage:
    python tools/run_migration.py path/to/migration.sql
    python tools/run_migration.py sql/migrations/
    python tools/run_migration.py sql/migrations/ --db ORDERS --pattern "*.sql"

Features:
- Uses db_helper.py for consistent database connections
- Supports single file or directory migrations
- Alphabetical ordering for directory migrations
- Verbose output with progress tracking
- Error handling and rollback
"""

import sys
import argparse
from pathlib import Path

# Add src/pipelines/utils to path for modern package structure
src_utils_path = Path(__file__).parent.parent / "src" / "pipelines" / "utils"
sys.path.insert(0, str(src_utils_path))

# Import from modern package structure
from db import get_connection, load_config
from logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Add legacy path for db_helper functions
pipelines_utils_path = Path(__file__).parent.parent / "pipelines" / "utils"
sys.path.insert(0, str(pipelines_utils_path))
import db_helper

def main():
    parser = argparse.ArgumentParser(
        description="Execute SQL migration scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a single migration
  python tools/run_migration.py sql/migrations/001_add_uuid_columns_staging.sql
  
  # Run all migrations in a directory
  python tools/run_migration.py sql/migrations/
  
  # Run migrations with specific database
  python tools/run_migration.py sql/migrations/ --db ORDERS
  
  # Run migrations with pattern matching
  python tools/run_migration.py sql/migrations/ --pattern "001_*.sql"
        """
    )
    
    parser.add_argument(
        'path',
        help='Path to migration file or directory'
    )
    
    parser.add_argument(
        '--db', '--database',
        default='ORDERS',
        help='Database key from config.yaml (default: UNIFIED_ORDERS)'
    )
    
    parser.add_argument(
        '--pattern',
        default='*.sql',
        help='File pattern for directory migrations (default: *.sql)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress verbose output'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate migration files without executing them'
    )
    
    parser.add_argument(
        '--show-results',
        action='store_true',
        help='Display query results as DataFrames'
    )
    
    parser.add_argument(
        '--max-rows',
        type=int,
        default=20,
        help='Maximum rows to display when --show-results is used (default: 20)'
    )
    
    args = parser.parse_args()
    
    migration_path = Path(args.path)
    verbose = not args.quiet
    
    if verbose:
        print("🔧 Database Migration Tool")
        print("=" * 50)
        print(f"📁 Path: {migration_path}")
        print(f"🗄️  Database: {args.db}")
        
        if args.validate_only:
            print("🔍 Mode: Validation Only")
        else:
            print("🚀 Mode: Execute")
        print("=" * 50)
    
    # Validation mode
    if args.validate_only:
        if migration_path.is_file():
            if migration_path.exists() and migration_path.suffix == '.sql':
                print(f"✅ Valid migration file: {migration_path}")
                return 0
            else:
                print(f"❌ Invalid migration file: {migration_path}")
                return 1
        elif migration_path.is_dir():
            migration_files = sorted(migration_path.glob(args.pattern))
            if migration_files:
                print(f"✅ Found {len(migration_files)} migration files:")
                for f in migration_files:
                    print(f"   - {f.name}")
                return 0
            else:
                print(f"❌ No migration files found with pattern: {args.pattern}")
                return 1
        else:
            print(f"❌ Path does not exist: {migration_path}")
            return 1
    
    # Execution mode
    try:
        if migration_path.is_file():
            # Single migration file
            if args.show_results:
                # Use run_query for results display
                success = db_helper.run_query_with_display(
                    migration_path=migration_path,
                    db_key=args.db,
                    max_rows=args.max_rows,
                    verbose=verbose
                )
            else:
                # Use run_migration for execution without results
                success = db_helper.run_migration(
                    migration_path=migration_path,
                    db_key=args.db,
                    verbose=verbose
                )
            
            return 0 if success else 1
            
        elif migration_path.is_dir():
            # Directory of migrations
            results = db_helper.run_migrations_directory(
                migrations_dir=migration_path,
                db_key=args.db,
                pattern=args.pattern,
                verbose=verbose
            )
            
            return 0 if results['failed'] == 0 else 1
            
        else:
            print(f"❌ Path does not exist: {migration_path}")
            return 1
            
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
