#!/usr/bin/env python3
"""
Monday.com Board CLI - Command-line interface for the Dynamic Board Template System

This CLI provides a user-friendly interface for managing Monday.com board configurations,
deployments, and operations using the Dynamic Board Template System.

Usage:
    python monday_board_cli.py deploy --board-id 12345 --board-name "Customer Orders" --table-name "MON_CustomerOrders"
    python monday_board_cli.py list
    python monday_board_cli.py status --board-id 12345
    python monday_board_cli.py update --board-id 12345
    python monday_board_cli.py remove --board-id 12345

Commands:
    deploy    Deploy a new Monday.com board
    list      List all registered boards
    status    Show status of a specific board
    update    Update an existing board configuration
    remove    Remove a board from the registry
    summary   Show deployment summary
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
import logging

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from board_schema_generator import BoardSchemaGenerator, discover_and_generate_schema
    from script_template_generator import ScriptTemplateGenerator, generate_script_from_schema
    from board_registry import BoardRegistry, BoardConfig
except ImportError as e:
    print(f"❌ Failed to import core modules: {e}")
    print("Please ensure all core modules are available in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MondayBoardCLI:
    """Command-line interface for Monday.com board management"""
    
    def __init__(self):
        self.registry = BoardRegistry()
        self.schema_generator = BoardSchemaGenerator()
        self.script_generator = ScriptTemplateGenerator()
    
    def deploy_board(self, args):
        """Deploy a new Monday.com board"""
        board_id = args.board_id
        board_name = args.board_name
        table_name = args.table_name
        database = args.database
        force = args.force
        
        print(f"🚀 Deploying Monday.com Board: {board_name} (ID: {board_id})")
        print(f"📋 Target: {database}.dbo.{table_name}")
        print("=" * 60)
        
        try:
            # Step 1: Discover board schema
            print("🔍 Step 1: Discovering board schema...")
            board_schema = self.schema_generator.discover_board_structure(board_id)
            
            # Override table name and database if provided
            if table_name:
                board_schema.table_name = table_name
            if database:
                board_schema.database = database
            
            print(f"   ✅ Discovered {len(board_schema.columns)} columns")
            
            # Step 2: Generate and execute DDL
            if args.skip_ddl:
                print("⏭️ Step 2: Skipping DDL execution (--skip-ddl)")
            else:
                print("🗄️ Step 2: Generating and executing DDL...")
                ddl = self.schema_generator.generate_sql_schema(board_schema)
                
                if args.dry_run:
                    print("   🔍 DRY RUN - DDL would be:")
                    print(ddl[:500] + "..." if len(ddl) > 500 else ddl)
                else:
                    self.schema_generator.execute_ddl(ddl, database)
                    print("   ✅ DDL executed successfully")
            
            # Step 3: Generate extraction script
            print("🐍 Step 3: Generating extraction script...")
            script_config = {
                "batch_size": args.batch_size,
                "max_workers": args.max_workers
            }
            script_path = generate_script_from_schema(board_schema, script_config=script_config)
            print(f"   ✅ Generated script: {script_path}")
            
            # Step 4: Generate workflow
            print("🔄 Step 4: Generating Kestra workflow...")
            workflow_content = self.script_generator.generate_workflow_config(board_schema)
            
            # Save workflow
            workflow_dir = Path(__file__).parent.parent / "generated"
            workflow_path = workflow_dir / f"workflow_{board_schema.board_name.lower().replace(' ', '_')}.yml"
            with open(workflow_path, 'w', encoding='utf-8') as f:
                f.write(workflow_content)
            print(f"   ✅ Generated workflow: {workflow_path}")
            
            # Step 5: Save metadata and register board
            print("📊 Step 5: Registering board...")
            metadata_path = self.schema_generator.save_board_metadata(board_schema)
            
            # Register in registry
            board_config = self.registry.register_board(board_schema, force=force)
            
            # Update deployment status
            status_updates = {
                "ddl_deployed": not args.skip_ddl and not args.dry_run,
                "script_generated": True,
                "workflow_created": True,
                "last_deployment": datetime.now()
            }
            self.registry.update_board_status(board_id, status_updates)
            
            # Update file paths
            board_config.metadata_path = str(metadata_path)
            board_config.script_path = str(script_path)
            board_config.workflow_path = str(workflow_path)
            
            print(f"   ✅ Registered board in registry")
            
            print("=" * 60)
            print("🎉 BOARD DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print(f"📊 Board: {board_schema.board_name} (ID: {board_id})")
            print(f"🗄️ Table: {database}.dbo.{board_schema.table_name}")
            print(f"📄 Metadata: {metadata_path}")
            print(f"🐍 Script: {script_path}")
            print(f"🔄 Workflow: {workflow_path}")
            
            if args.dry_run:
                print("\n⚠️ This was a DRY RUN - no DDL was executed")
            
        except Exception as e:
            print("=" * 60)
            print(f"❌ DEPLOYMENT FAILED: {e}")
            logger.error(f"Deployment failed: {e}")
            return 1
        
        return 0
    
    def list_boards(self, args):
        """List all registered boards"""
        boards = self.registry.list_all_boards()
        
        if not boards:
            print("📋 No boards registered in the system.")
            return 0
        
        print(f"📋 Registered Monday.com Boards ({len(boards)} total)")
        print("=" * 80)
        
        for board in boards:
            status = board.deployment_status
            status_icon = "🟢" if all([status.ddl_deployed, status.script_generated, status.workflow_created]) else "🟡"
            
            print(f"{status_icon} {board.board_name} (ID: {board.board_id})")
            print(f"   📊 Table: {board.database}.dbo.{board.table_name}")
            print(f"   📅 Created: {board.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   🔄 Updated: {board.updated_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   ✅ DDL: {'Yes' if status.ddl_deployed else 'No'} | " + 
                  f"Script: {'Yes' if status.script_generated else 'No'} | " + 
                  f"Workflow: {'Yes' if status.workflow_created else 'No'}")
            
            if status.last_successful_run:
                print(f"   🎯 Last Run: {status.last_successful_run.strftime('%Y-%m-%d %H:%M')}")
            
            print()
        
        return 0
    
    def show_status(self, args):
        """Show detailed status of a specific board"""
        board_config = self.registry.get_board_config(args.board_id)
        
        if not board_config:
            print(f"❌ Board {args.board_id} not found in registry")
            return 1
        
        status = board_config.deployment_status
        
        print(f"📊 Board Status: {board_config.board_name} (ID: {board_config.board_id})")
        print("=" * 60)
        print(f"📋 Table: {board_config.database}.dbo.{board_config.table_name}")
        print(f"📅 Created: {board_config.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔄 Updated: {board_config.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 Schema Version: {board_config.schema_version}")
        print()
        
        print("🚀 Deployment Status:")
        print(f"   DDL Deployed: {'✅ Yes' if status.ddl_deployed else '❌ No'}")
        print(f"   Script Generated: {'✅ Yes' if status.script_generated else '❌ No'}")
        print(f"   Workflow Created: {'✅ Yes' if status.workflow_created else '❌ No'}")
        
        if status.last_deployment:
            print(f"   Last Deployment: {status.last_deployment.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if status.last_successful_run:
            print(f"   Last Successful Run: {status.last_successful_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if status.deployment_errors:
            print(f"   ⚠️ Errors: {len(status.deployment_errors)}")
            for error in status.deployment_errors[-3:]:  # Show last 3 errors
                print(f"      • {error}")
        
        print()
        
        # File paths
        if board_config.metadata_path:
            print(f"📄 Metadata: {board_config.metadata_path}")
        if board_config.script_path:
            print(f"🐍 Script: {board_config.script_path}")
        if board_config.workflow_path:
            print(f"🔄 Workflow: {board_config.workflow_path}")
        
        return 0
    
    def update_board(self, args):
        """Update an existing board configuration"""
        board_id = args.board_id
        force = args.force
        
        print(f"🔄 Updating board configuration for ID: {board_id}")
        
        board_config = self.registry.get_board_config(board_id)
        if not board_config:
            print(f"❌ Board {board_id} not found in registry")
            return 1
        
        try:
            # Re-discover schema
            print("🔍 Re-discovering board schema...")
            board_schema = self.schema_generator.discover_board_structure(board_id)
            board_schema.table_name = board_config.table_name
            board_schema.database = board_config.database
            
            # Regenerate script
            print("🐍 Regenerating extraction script...")
            script_path = generate_script_from_schema(board_schema)
            
            # Update metadata
            print("📊 Updating metadata...")
            metadata_path = self.schema_generator.save_board_metadata(board_schema)
            
            # Update registry
            self.registry.update_board_status(board_id, {
                "script_generated": True,
                "last_deployment": datetime.now()
            })
            
            print("✅ Board update completed successfully!")
            return 0
            
        except Exception as e:
            print(f"❌ Update failed: {e}")
            return 1
    
    def remove_board(self, args):
        """Remove a board from the registry"""
        board_id = args.board_id
        confirm = args.confirm
        
        board_config = self.registry.get_board_config(board_id)
        if not board_config:
            print(f"❌ Board {board_id} not found in registry")
            return 1
        
        if not confirm:
            response = input(f"⚠️ Remove board '{board_config.board_name}' (ID: {board_id})? [y/N]: ")
            if response.lower() != 'y':
                print("❌ Operation cancelled")
                return 1
        
        try:
            self.registry.remove_board(board_id)
            print(f"✅ Removed board '{board_config.board_name}' from registry")
            print("⚠️ Note: Generated files (DDL, scripts, workflows) were not deleted")
            return 0
            
        except Exception as e:
            print(f"❌ Removal failed: {e}")
            return 1
    
    def show_summary(self, args):
        """Show deployment summary"""
        summary = self.registry.get_deployment_summary()
        
        print("📊 Monday.com Board Deployment Summary")
        print("=" * 40)
        print(f"Total Boards: {summary['total_boards']}")
        
        if summary['total_boards'] > 0:
            print(f"DDL Deployed: {summary['ddl_deployed']}")
            print(f"Scripts Generated: {summary['script_generated']}")
            print(f"Workflows Created: {summary['workflow_created']}")
            print(f"Fully Deployed: {summary['fully_deployed']}")
            print(f"Deployment Rate: {summary['deployment_percentage']:.1f}%")
        
        return 0


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Monday.com Board CLI - Dynamic Board Template System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy a new board
  python monday_board_cli.py deploy --board-id 12345 --board-name "Customer Orders" --table-name "MON_CustomerOrders"
  
  # List all boards
  python monday_board_cli.py list
  
  # Show board status
  python monday_board_cli.py status --board-id 12345
  
  # Update board configuration
  python monday_board_cli.py update --board-id 12345
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy a new Monday.com board')
    deploy_parser.add_argument('--board-id', type=int, required=True, help='Monday.com board ID')
    deploy_parser.add_argument('--board-name', type=str, help='Board name (will be discovered if not provided)')
    deploy_parser.add_argument('--table-name', type=str, help='SQL table name (will be generated if not provided)')
    deploy_parser.add_argument('--database', type=str, default='orders', help='Target database (default: orders)')
    deploy_parser.add_argument('--batch-size', type=int, default=100, help='Batch size for data insertion (default: 100)')
    deploy_parser.add_argument('--max-workers', type=int, default=8, help='Max concurrent workers (default: 8)')
    deploy_parser.add_argument('--force', action='store_true', help='Overwrite existing board configuration')
    deploy_parser.add_argument('--skip-ddl', action='store_true', help='Skip DDL execution')
    deploy_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all registered boards')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show status of a specific board')
    status_parser.add_argument('--board-id', type=int, required=True, help='Monday.com board ID')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update an existing board configuration')
    update_parser.add_argument('--board-id', type=int, required=True, help='Monday.com board ID')
    update_parser.add_argument('--force', action='store_true', help='Force update even if no changes detected')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a board from the registry')
    remove_parser.add_argument('--board-id', type=int, required=True, help='Monday.com board ID')
    remove_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show deployment summary')
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = MondayBoardCLI()
    
    # Route to appropriate command handler
    handlers = {
        'deploy': cli.deploy_board,
        'list': cli.list_boards,
        'status': cli.show_status,
        'update': cli.update_board,
        'remove': cli.remove_board,
        'summary': cli.show_summary
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
