#!/usr/bin/env python3
"""
Database Migration Tool

Execute SQL migration files against configured databases.
Supports single migrations or entire directories.

Usage:
    python tools/run-migration.py --file sql/migrations/001_add_uuid_columns_staging.sql
    python tools/run-migration.py --dir sql/migrations --db UNIFIED_ORDERS
    python tools/run-migration.py --dir sql/migrations --pattern "00*_*.sql"

Examples:
    # Run single migration
    python tools/run-migration.py -f sql/migrations/001_add_uuid_columns_staging.sql

    # Run all migrations in directory
    python tools/run-migration.py -d sql/migrations

    # Run specific pattern with different database
    python tools/run-migration.py -d sql/migrations -p "001_*.sql" --db STAGING_DB
"""

import argparse
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from db_helper import run_migration, run_migrations_directory


def main():
    parser = argparse.ArgumentParser(
        description="Execute SQL migration files against configured databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Usage:')[1] if 'Usage:' in __doc__ else ""
    )
    
    # Migration source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '-f', '--file',
        type=str,
        help="Path to single migration file"
    )
    source_group.add_argument(
        '-d', '--dir', '--directory',
        type=str,
        help="Path to directory containing migration files"
    )
    
    # Database options
    parser.add_argument(
        '--db', '--database',
        type=str,
        default='UNIFIED_ORDERS',
        help="Database key from config.yaml (default: UNIFIED_ORDERS)"
    )
    
    # Directory-specific options
    parser.add_argument(
        '-p', '--pattern',
        type=str,
        default='*.sql',
        help="File pattern for directory migrations (default: *.sql)"
    )
    
    # Output options
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help="Suppress verbose output"
    )
    
    # Validation options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Validate files without executing (TODO: future feature)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to repo root
    repo_root = Path(__file__).parent.parent
    
    try:
        if args.file:
            # Single file migration
            migration_path = repo_root / args.file
            
            if not args.quiet:
                print(f"🔧 Running single migration")
                print(f"📁 File: {args.file}")
                print(f"📊 Database: {args.db}")
                print("=" * 60)
            
            success = run_migration(
                migration_path=migration_path,
                db_key=args.db,
                verbose=not args.quiet
            )
            
            if success:
                if not args.quiet:
                    print("\n🎉 Migration completed successfully!")
                sys.exit(0)
            else:
                if not args.quiet:
                    print("\n💥 Migration failed!")
                sys.exit(1)
        
        elif args.dir:
            # Directory migrations
            migrations_dir = repo_root / args.dir
            
            if not args.quiet:
                print(f"🔧 Running directory migrations")
                print(f"📁 Directory: {args.dir}")
                print(f"🔍 Pattern: {args.pattern}")
                print(f"📊 Database: {args.db}")
                print("=" * 60)
            
            results = run_migrations_directory(
                migrations_dir=migrations_dir,
                db_key=args.db,
                pattern=args.pattern,
                verbose=not args.quiet
            )
            
            if results['failed'] == 0:
                if not args.quiet:
                    print(f"\n🎉 All {results['successful']} migrations completed successfully!")
                sys.exit(0)
            else:
                if not args.quiet:
                    print(f"\n💥 {results['failed']} migrations failed!")
                    print("Failed migrations:")
                    for detail in results['details']:
                        if not detail['success']:
                            print(f"  ❌ {detail['file']}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Migration interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n💥 Migration tool error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
