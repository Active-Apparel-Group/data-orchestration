#!/usr/bin/env python3
"""
Codebase Configuration Audit Tool

This script scans the entire data orchestration codebase to identify:
1. Files with database connections
2. Files referencing YAML mapping files
3. Hardcoded configuration values that should use the master mapping system

Generates a comprehensive tracking table for migration planning and AI agent automation.

Usage:
    python scan_codebase_config.py

Output:
    - config_audit_report.md (markdown table)
    - config_audit_data.json (structured data for AI agents)
    - migration_priorities.md (recommended migration order)
"""

import os
import re
import json
import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class FileAuditResult:
    """Data structure for file audit results"""
    file_path: str
    relative_path: str
    folder: str
    file_type: str
    has_db_connection: bool
    has_yaml_mapping: bool
    db_connection_details: List[str]
    yaml_mapping_details: List[str]
    hardcoded_configs: List[str]
    migration_priority: str
    estimated_effort: str
    notes: str

class CodebaseConfigAuditor:
    """Main auditor class for scanning codebase configuration"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.results: List[FileAuditResult] = []
        
        # Define patterns for different types of configurations
        self.db_patterns = [
            # Database connection patterns
            r'pyodbc\.connect',
            r'sqlalchemy\.create_engine',
            r'pymssql\.connect',
            r'psycopg2\.connect',
            r'mysql\.connector',
            r'sqlite3\.connect',
            r'ENGINE\s*=',
            r'DATABASE\s*=',
            r'SERVER\s*=',
            r'DRIVER\s*=',
            r'connectionString',
            r'connection_string',
            r'db_helper',
            r'get_connection',
            r'execute_query',
            r'run_sql',
            r'load_sql_view',
            # Monday.com API patterns
            r'monday\.com/v2',
            r'api\.monday\.com',
            r'MONDAY_API_KEY',
            r'MONDAY_TOKEN',
        ]
        
        self.yaml_patterns = [
            # YAML file references
            r'\.yaml\b',
            r'\.yml\b',
            r'yaml\.safe_load',
            r'yaml\.load',
            r'yaml\.dump',
            r'load_mapping_config',
            r'load_customer_mapping',
            r'mapping_config',
            r'orders_unified_monday_mapping',
            r'field_mapping_matrix',
            r'customer_mapping',
            r'mapping_fields',
            r'monday_column_ids',
        ]
        
        self.hardcoded_config_patterns = [
            # Board IDs
            r'BOARD_ID\s*=\s*["\']?[0-9]+["\']?',
            r'board_id["\']?\s*:\s*["\']?[0-9]+["\']?',
            r'8709134353',
            r'9200517329',
            r'9218090006',
            # Table/view names
            r'MON_COO_Planning',
            r'MON_CustMasterSchedule',
            r'STG_MON_',
            r'ERR_MON_',
            r'v_mon_customer_ms',
            r'v_packed_products',
            r'v_orders_shipped',
            # Database names
            r'orders\.',
            r'distribution\.',
            r'warehouse\.',
            # Column IDs
            r'text_mkr\w+',
            r'dropdown_mkr\w+',
            r'numeric_mkr\w+',
            r'date_mkr\w+',
        ]
        
        # File patterns to scan
        self.include_patterns = [
            '*.py',
            '*.sql',
            '*.yml',
            '*.yaml',
            '*.json',
            '*.md',
            '*.txt',
            '*.ps1',
            '*.sh',
            '*.bat',
        ]
        
        # Directories to skip
        self.skip_dirs = {
            '__pycache__',
            '.git',
            '.vscode',
            'node_modules',
            '.backup',
            'venv',
            'env',
            '.pytest_cache',
        }

    def should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned"""
        # Skip directories in skip list
        if any(skip_dir in file_path.parts for skip_dir in self.skip_dirs):
            return False
        
        # Check if file matches include patterns
        return any(fnmatch.fnmatch(file_path.name, pattern) for pattern in self.include_patterns)

    def scan_file_content(self, file_path: Path) -> FileAuditResult:
        """Scan a single file for configuration patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return FileAuditResult(
                file_path=str(file_path),
                relative_path=str(file_path.relative_to(self.root_path)),
                folder=str(file_path.parent.relative_to(self.root_path)),
                file_type=file_path.suffix,
                has_db_connection=False,
                has_yaml_mapping=False,
                db_connection_details=[f"Error reading file: {e}"],
                yaml_mapping_details=[],
                hardcoded_configs=[],
                migration_priority="error",
                estimated_effort="unknown",
                notes=f"Could not read file: {e}"
            )
        
        # Check for database connections
        db_matches = []
        has_db_connection = False
        for pattern in self.db_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                has_db_connection = True
                db_matches.extend([f"{pattern}: {len(matches)} matches"])
        
        # Check for YAML mappings
        yaml_matches = []
        has_yaml_mapping = False
        for pattern in self.yaml_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                has_yaml_mapping = True
                yaml_matches.extend([f"{pattern}: {len(matches)} matches"])
        
        # Check for hardcoded configurations
        hardcoded_matches = []
        for pattern in self.hardcoded_config_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                hardcoded_matches.extend([f"{pattern}: {matches}"])
        
        # Determine migration priority
        priority = self.calculate_migration_priority(
            has_db_connection, has_yaml_mapping, len(hardcoded_matches), file_path
        )
        
        # Estimate effort
        effort = self.estimate_migration_effort(
            has_db_connection, has_yaml_mapping, len(hardcoded_matches), file_path
        )
        
        return FileAuditResult(
            file_path=str(file_path),
            relative_path=str(file_path.relative_to(self.root_path)),
            folder=str(file_path.parent.relative_to(self.root_path)),
            file_type=file_path.suffix,
            has_db_connection=has_db_connection,
            has_yaml_mapping=has_yaml_mapping,
            db_connection_details=db_matches,
            yaml_mapping_details=yaml_matches,
            hardcoded_configs=hardcoded_matches,
            migration_priority=priority,
            estimated_effort=effort,
            notes=""
        )

    def calculate_migration_priority(self, has_db: bool, has_yaml: bool, 
                                   hardcoded_count: int, file_path: Path) -> str:
        """Calculate migration priority based on file characteristics"""
        # Critical: Files that are actively used and have many hardcoded configs
        if 'scripts/' in str(file_path) and (has_db or has_yaml) and hardcoded_count > 3:
            return "Critical"
        
        # High: Production scripts with some hardcoded configs
        if 'scripts/' in str(file_path) and (has_db or has_yaml):
            return "High"
        
        # Medium: Development files or files with fewer hardcoded configs
        if has_db or has_yaml or hardcoded_count > 0:
            return "Medium"
        
        # Low: Files that don't need migration
        return "Low"

    def estimate_migration_effort(self, has_db: bool, has_yaml: bool, 
                                hardcoded_count: int, file_path: Path) -> str:
        """Estimate effort required for migration"""
        total_complexity = (
            (2 if has_db else 0) + 
            (1 if has_yaml else 0) + 
            (hardcoded_count * 0.5)
        )
        
        if total_complexity >= 5:
            return "Large (8+ hours)"
        elif total_complexity >= 3:
            return "Medium (4-8 hours)"
        elif total_complexity >= 1:
            return "Small (1-4 hours)"
        else:
            return "Minimal (<1 hour)"

    def scan_codebase(self) -> None:
        """Scan the entire codebase"""
        print(f"🔍 Scanning codebase from: {self.root_path}")
        
        files_scanned = 0
        for file_path in self.root_path.rglob('*'):
            if file_path.is_file() and self.should_scan_file(file_path):
                result = self.scan_file_content(file_path)
                self.results.append(result)
                files_scanned += 1
                
                if files_scanned % 50 == 0:
                    print(f"📄 Scanned {files_scanned} files...")
        
        print(f"✅ Completed scanning {files_scanned} files")

    def generate_markdown_report(self, output_path: str) -> None:
        """Generate markdown report with tracking table"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Codebase Configuration Audit Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary statistics
            total_files = len(self.results)
            db_files = sum(1 for r in self.results if r.has_db_connection)
            yaml_files = sum(1 for r in self.results if r.has_yaml_mapping)
            hardcoded_files = sum(1 for r in self.results if r.hardcoded_configs)
            
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Files Scanned:** {total_files}\n")
            f.write(f"- **Files with DB Connections:** {db_files}\n") 
            f.write(f"- **Files with YAML Mappings:** {yaml_files}\n")
            f.write(f"- **Files with Hardcoded Configs:** {hardcoded_files}\n\n")
            
            # Priority breakdown
            priorities = {}
            for result in self.results:
                priorities[result.migration_priority] = priorities.get(result.migration_priority, 0) + 1
            
            f.write("## Migration Priority Breakdown\n\n")
            for priority, count in sorted(priorities.items()):
                f.write(f"- **{priority}:** {count} files\n")
            f.write("\n")
            
            # Main tracking table
            f.write("## File Tracking Table\n\n")
            f.write("| File | Folder | DB Connection | YAML Mapping | Priority | Effort | Notes |\n")
            f.write("|------|--------|---------------|--------------|----------|--------|-------|\n")
            
            # Sort by priority (Critical, High, Medium, Low)
            priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "error": 4}
            sorted_results = sorted(
                self.results, 
                key=lambda x: (priority_order.get(x.migration_priority, 5), x.relative_path)
            )
            
            for result in sorted_results:
                if result.has_db_connection or result.has_yaml_mapping or result.hardcoded_configs:
                    # Create file link
                    file_link = f"[{result.relative_path}]({result.relative_path})"
                    
                    # Checkboxes
                    db_checkbox = "☑️" if result.has_db_connection else "☐"
                    yaml_checkbox = "☑️" if result.has_yaml_mapping else "☐"
                    
                    # Priority with emoji
                    priority_emoji = {
                        "Critical": "🔴",
                        "High": "🟠", 
                        "Medium": "🟡",
                        "Low": "🟢",
                        "error": "❌"
                    }
                    priority_display = f"{priority_emoji.get(result.migration_priority, '')} {result.migration_priority}"
                    
                    # Notes summary
                    notes = []
                    if result.hardcoded_configs:
                        notes.append(f"{len(result.hardcoded_configs)} hardcoded configs")
                    if result.db_connection_details:
                        notes.append(f"{len(result.db_connection_details)} DB patterns")
                    if result.yaml_mapping_details:
                        notes.append(f"{len(result.yaml_mapping_details)} YAML patterns")
                    notes_text = "; ".join(notes)
                    
                    f.write(f"| {file_link} | {result.folder} | {db_checkbox} | {yaml_checkbox} | {priority_display} | {result.estimated_effort} | {notes_text} |\n")
            
            f.write("\n")
            
            # Detailed findings section
            f.write("## Detailed Findings\n\n")
            
            critical_high_files = [r for r in sorted_results if r.migration_priority in ["Critical", "High"]]
            if critical_high_files:
                f.write("### Critical and High Priority Files\n\n")
                for result in critical_high_files:
                    f.write(f"#### {result.relative_path}\n")
                    f.write(f"- **Priority:** {result.migration_priority}\n")
                    f.write(f"- **Estimated Effort:** {result.estimated_effort}\n")
                    
                    if result.db_connection_details:
                        f.write("- **Database Connections:**\n")
                        for detail in result.db_connection_details[:5]:  # Limit to first 5
                            f.write(f"  - {detail}\n")
                    
                    if result.yaml_mapping_details:
                        f.write("- **YAML Mappings:**\n")
                        for detail in result.yaml_mapping_details[:5]:  # Limit to first 5
                            f.write(f"  - {detail}\n")
                    
                    if result.hardcoded_configs:
                        f.write("- **Hardcoded Configurations:**\n")
                        for detail in result.hardcoded_configs[:10]:  # Limit to first 10
                            f.write(f"  - {detail}\n")
                    
                    f.write("\n")

    def generate_json_data(self, output_path: str) -> None:
        """Generate JSON data for AI agents"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_files": len(self.results),
                "files_with_db": sum(1 for r in self.results if r.has_db_connection),
                "files_with_yaml": sum(1 for r in self.results if r.has_yaml_mapping),
                "files_with_hardcoded": sum(1 for r in self.results if r.hardcoded_configs),
            },
            "files": [asdict(result) for result in self.results if 
                     result.has_db_connection or result.has_yaml_mapping or result.hardcoded_configs]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def generate_migration_priorities(self, output_path: str) -> None:
        """Generate migration priorities document"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Migration Priorities and Recommendations\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Get critical and high priority files
            critical_files = [r for r in self.results if r.migration_priority == "Critical"]
            high_files = [r for r in self.results if r.migration_priority == "High"]
            
            f.write("## Recommended Migration Order\n\n")
            
            if critical_files:
                f.write("### Phase 1: Critical Priority (Immediate)\n\n")
                f.write("These files should be migrated immediately as they are actively used production scripts with many hardcoded configurations.\n\n")
                for i, result in enumerate(critical_files, 1):
                    f.write(f"{i}. **{result.relative_path}**\n")
                    f.write(f"   - Effort: {result.estimated_effort}\n")
                    f.write(f"   - Configs: {len(result.hardcoded_configs)} hardcoded items\n\n")
            
            if high_files:
                f.write("### Phase 2: High Priority (Next Sprint)\n\n")
                f.write("These files are production scripts that should be migrated in the next development cycle.\n\n")
                for i, result in enumerate(high_files, 1):
                    f.write(f"{i}. **{result.relative_path}**\n")
                    f.write(f"   - Effort: {result.estimated_effort}\n")
                    f.write(f"   - Configs: {len(result.hardcoded_configs)} hardcoded items\n\n")
            
            f.write("## AI Agent Automation Opportunities\n\n")
            f.write("The following tasks are well-suited for AI agent automation:\n\n")
            f.write("1. **Hardcoded Board ID Replacement**\n")
            f.write("   - Replace hardcoded board IDs with `mapping.get_board_config()` calls\n")
            f.write("   - Pattern: `BOARD_ID = \"123456\"` → `BOARD_ID = mapping.get_board_config('board_name')['board_id']`\n\n")
            
            f.write("2. **Table Name Standardization**\n")
            f.write("   - Replace hardcoded table names with mapping references\n")
            f.write("   - Pattern: `\"MON_CustMasterSchedule\"` → `mapping.get_board_config('customer_master_schedule')['table_name']`\n\n")
            
            f.write("3. **Type Conversion Updates**\n")
            f.write("   - Standardize type conversions using mapping helpers\n")
            f.write("   - Pattern: Manual type handling → `mapping.get_sql_type()` and `mapping.convert_field_value()`\n\n")
            
            f.write("4. **YAML File Consolidation**\n")
            f.write("   - Update references from individual YAML files to master mapping system\n")
            f.write("   - Pattern: `load_mapping_config('old_file.yaml')` → `mapping.get_board_config('board_name')`\n\n")

