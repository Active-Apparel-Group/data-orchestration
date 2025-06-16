import os
import logging
import yaml
import base64
from dotenv import load_dotenv
import pyodbc
import pandas as pd

def load_env():
    """Load .env file from repo root."""
    env_path = os.path.join(os.path.dirname(__file__), '../../.env')
    load_dotenv(dotenv_path=env_path)
    logging.info("Environment variables loaded from .env")

def get_db_config(db_key):
    """Get DB config from environment variables."""
    load_env()  # Ensure environment is loaded
    # Get password from either SECRET_xxx_PWD (base64) or DB_xxx_PASSWORD (plain)
    password = os.getenv(f'SECRET_{db_key.upper()}_PWD')
    if password:
        # Decode base64 password
        password = base64.b64decode(password).decode()
    else:
        # Fallback to plain password
        password = os.getenv(f'DB_{db_key.upper()}_PASSWORD')
    
    config = {
        'host': os.getenv(f'DB_{db_key.upper()}_HOST'),
        'port': int(os.getenv(f'DB_{db_key.upper()}_PORT', 1433)),
        'database': os.getenv(f'DB_{db_key.upper()}_DATABASE'),
        'username': os.getenv(f'DB_{db_key.upper()}_USERNAME'),
        'password': password,
        'encrypt': os.getenv(f'DB_{db_key.upper()}_ENCRYPT', 'yes'),
        'trustServerCertificate': os.getenv(f'DB_{db_key.upper()}_TRUSTSERVERCERTIFICATE', 'no'),
    }
    return config

def get_connection(db_key):
    """Create database connection using environment config."""
    load_env()  # Ensure environment is loaded
    config = get_db_config(db_key)
    
    # Use ODBC Driver 17 for SQL Server if available, fallback to SQL Server
    driver = "{ODBC Driver 17 for SQL Server}"
    try:
        # Test if ODBC Driver 17 is available
        test_conn_str = f"DRIVER={driver};SERVER=test;DATABASE=test;"
        pyodbc.connect(test_conn_str, timeout=1)
    except:
        # Fallback to older driver
        driver = "{SQL Server}"
    
    # Build connection string with proper SSL handling
    conn_str_parts = [
        f"DRIVER={driver}",
        f"SERVER={config['host']},{config['port']}",
        f"DATABASE={config['database']}",
        f"UID={config['username']}",
        f"PWD={config['password']}"
    ]
    
    # Handle SSL settings properly for older SQL Server drivers
    encrypt = config['encrypt'].lower()
    trust_cert = config['trustServerCertificate'].lower()
    
    if encrypt == 'yes':
        conn_str_parts.append("Encrypt=yes")
    elif encrypt == 'no':
        conn_str_parts.append("Encrypt=no")
    
    if trust_cert == 'yes':
        conn_str_parts.append("TrustServerCertificate=yes")
    elif trust_cert == 'no':
        conn_str_parts.append("TrustServerCertificate=no")
    
    # For older drivers, also try these alternative SSL settings
    if driver == "{SQL Server}":
        if encrypt == 'no':
            conn_str_parts.append("Integrated Security=no")
        # Remove problematic SSL settings for very old servers
        conn_str_parts = [part for part in conn_str_parts 
                         if not part.startswith(('Encrypt=', 'TrustServerCertificate='))]
    
    conn_str = ";".join(conn_str_parts) + ";"
    
    logging.info(f"Connecting to database: {db_key} ({config['host']}) with driver: {driver}")
    logging.debug(f"Connection string: {conn_str}")
    
    try:
        # Add connection timeout
        return pyodbc.connect(conn_str, timeout=30)
    except pyodbc.Error as e:
        # If modern settings fail, try with minimal connection string
        if "SSL Security error" in str(e) or "Invalid connection string attribute" in str(e):
            logging.warning(f"SSL connection failed for {db_key}, trying without SSL settings...")
            basic_conn_str = (
                f"DRIVER={{SQL Server}};SERVER={config['host']},{config['port']};"
                f"DATABASE={config['database']};UID={config['username']};PWD={config['password']};"
            )
            return pyodbc.connect(basic_conn_str, timeout=30)
        else:
            raise

def run_sql(filename, db_key, params=None):
    """Read and execute SQL from /sql directory, return DataFrame."""
    sql_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sql'))
    with open(os.path.join(sql_dir, filename), "r") as f:
        query = f.read()
    
    # Replace parameters in SQL if provided
    if params:
        for key, value in params.items():
            placeholder = f"{{{key}}}"  # e.g., {size_filter}
            query = query.replace(placeholder, str(value))
    
    with get_connection(db_key) as conn:
        return pd.read_sql(query, conn)

def load_customer_map():
    """Load and validate the customer alias YAML."""
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docs/mapping/customer_mapping.yaml'))
    with open(yaml_path, 'r') as f:
        mapping = yaml.safe_load(f)
    # Add duplicate check if needed
    alias_map = {}
    for entry in mapping['customers']:
        canonical = entry['canonical']
        if canonical.strip().upper() in alias_map:
            raise ValueError(f"Duplicate canonical: {canonical}")
        for alias in entry.get('aliases', []):
            alias_upper = alias.strip().upper()
            if alias_upper in alias_map:
                raise ValueError(f"Duplicate alias: {alias}")
            alias_map[alias_upper] = canonical
        alias_map[canonical.strip().upper()] = canonical
    logging.info("Customer mapping loaded and validated")
    return alias_map

def load_customer_mapping_full():
    """Load the complete customer mapping structure with matching configurations."""
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docs/mapping/customer_mapping.yaml'))
    with open(yaml_path, 'r') as f:
        mapping = yaml.safe_load(f)
    logging.info("Complete customer mapping loaded")
    return mapping

def get_customer_matching_config(canonical_customer):
    """Get customer-specific matching configuration (simplified for Phase 1)."""
    mapping = load_customer_mapping_full()
    
    # Default configuration for customers without specific matching rules
    default_config = {
        'style_match_strategy': 'standard',
        'style_field_name': 'Style',
        'exact_match_fields': ['Canonical_Customer', 'Customer_PO', 'Style', 'Color']
    }
    
    # Find customer entry
    customer_entry = None
    for entry in mapping['customers']:
        if entry['canonical'].strip().upper() == canonical_customer.strip().upper():
            customer_entry = entry
            break
    
    if customer_entry and 'matching_config' in customer_entry:
        # Extract only the simplified config fields we need for Phase 1
        config = default_config.copy()
        
        customer_config = customer_entry['matching_config']
        
        # Map from YAML to our simplified config
        if 'style_match_strategy' in customer_config:
            config['style_match_strategy'] = customer_config['style_match_strategy']
        
        if 'style_field_override' in customer_config:
            config['style_field_name'] = customer_config['style_field_override']
        
        if 'exact_match_fields' in customer_config:
            config['exact_match_fields'] = customer_config['exact_match_fields']
        
        logging.info(f"Using custom matching config for {canonical_customer}: strategy={config['style_match_strategy']}, field={config['style_field_name']}")
        return config
    else:
        logging.info(f"Using default matching config for {canonical_customer}")
        return default_config
