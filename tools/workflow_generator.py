#!/usr/bin/env python3
"""
🏗️ KESTRA WORKFLOW GENERATOR v3.0 - DYNAMIC CONFIG SUPPORT
Automatically creates standardized Kestra workflow structure with:
- YAML workflow file with dynamic database connections
- Python script folder with main.py
- Documentation folder with plan
- README files
- Integration with config.yaml for database selection
"""

import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

class WorkflowGenerator:
    def __init__(self, base_path=None):
        """Initialize with base project path."""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.config_data = self.load_config()
        
    def load_config(self):
        """Load database configurations from config.yaml."""
        config_path = self.base_path / 'config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                print(f"✅ Loaded config from: {config_path}")
                return config_data
            except Exception as e:
                print(f"⚠️  Error loading config.yaml: {e}")
                return None
        else:
            print(f"⚠️  No config.yaml found at: {config_path}")
            return None
    
    def display_database_options(self):
        """Display available database connections from config.yaml."""
        if not self.config_data or 'databases' not in self.config_data:
            return []
        
        databases = self.config_data['databases']
        print("🗄️  Available Database Connections:")
        print("=" * 50)
        
        options = []
        for i, (key, config) in enumerate(databases.items(), 1):
            host = config.get('host', 'Unknown')
            database = config.get('database', 'Unknown')
            print(f"  {i:2d} - {key:15s} | {host:30s} | {database}")
            options.append((key, config))
        
        print("=" * 50)
        return options
    
    def prompt_database_selection(self):
        """Allow user to select multiple database connections."""
        if not self.config_data or 'databases' not in self.config_data:
            print("⚠️  No database configurations found. Using default single connection.")
            return []
        
        options = self.display_database_options()
        if not options:
            return []
        
        print()
        print("📋 Select database connections for this workflow:")
        print("   • Enter numbers separated by commas (e.g., 1,3,4)")
        print("   • Enter 'all' to use all connections")
        print("   • Enter 'none' for no database connections")
        
        while True:
            selection = input("🔢 Your selection: ").strip()
            
            if selection.lower() == 'none':
                return []
            elif selection.lower() == 'all':
                return options
            else:
                try:
                    indices = [int(x.strip()) for x in selection.split(',')]
                    selected = []
                    for idx in indices:
                        if 1 <= idx <= len(options):
                            selected.append(options[idx - 1])
                        else:
                            print(f"❌ Invalid option: {idx}. Please select from 1-{len(options)}")
                            break
                    else:
                        return selected
                except ValueError:
                    print("❌ Invalid format. Use numbers separated by commas (e.g., 1,3,4)")
        
    def prompt_workflow_details(self):
        """Interactive prompt for workflow details."""
        print("🏗️ === KESTRA WORKFLOW GENERATOR v3.0 ===")
        print(f"⏰ {self.timestamp}")
        print(f"📁 Base Path: {self.base_path}")
        print()
        
        # Get workflow name
        while True:
            workflow_name = input("🏷️  Enter workflow name (kebab-case, e.g., 'user-data-sync'): ").strip()
            if workflow_name and '-' in workflow_name and workflow_name.islower():
                break
            print("❌ Please use kebab-case format (lowercase with hyphens)")
        
        # Get description
        description = input("📝 Enter workflow description: ").strip()
        if not description:
            description = f"Workflow for {workflow_name}"
        
        # Get namespace
        namespace = input("🏷️  Enter namespace (default: company.team): ").strip()
        if not namespace:
            namespace = "company.team"
        
        # Database selection from config.yaml
        selected_databases = self.prompt_database_selection()
          # SQL queries
        uses_sql_files = False
        if selected_databases:
            uses_sql_files = input("📄 Does this workflow use SQL files? (y/n, default: n): ").strip().lower()
            uses_sql_files = uses_sql_files == 'y'
        
        return {
            'workflow_name': workflow_name,
            'script_name': workflow_name,  # Now the same as workflow_name
            'description': description,
            'namespace': namespace,
            'selected_databases': selected_databases,
            'uses_database': len(selected_databases) > 0,
            'uses_sql_files': uses_sql_files
        }
    
    def create_folder_structure(self, config):
        """Create the folder structure for the workflow."""
        folders = [
            self.base_path / 'workflows',
            self.base_path / 'scripts' / config['script_name'],
            self.base_path / 'docs' / 'workflows' / config['script_name'],
        ]
        
        if config['uses_sql_files']:
            folders.append(self.base_path / 'queries')
        
        created_folders = []
        for folder in folders:
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                created_folders.append(str(folder))
                print(f"📁 Created folder: {folder}")
            else:
                print(f"📁 Folder exists: {folder}")        
        return created_folders
    
    def generate_database_variables(self, selected_databases):
        """Generate environment variables section for selected databases with actual config values."""
        if not selected_databases:
            return "", ""
        
        # We don't need variables section anymore - putting actual values directly in env
        variables_section = ""
        env_vars_section = "        env:\n          # Database configuration - actual values from config.yaml"
        
        for db_key, db_config in selected_databases:
            # Use actual values from config.yaml, not template references
            host = db_config.get('host', 'localhost')
            port = str(db_config.get('port', '1433'))
            database = db_config.get('database', 'defaultdb')
            username = db_config.get('username', 'admin')
            password = db_config.get('password', 'password')
            encrypt = db_config.get('encrypt', 'yes')
            trust_cert = db_config.get('trustServerCertificate', 'yes')
            
            # Create environment variables with actual values from config
            env_vars_section += f"""
          # {db_key.upper()} Database
          DB_{db_key.upper()}_HOST: "{host}"
          DB_{db_key.upper()}_PORT: "{port}"
          DB_{db_key.upper()}_DATABASE: "{database}"
          DB_{db_key.upper()}_USERNAME: "{username}"
          DB_{db_key.upper()}_PASSWORD: "{password}"
          DB_{db_key.upper()}_ENCRYPT: "{encrypt}"
          DB_{db_key.upper()}_TRUSTSERVERCERTIFICATE: "{trust_cert}\""""
        
        return variables_section, env_vars_section
    
    def generate_workflow_yaml(self, config):
        """Generate the Kestra workflow YAML file with dynamic database connections using flow.id."""
        sql_include = ""
        config_include = ""
        
        # Include config.yaml if we have database connections
        if config['selected_databases']:
            config_include = """
        - config.yaml"""
        
        # Generate database variables and environment variables
        db_variables, db_env_vars = self.generate_database_variables(config['selected_databases'])
        
        # SQL include on separate line with proper indentation - now using flow.id
        if config['uses_sql_files']:
            sql_include = f"""
        - queries/{{{{flow.id}}}}_*.sql"""
        
        yaml_content = f"""id: {config['workflow_name']}
namespace: {config['namespace']}
description: "{config['description']}"

tasks:
  - id: setup_and_log
    type: io.kestra.plugin.core.log.Log
    message: |
      🚀 Starting Workflow: {{{{ flow.id }}}}
      📅 Timestamp: {{{{ now() }}}}
      🏷️  Namespace: {{{{ flow.namespace }}}}
      📝 Description: {config['description']}
      📁 Script Location: scripts/{{{{flow.id}}}}/
      🗄️  Database Connections: {len(config['selected_databases'])}
      
  - id: execute_main_workflow
    type: io.kestra.plugin.core.flow.WorkingDirectory
    description: "Execute {{{{flow.id}}}} main script with environment configuration"
    namespaceFiles:
      enabled: true
      include:
        - scripts/{{{{flow.id}}}}/**{config_include}{sql_include}
    tasks:
      - id: run_main_script
        type: io.kestra.plugin.scripts.python.Commands
        taskRunner:
          type: io.kestra.plugin.scripts.runner.docker.Docker
          pullPolicy: NEVER
        containerImage: my-custom-kestra:latest
        description: "Execute main workflow logic for {{{{flow.id}}}}"
        namespaceFiles:
          enabled: true
{db_env_vars}
        commands:
          - echo "🚀 === {config['description']} Starting ==="
          - echo "📄 Executing main script for {{{{flow.id}}}}..."
          - python scripts/{{{{flow.id}}}}/main.py
          - echo "✅ === {config['description']} Completed ==="
          
  - id: completion_log
    type: io.kestra.plugin.core.log.Log
    message: |
      ✅ Workflow completed successfully!
      🎯 Workflow: {{{{flow.id}}}}
      📊 Results: Check task outputs above for detailed execution results
      ⏰ Completed at: {{{{ now() }}}}
"""
        
        return yaml_content
    
    def generate_database_helper_functions(self, selected_databases):
        """Generate database connection helper functions for selected databases."""
        if not selected_databases:
            return "", ""
        
        # Since we're providing actual values in the workflow YAML, we don't need yaml module
        imports = """import pyodbc
from datetime import datetime"""
        
        functions = '''

def get_database_connection(db_name):
    """
    Create database connection using environment variables from Kestra workflow.
    
    Args:
        db_name (str): Database name (e.g., 'orders', 'dms', 'infor_132')
    """
    
    # Get connection details from environment variables (set by Kestra workflow)
    env_prefix = f"DB_{db_name.upper()}_"
    config = {
        'host': os.getenv(f'{env_prefix}HOST'),
        'port': os.getenv(f'{env_prefix}PORT', '1433'),
        'database': os.getenv(f'{env_prefix}DATABASE'),
        'username': os.getenv(f'{env_prefix}USERNAME'),
        'password': os.getenv(f'{env_prefix}PASSWORD'),
        'encrypt': os.getenv(f'{env_prefix}ENCRYPT', 'yes'),
        'trust_cert': os.getenv(f'{env_prefix}TRUSTSERVERCERTIFICATE', 'yes'),
    }
    
    # Validate required config
    required_fields = ['host', 'database', 'username', 'password']
    for field in required_fields:
        if not config[field]:
            raise ValueError(f"Missing required database config for {db_name}: {field}")
    
    print(f"🔗 Connecting to {db_name} database:")
    print(f"   📍 Host: {config['host']}:{config['port']}")
    print(f"   🗄️  Database: {config['database']}")
    print(f"   👤 Username: {config['username']}")
    print(f"   🔒 Encrypt: {config['encrypt']}")
    print(f"   ⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Build connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config['host']},{config['port']};"
        f"DATABASE={config['database']};"
        f"UID={config['username']};"
        f"PWD={config['password']};"
        f"Encrypt={config['encrypt']};"
        f"TrustServerCertificate={config['trust_cert']};"
    )
    
    try:
        print(f"🔄 Attempting {db_name} database connection...")
        connection = pyodbc.connect(conn_str, timeout=30)
        print(f"✅ {db_name} database connection successful!")
        return connection
    except pyodbc.Error as e:
        print(f"❌ Connection failed with ODBC Driver 17: {e}")
        print("🔄 Trying fallback to SQL Server driver...")
        # Fallback to older driver if needed
        conn_str = conn_str.replace("ODBC Driver 17 for SQL Server", "SQL Server")
        try:
            connection = pyodbc.connect(conn_str, timeout=30)
            print(f"✅ {db_name} database connection successful with fallback driver!")
            return connection
        except pyodbc.Error as e2:
            print(f"❌ Connection failed with both drivers: {e2}")
            raise'''
        
        return imports, functions
    
    def generate_main_script(self, config):
        """Generate the main Python script with dynamic database support."""
        if not config['selected_databases']:
            # No database version
            script_content = f'''import os
import sys
from datetime import datetime

def main():
    """
    Main workflow function for {config['workflow_name']}.
    
    Description: {config['description']}
    """
    
    print(f"🚀 === {config['description']} ===")
    print(f"⏰ Started at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print(f"📋 Workflow: {config['workflow_name']}")
    print(f"🏷️  Namespace: {config['namespace']}")
    print()
    
    try:
        # TODO: Add your workflow logic here
        print("🔧 Implementing workflow logic...")
        print("📊 Processing data...")
        
        print("⚠️  This is a template - implement your specific logic here!")
        
        print()
        print("✅ Workflow completed successfully!")
        print(f"⏰ Completed at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {{e}}")
        print(f"⏰ Failed at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        else:
            # Database version with dynamic connections
            db_imports, db_functions = self.generate_database_helper_functions(config['selected_databases'])
            
            # Generate database test calls
            db_test_calls = ""
            for db_key, _ in config['selected_databases']:
                db_test_calls += f"""
        # Test {db_key} database connection
        print("🧪 Testing {db_key} database connection...")
        conn = get_database_connection('{db_key}')
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE() as current_datetime")
        result = cursor.fetchone()
        print(f"✅ {db_key} database test successful! Current time: {{result[0]}}")
        cursor.close()
        conn.close()
"""
            
            # Generate database list for display
            db_list = ", ".join([db_key for db_key, _ in config['selected_databases']])
            
            script_content = f'''import os