def main():
    """Main function"""
    print("🔍 Starting Codebase Configuration Audit")
    print("=" * 50)
    
    # Get the project root (two levels up from this script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    print(f"📁 Project root: {project_root}")
    
    # Initialize auditor
    auditor = CodebaseConfigAuditor(str(project_root))
    
    # Scan codebase
    auditor.scan_codebase()
    
    # Generate outputs
    output_dir = script_dir
    
    print("\n📊 Generating reports...")
    
    # Markdown report
    markdown_path = output_dir / "config_audit_report.md"
    auditor.generate_markdown_report(str(markdown_path))
    print(f"✅ Generated: {markdown_path}")
    
    # JSON data for AI agents
    json_path = output_dir / "config_audit_data.json"
    auditor.generate_json_data(str(json_path))
    print(f"✅ Generated: {json_path}")
    
    # Migration priorities
    priorities_path = output_dir / "migration_priorities.md"
    auditor.generate_migration_priorities(str(priorities_path))
    print(f"✅ Generated: {priorities_path}")
    
    print("\n🎯 Audit Complete!")
    print(f"📈 Scanned {len(auditor.results)} total files")
    
    # Summary stats
    db_files = sum(1 for r in auditor.results if r.has_db_connection)
    yaml_files = sum(1 for r in auditor.results if r.has_yaml_mapping)
    hardcoded_files = sum(1 for r in auditor.results if r.hardcoded_configs)
    
    print(f"🔗 Found {db_files} files with database connections")
    print(f"📄 Found {yaml_files} files with YAML mappings")
    print(f"⚙️ Found {hardcoded_files} files with hardcoded configurations")
    
    # Priority breakdown
    priorities = {}
    for result in auditor.results:
        if result.has_db_connection or result.has_yaml_mapping or result.hardcoded_configs:
            priorities[result.migration_priority] = priorities.get(result.migration_priority, 0) + 1
    
    print("\n📋 Migration priorities:")
    for priority, count in sorted(priorities.items()):
        emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "")
        print(f"   {emoji} {priority}: {count} files")

if __name__ == "__main__":
    main()
