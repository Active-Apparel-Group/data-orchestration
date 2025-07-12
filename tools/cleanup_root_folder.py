#!/usr/bin/env python3
"""
Root Folder Cleanup Script
Purpose: Move misplaced files from root to proper project locations
Location: tools/cleanup_root_folder.py
"""
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import logger_helper

class RootFolderCleanup:
    """Clean up root folder violations per project structure rules"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.repo_root = repo_root
        self.moved_files = []
        self.violations_found = []
        
        # Create results directory if it doesn't exist
        self.results_dir = self.repo_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Create logs directory if it doesn't exist  
        self.logs_dir = self.repo_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
    def identify_violations(self):
        """Identify files that violate project structure rules"""
        
        # Files that SHOULD be in root (allowed)
        allowed_in_root = {
            '.env', '.env.example', '.env_encoded', '.gitignore', 
            'docker-compose.yml', 'dockerfile', 'Makefile', 
            'pytest.ini', 'README.md', 'requirements.txt', 
            'requirements.lock', 'setup.bat'
        }
        
        # Directories that SHOULD be in root (allowed)
        allowed_dirs = {
            '.git', '.github', '.vscode', '.backup',
            'dev', 'docs', 'jobs', 'queries', 'scripts', 'sql', 
            'tasks', 'templates', 'tests', 'tools', 'ui', 'utils', 'workflows'
        }
        
        violations = []
        
        for item in self.repo_root.iterdir():
            if item.is_file():
                if item.name not in allowed_in_root:
                    violations.append(item)
            elif item.is_dir():
                if item.name not in allowed_dirs:
                    violations.append(item)
        
        self.violations_found = violations
        return violations
    
    def categorize_violations(self):
        """Categorize violations by file type for proper placement"""
        categories = {
            'test_results': [],
            'analysis_results': [],
            'logs': [],
            'temp_files': [],
            'unknown': []
        }
        
        for violation in self.violations_found:
            filename = violation.name.lower()
            
            if 'test_results' in filename or filename.startswith('test_results_'):
                categories['test_results'].append(violation)
            elif any(keyword in filename for keyword in ['analysis_results', 'sql_query', 'sql_validation', 'targeted_sql']):
                categories['analysis_results'].append(violation)
            elif filename.endswith('.log') or 'log' in filename:
                categories['logs'].append(violation)
            elif filename.startswith('subitem_milestone_test'):
                categories['test_results'].append(violation)
            else:
                categories['unknown'].append(violation)
        
        return categories
    
    def cleanup_violations(self, dry_run=False):
        """Move violations to proper locations"""
        categories = self.categorize_violations()
        
        moves_planned = []
        
        # Test results files
        for file in categories['test_results']:
            target = self.results_dir / file.name
            moves_planned.append((file, target, "Test results"))
        
        # Analysis results files  
        for file in categories['analysis_results']:
            target = self.results_dir / file.name
            moves_planned.append((file, target, "Analysis results"))
        
        # Log files
        for file in categories['logs']:
            target = self.logs_dir / file.name
            moves_planned.append((file, target, "Log files"))
        
        # Unknown files (move to temp for manual review)
        temp_dir = self.repo_root / "temp_cleanup"
        if categories['unknown'] and not dry_run:
            temp_dir.mkdir(exist_ok=True)
        
        for file in categories['unknown']:
            target = temp_dir / file.name
            moves_planned.append((file, target, "Unknown (needs manual review)"))
        
        if dry_run:
            self.logger.info("DRY RUN - Files that would be moved:")
            for source, target, category in moves_planned:
                self.logger.info(f"  {category}: {source.name} -> {target}")
            return moves_planned
        
        # Execute moves
        for source, target, category in moves_planned:
            try:
                if target.exists():
                    # If target exists, add timestamp to avoid conflicts
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name_parts = target.name.split('.')
                    if len(name_parts) > 1:
                        new_name = f"{'.'.join(name_parts[:-1])}_{timestamp}.{name_parts[-1]}"
                    else:
                        new_name = f"{target.name}_{timestamp}"
                    target = target.parent / new_name
                
                shutil.move(str(source), str(target))
                self.moved_files.append((source.name, target, category))
                self.logger.info(f"Moved {category}: {source.name} -> {target}")
                
            except Exception as e:
                self.logger.error(f"Failed to move {source.name}: {e}")
        
        return self.moved_files
    
    def generate_cleanup_report(self):
        """Generate a cleanup report"""
        violations = self.identify_violations()
        categories = self.categorize_violations()
        
        report = []
        report.append("=" * 60)
        report.append("ROOT FOLDER CLEANUP REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("📋 VIOLATIONS FOUND")
        report.append("-" * 30)
        report.append(f"Total files violating structure rules: {len(violations)}")
        report.append("")
        
        for category, files in categories.items():
            if files:
                category_name = category.replace('_', ' ').title()
                report.append(f"{category_name}: {len(files)} files")
                for file in files[:5]:  # Show first 5
                    report.append(f"  • {file.name}")
                if len(files) > 5:
                    report.append(f"  • ... and {len(files) - 5} more")
                report.append("")
        
        if self.moved_files:
            report.append("✅ FILES MOVED")
            report.append("-" * 30)
            for original_name, target, category in self.moved_files:
                report.append(f"{category}: {original_name} -> {target.name}")
            report.append("")
        
        report.append("📁 RECOMMENDED FOLDER STRUCTURE")
        report.append("-" * 30)
        report.append("✅ ALLOWED IN ROOT:")
        report.append("  • Configuration: .env, docker-compose.yml, Makefile, etc.")
        report.append("  • Documentation: README.md")
        report.append("  • Dependencies: requirements.txt")
        report.append("")
        report.append("✅ PROPER LOCATIONS:")
        report.append("  • Test results: test_results/")
        report.append("  • Analysis files: test_results/")
        report.append("  • Log files: logs/")
        report.append("  • Python code: utils/, scripts/, tests/")
        report.append("  • SQL/configs: sql/")
        report.append("  • Documentation: docs/")
        
        return "\n".join(report)

def main():
    """Main execution function"""
    print("🧹 Root Folder Cleanup - Enforcing Project Structure Rules")
    print("=" * 60)
    
    cleanup = RootFolderCleanup()
    
    # First, show what violations exist
    violations = cleanup.identify_violations()
    print(f"Found {len(violations)} files violating project structure rules!")
    print()
    
    if violations:
        # Show dry run first
        print("📋 DRY RUN - Proposed file moves:")
        print("-" * 40)
        moves = cleanup.cleanup_violations(dry_run=True)
        print()
        
        # Ask for confirmation
        response = input("Proceed with cleanup? (y/N): ").lower().strip()
        
        if response == 'y':
            print("\n🧹 Executing cleanup...")
            moved = cleanup.cleanup_violations(dry_run=False)
            print(f"\n✅ Cleanup complete! Moved {len(moved)} files.")
        else:
            print("\n❌ Cleanup cancelled.")
    else:
        print("✅ Root folder is clean - no violations found!")
    
    # Generate report
    report = cleanup.generate_cleanup_report()
    print("\n" + report)
    
    # Save report
    report_file = cleanup.repo_root / "docs" / f"ROOT_CLEANUP_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Cleanup report saved to: {report_file}")

if __name__ == "__main__":
    main()