import sys
{db_imports}

def main():
    """
    Main workflow function for {config['workflow_name']}.
    
    Description: {config['description']}
    Database Connections: {db_list}
    """
    
    print(f"🚀 === {config['description']} ===")
    print(f"⏰ Started at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print(f"📋 Workflow: {config['workflow_name']}")
    print(f"🏷️  Namespace: {config['namespace']}")
    print(f"🗄️  Database Connections: {db_list}")
    print()
    
    try:
        # Test database connections{db_test_calls}        
        # TODO: Add your workflow logic here
        print("🔧 Implementing workflow logic...")
        print("📊 Processing data...")
        
        print("⚠️  This is a template - implement your specific logic here!")
        
        print()
        print("✅ Workflow completed successfully!")
        print(f"⏰ Completed at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {{e}}")
        print(f"⏰ Failed at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
        sys.exit(1){db_functions}

if __name__ == "__main__":
    main()
'''
        
        return script_content
    
    def create_files(self, config):
        """Create all the workflow files."""
        files_created = []
        
        # Create workflow YAML
        yaml_path = self.base_path / 'workflows' / f"{config['workflow_name']}.yml"
        yaml_content = self.generate_workflow_yaml(config)
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        files_created.append(str(yaml_path))
        print(f"📄 Created workflow: {yaml_path}")
        
        # Create main Python script
        script_path = self.base_path / 'scripts' / config['script_name'] / 'main.py'
        script_content = self.generate_main_script(config)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        files_created.append(str(script_path))
        print(f"🐍 Created script: {script_path}")
        
        # Create script README
        readme_path = self.base_path / 'scripts' / config['script_name'] / 'README.md'
        db_info = ""
        if config['selected_databases']:
            db_names = [db_key for db_key, _ in config['selected_databases']]
            db_info = f"\\n\\n## 🗄️ Database Connections\\nThis workflow uses: {', '.join(db_names)}"
        
        readme_content = f"""# {config['workflow_name'].title().replace('-', ' ')} Script

## 📝 Overview
{config['description']}

**Workflow**: `{config['workflow_name']}`  
**Namespace**: `{config['namespace']}`  
**Script Folder**: `scripts/{config['script_name']}/`  
{db_info}

## 🔧 Configuration
{'Multi-database workflow with dynamic configuration from config.yaml' if config['selected_databases'] else 'No database connections required'}

## 🚀 Usage
The script is executed automatically by the Kestra workflow `{config['workflow_name']}.yml`.

## 🛠️ Development
1. Modify `main.py` to implement your specific logic
2. Test the script independently before deploying to Kestra
3. Use `get_database_connection('db_name')` for database access

---

**Generated by Kestra Workflow Generator v3.0 on {self.timestamp}**
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        files_created.append(str(readme_path))
        print(f"📚 Created README: {readme_path}")
          # Create sample SQL file if needed - now using flow.id naming convention
        if config['uses_sql_files']:
            sql_path = self.base_path / 'queries' / f"{config['workflow_name']}_sample.sql"
            sql_content = f"""-- Sample SQL query for {config['workflow_name']}
-- Created: {self.timestamp}

SELECT 
    GETDATE() as current_timestamp,
    '{config['workflow_name']}' as workflow_name,
    'Sample query - replace with your actual SQL' as note;
"""
            with open(sql_path, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            files_created.append(str(sql_path))
            print(f"📄 Created SQL sample: {sql_path}")
        
        return files_created
    
    def run(self):
        """Main execution function."""
        try:
            # Get workflow details from user
            config = self.prompt_workflow_details()
            
            print(f"\\n🔧 Creating workflow structure for '{config['workflow_name']}'...")
            
            # Display selected databases
            if config['selected_databases']:
                print("\\n🗄️  Selected Database Connections:")
                for db_key, db_config in config['selected_databases']:
                    print(f"   ✅ {db_key} - {db_config.get('host', 'Unknown')} / {db_config.get('database', 'Unknown')}")
            
            # Create folder structure
            self.create_folder_structure(config)
            
            # Create files
            files_created = self.create_files(config)
            
            # Summary
            print(f"\\n✅ === WORKFLOW GENERATION COMPLETE ===")
            print(f"🏷️  Workflow: {config['workflow_name']}")
            print(f"📝 Description: {config['description']}")
            print(f"🏷️  Namespace: {config['namespace']}")
            print(f"🗄️  Database Connections: {len(config['selected_databases'])}")
            print(f"📁 Script Folder: scripts/{config['script_name']}/")
            print(f"⏰ Created: {self.timestamp}")
            
            print(f"\\n📄 Files Created:")
            for file_path in files_created:
                print(f"   ✅ {file_path}")
            
            print(f"\\n🎯 Next Steps:")
            print(f"   1. Review and customize the generated files")
            print(f"   2. Update .env file with database connection variables")
            print(f"   3. Implement your workflow logic in scripts/{config['script_name']}/main.py")
            print(f"   4. Test the script independently before deploying to Kestra")
            
            if config['selected_databases']:
                print(f"\\n🗄️  Environment Variables Needed:")
                for db_key, _ in config['selected_databases']:
                    print(f"   DB_{db_key.upper()}_HOST, DB_{db_key.upper()}_DATABASE, etc.")
            
            print(f"\\n🚀 Ready to start developing your workflow!")
            
        except KeyboardInterrupt:
            print(f"\\n⚠️  Generation cancelled by user")
            sys.exit(0)
        except Exception as e:
            print(f"\\n❌ Error generating workflow: {e}")
            sys.exit(1)

def main():
    """Entry point for the workflow generator."""
    # Support command line argument for base path
    base_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    generator = WorkflowGenerator(base_path)
    generator.run()

if __name__ == "__main__":
    main()
