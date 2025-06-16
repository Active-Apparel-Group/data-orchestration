#!/usr/bin/env python3
"""
🏗️ KESTRA WORKFLOW GENERATOR v2.0
Automatically creates standardized Kestra workflow structure with:
- YAML workflow file
- Python script folder with main.py
- Documentation folder with plan
- README files

FIXES:
- Proper include path formatting for scripts in subfolders
- Correct YAML formatting for SQL file includes
- Dynamic path handling
"""

import os
import sys
from datetime import datetime
from pathlib import Path

class WorkflowGenerator:
    def __init__(self, base_path=None):
        """Initialize with base project path."""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    def prompt_workflow_details(self):
        """Interactive prompt for workflow details."""
        print("🏗️ === KESTRA WORKFLOW GENERATOR v2.0 ===")
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
        
        # Database usage
        uses_database = input("🗄️  Does this workflow use database? (y/n, default: y): ").strip().lower()
        uses_database = uses_database != 'n'
        
        # SQL queries
        uses_sql_files = False
        if uses_database:
            uses_sql_files = input("📄 Does this workflow use SQL files? (y/n, default: n): ").strip().lower()
            uses_sql_files = uses_sql_files == 'y'
        
        return {
            'workflow_name': workflow_name,
            'script_name': workflow_name.replace('-', '_'),
            'description': description,
            'namespace': namespace,
            'uses_database': uses_database,
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
    
    def generate_workflow_yaml(self, config):
        """Generate the Kestra workflow YAML file with corrected formatting."""
        db_variables = ""
        db_env_vars = ""
        sql_include = ""
        
        if config['uses_database']:
            db_variables = """
# Database Configuration Variables
variables:
  db_host: "{{ envs.db_orders_host }}"
  db_port: "{{ envs.db_orders_port }}"
  db_database: "{{ envs.db_orders_database }}"
  db_username: "{{ envs.db_orders_username }}"
  db_password: "{{ envs.db_orders_password }}"
  db_encrypt: "{{ envs.db_orders_encrypt }}"
  db_trust_cert: "{{ envs.db_orders_trustservercertificate }}"
"""
            
            db_env_vars = """        env:
          # Database environment variables passed to container
          DB_ORDERS_HOST: "{{ vars.db_host }}"
          DB_ORDERS_PORT: "{{ vars.db_port }}"
          DB_ORDERS_DATABASE: "{{ vars.db_database }}"
          DB_ORDERS_USERNAME: "{{ vars.db_username }}"
          DB_ORDERS_PASSWORD: "{{ vars.db_password }}"
          DB_ORDERS_ENCRYPT: "{{ vars.db_encrypt }}"
          DB_ORDERS_TRUSTSERVERCERTIFICATE: "{{ vars.db_trust_cert }}"
"""
        
        # Fixed: SQL include on separate line with proper indentation
        if config['uses_sql_files']:
            sql_include = f"""
        - queries/{config['script_name']}_*.sql"""
        
        yaml_content = f"""id: {config['workflow_name']}
namespace: {config['namespace']}
description: "{config['description']}"
{db_variables}
tasks:
  - id: setup_and_log
    type: io.kestra.plugin.core.log.Log
    message: |
      🚀 Starting Workflow: {{{{ flow.id }}}}
      📅 Timestamp: {{{{ now() }}}}
      🏷️  Namespace: {{{{ flow.namespace }}}}
      📝 Description: {config['description']}
      📁 Script Location: scripts/{config['script_name']}/
      
  - id: execute_main_workflow
    type: io.kestra.plugin.core.flow.WorkingDirectory
    description: "Execute {config['workflow_name']} main script with environment configuration"
    namespaceFiles:
      enabled: true
      include:
        - scripts/{config['script_name']}/**{sql_include}
    tasks:
      - id: run_main_script
        type: io.kestra.plugin.scripts.python.Commands
        taskRunner:
          type: io.kestra.plugin.scripts.runner.docker.Docker
          pullPolicy: NEVER
        containerImage: my-custom-kestra:latest
        description: "Execute main workflow logic for {config['workflow_name']}"
        namespaceFiles:
          enabled: true
{db_env_vars}        commands:
          - echo "🚀 === {config['description']} Starting ==="
          - echo "📄 Executing main script..."
          - python scripts/{config['script_name']}/main.py
          - echo "✅ === {config['description']} Completed ==="
          
  - id: completion_log
    type: io.kestra.plugin.core.log.Log
    message: |
      ✅ Workflow completed successfully!
      🎯 Workflow: {config['workflow_name']}
      📊 Results: Check task outputs above for detailed execution results
      ⏰ Completed at: {{{{ now() }}}}
"""
        
        return yaml_content
    
    def generate_main_script(self, config):
        """Generate the main Python script."""
        db_imports = ""
        db_function = ""
        db_connection_call = ""
        
        if config['uses_database']:
            db_imports = """import pyodbc
from datetime import datetime"""
            
            db_function = '''

def get_database_connection():
    """Create database connection using environment variables."""
    
    # Get database config from environment variables
    config = {
        'host': os.getenv('DB_ORDERS_HOST'),
        'port': os.getenv('DB_ORDERS_PORT', '1433'),
        'database': os.getenv('DB_ORDERS_DATABASE'),
        'username': os.getenv('DB_ORDERS_USERNAME'),
        'password': os.getenv('DB_ORDERS_PASSWORD'),
        'encrypt': os.getenv('DB_ORDERS_ENCRYPT', 'yes'),
        'trust_cert': os.getenv('DB_ORDERS_TRUSTSERVERCERTIFICATE', 'yes'),
    }

    # Validate required config
    required_fields = ['host', 'database', 'username', 'password']
    for field in required_fields:
        if not config[field]:
            raise ValueError(f"Missing required database config: {field} (set DB_ORDERS_{field.upper()} environment variable)")
    
    print(f"🔗 Connecting to database:")
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
        print("🔄 Attempting database connection...")
        connection = pyodbc.connect(conn_str, timeout=30)
        print("✅ Database connection successful!")
        return connection
    except pyodbc.Error as e:
        print(f"❌ Connection failed with ODBC Driver 17: {e}")
        print("🔄 Trying fallback to SQL Server driver...")
        # Fallback to older driver if needed
        conn_str = conn_str.replace("ODBC Driver 17 for SQL Server", "SQL Server")
        try:
            connection = pyodbc.connect(conn_str, timeout=30)
            print("✅ Database connection successful with fallback driver!")
            return connection
        except pyodbc.Error as e2:
            print(f"❌ Connection failed with both drivers: {e2}")
            raise'''
            
            db_connection_call = """
        # Test database connection
        print("🧪 Testing database connection...")
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE() as current_time")
        result = cursor.fetchone()
        print(f"✅ Database test successful! Current time: {result[0]}")
        cursor.close()
        conn.close()
"""
        
        script_content = f'''import os
import sys{db_imports}

def main():
    """
    Main workflow function for {config['workflow_name']}.
    
    Description: {config['description']}
    """
    
    print(f"🚀 === {config['description']} ===")
    print(f"⏰ Started at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in locals() else 'N/A'}}")
    print(f"📋 Workflow: {config['workflow_name']}")
    print(f"🏷️  Namespace: {config['namespace']}")
    print()
    
    try:
        # Main workflow logic starts here{db_connection_call}        
        # TODO: Add your workflow logic here
        print("🔧 Implementing workflow logic...")
        print("📊 Processing data...")
        
        # Placeholder for actual implementation
        print("⚠️  This is a template - implement your specific logic here!")
        
        print()
        print("✅ Workflow completed successfully!")
        print(f"⏰ Completed at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in locals() else 'N/A'}}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {{e}}")
        print(f"⏰ Failed at: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in locals() else 'N/A'}}")
        sys.exit(1){db_function}

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
        readme_content = f"""# {config['workflow_name'].title().replace('-', ' ')} Script

## 📝 Overview
{config['description']}

**Workflow**: `{config['workflow_name']}`  
**Namespace**: `{config['namespace']}`  
**Script Folder**: `scripts/{config['script_name']}/`  

## 🔧 Configuration
{'Database workflow - requires DB environment variables' if config['uses_database'] else 'No special configuration required'}

## 🚀 Usage
The script is executed automatically by the Kestra workflow `{config['workflow_name']}.yml`.

## 🛠️ Development
1. Modify `main.py` to implement your specific logic
2. Test the script independently before deploying to Kestra

---

**Generated by Kestra Workflow Generator v2.0 on {self.timestamp}**
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        files_created.append(str(readme_path))
        print(f"📚 Created README: {readme_path}")
        
        # Create sample SQL file if needed
        if config['uses_sql_files']:
            sql_path = self.base_path / 'queries' / f"{config['script_name']}_sample.sql"
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
            
            print(f"\n🔧 Creating workflow structure for '{config['workflow_name']}'...")
            
            # Create folder structure
            self.create_folder_structure(config)
            
            # Create files
            files_created = self.create_files(config)
            
            # Summary
            print(f"\n✅ === WORKFLOW GENERATION COMPLETE ===")
            print(f"🏷️  Workflow: {config['workflow_name']}")
            print(f"📝 Description: {config['description']}")
            print(f"🏷️  Namespace: {config['namespace']}")
            print(f"📁 Script Folder: scripts/{config['script_name']}/")
            print(f"⏰ Created: {self.timestamp}")
            
            print(f"\n📄 Files Created:")
            for file_path in files_created:
                print(f"   ✅ {file_path}")
            
            print(f"\n🎯 Next Steps:")
            print(f"   1. Review and customize the generated files")
            print(f"   2. Implement your workflow logic in scripts/{config['script_name']}/main.py")
            print(f"   3. Test the script independently before deploying to Kestra")
            
            print(f"\n🚀 Ready to start developing your workflow!")
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Generation cancelled by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error generating workflow: {e}")
            sys.exit(1)

def main():
    """Entry point for the workflow generator."""
    # Support command line argument for base path
    base_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    generator = WorkflowGenerator(base_path)
    generator.run()

if __name__ == "__main__":
    main()
